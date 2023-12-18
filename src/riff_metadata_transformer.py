import os
import re
from struct import pack, unpack
from typing import BinaryIO, List, Optional

from wave_chunk_parser.exceptions import InvalidHeaderException
from wave_chunk_parser.utils import word_align, seek_and_read
from wave_chunk_parser.chunks import RiffChunk, Chunk, FormatChunk, DataChunk, GenericChunk

from .transformer import Transformer

NOTE_OFFSET_MAP = {n.lower(): o for n, o in {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}.items()}


def get_note_offset(note: str) -> int:
    return NOTE_OFFSET_MAP[note.lower()]


class AcidChunk(Chunk):
    """
    From https://forums.cockos.com/showthread.php?t=227118

    ** The acid chunk goes a little something like this:
    **
    ** 4 bytes          'acid'
    ** 4 bytes (int)     length of chunk starting at next byte
    **
    ** 4 bytes (int)     type of file:
    **        this appears to be a bit mask,however some combinations
    **        are probably impossible and/or qualified as "errors"
    **
    **        0x01 On: One Shot         Off: Loop
    **        0x02 On: Root note is Set Off: No root
    **        0x04 On: Stretch is On,   Off: Strech is OFF
    **        0x08 On: Disk Based       Off: Ram based
    **        0x10 On: ??????????       Off: ????????? (Acidizer puts that ON)
    **
    ** 2 bytes (short)      root note
    **        if type 0x10 is OFF : [C,C#,(...),B] -> [0x30 to 0x3B]
    **        if type 0x10 is ON  : [C,C#,(...),B] -> [0x3C to 0x47]
    **         (both types fit on same MIDI pitch albeit different octaves, so who cares)
    **
    ** 2 bytes (short)      ??? always set to 0x8000
    ** 4 bytes (float)      ??? seems to be always 0
    ** 4 bytes (int)        number of beats
    ** 2 bytes (short)      meter denominator   //always 4 in SF/ACID
    ** 2 bytes (short)      meter numerator     //always 4 in SF/ACID
    **                      //are we sure about the order?? usually its num/denom
    ** 4 bytes (float)      tempo
    """

    file_type: int
    root_note: int
    n_beats: int
    tempo: float

    HEADER_FORMAT = b"acid"
    LENGTH_CHUNK = 32

    def __init__(self, file_type: int, root_note: int, n_beats: int, tempo: float):
        self.file_type = file_type
        self.root_note = root_note
        self.n_beats = n_beats
        self.tempo = tempo

    @property
    def get_name(self) -> str:
        return str(self.HEADER_FORMAT)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'AcidChunk':
        (
            file_type,
            root_note,
            _,
            _,
            n_beats,
            _,
            _,
            tempo,
        ) = unpack(
            "<IHHfIHHf",
            data,
        )

        return cls(file_type, root_note, n_beats, tempo)

    @classmethod
    def from_generic_chunk(cls, chunk: Chunk) -> 'AcidChunk':
        # noinspection PyTypeChecker
        generic_chunk: GenericChunk = chunk
        return cls.from_bytes(generic_chunk.datas.tobytes())

    @classmethod
    def from_file(cls, file_handle: BinaryIO, offset: int) -> 'AcidChunk':
        (header_str, length) = cls.read_header(file_handle, offset)

        if not header_str == cls.HEADER_FORMAT:
            raise InvalidHeaderException("Format chunk must start with acid")

        return cls.from_bytes(
            seek_and_read(
                file_handle,
                offset + cls.OFFSET_CHUNK_CONTENT,
                cls.LENGTH_CHUNK - cls.OFFSET_CHUNK_CONTENT,
            )
        )

    @word_align
    def to_bytes(self) -> bytes:
        format = pack(
            "<4sIIHHfIHHf",
            self.HEADER_FORMAT,
            24,  # length
            self.file_type,
            self.root_note,
            0x8000,
            0.0,
            self.n_beats,
            4,
            4,
            self.tempo,
        )
        return format


class InstrumentChunk(Chunk):
    """
    From https://web.archive.org/web/20130822004502/http://www.sonicspot.com/guide/wavefiles.html#wavefilechunks

    | Offset | Size | Description        | Value               |
    |--------|------|--------------------|---------------------|
    | 0x00   | 4    | Chunk ID           | "inst" (0x696E7374) |
    | 0x04   | 4    | Chunk Data Size    | 7                   |
    | 0x08   | 1    | Unshifted Note     | 0 - 127             |
    | 0x09   | 1    | Fine Tune (dB)     | -50 - +50           |
    | 0x0A   | 1    | Gain               | -64 - +64           |
    | 0x0B   | 1    | Low Note           | 0 - 127             |
    | 0x0C   | 1    | High Note          | 0 - 127             |
    | 0x0D   | 1    | Low Velocity       | 1 - 127             |
    | 0x0E   | 1    | High Velocity      | 1 - 127             |
    """

    HEADER_FORMAT = b"inst"
    LENGTH_CHUNK = 7
    UNSHIFTED_NOTE_C5 = 0x3c

    def __init__(
            self,
            unshifted_note: int = UNSHIFTED_NOTE_C5,
            fine_tune: int = 0x00,
            gain: int = 0x00,
            low_note: int = 0x00,
            high_note: int = 0x7f,
            low_velocity: int = 0x00,
            high_velocity: int = 0x7f,
    ):
        self.unshifted_note = unshifted_note
        self.fine_tune = fine_tune
        self.gain = gain
        self.low_note = low_note
        self.high_note = high_note
        self.low_velocity = low_velocity
        self.high_velocity = high_velocity

    @property
    def get_name(self) -> str:
        return str(self.HEADER_FORMAT)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'InstrumentChunk':
        (
            unshifted_note,
            fine_tune,
            gain,
            low_note,
            high_note,
            low_velocity,
            high_velocity,
        ) = unpack(
            "<BBBBBBB",
            data,
        )

        return cls(unshifted_note, fine_tune, gain, low_note, high_note, low_velocity, high_velocity)

    @classmethod
    def from_generic_chunk(cls, chunk: Chunk) -> 'InstrumentChunk':
        # noinspection PyTypeChecker
        generic_chunk: GenericChunk = chunk
        return cls.from_bytes(generic_chunk.datas.tobytes())

    @classmethod
    def from_file(cls, file_handle: BinaryIO, offset: int) -> 'InstrumentChunk':
        (header_str, length) = cls.read_header(file_handle, offset)

        if not header_str == cls.HEADER_FORMAT:
            raise InvalidHeaderException("Format chunk must start with inst")

        return cls.from_bytes(
            seek_and_read(
                file_handle,
                offset + cls.OFFSET_CHUNK_CONTENT,
                cls.LENGTH_CHUNK - cls.OFFSET_CHUNK_CONTENT,
            )
        )

    @word_align
    def to_bytes(self) -> bytes:
        format = pack(
            "<4sIBBBBBBB",
            self.HEADER_FORMAT,
            7,  # length
            self.unshifted_note,
            self.fine_tune,
            self.gain,
            self.low_note,
            self.high_note,
            self.low_velocity,
            self.high_velocity,
        )
        return format


class RiffChunkEditor:
    riff_chunk: RiffChunk
    acid_chunk: Optional[tuple[AcidChunk, bool]]
    inst_chunk: Optional[tuple[InstrumentChunk, bool]]

    def __init__(self, filename: str):
        self.filename = filename
        self.acid_chunk = None
        self.inst_chunk = None

    def __enter__(self):
        self.fd = open(self.filename, "r+b")
        # noinspection PyTypeChecker
        self.riff_chunk = RiffChunk.from_file(self.fd)
        return self

    def get_acid_chunk(self) -> tuple[AcidChunk, bool]:
        """
        :return: (AcidChunk, True if it was already present in the file)
        """
        if not self.acid_chunk:
            chunk = self.riff_chunk.get_chunk("acid")
            acid_chunk: AcidChunk
            if chunk:
                acid_chunk = AcidChunk.from_generic_chunk(chunk)
            else:
                acid_chunk = AcidChunk(
                    file_type=0x01,
                    root_note=0x3C,
                    n_beats=0,
                    tempo=0,
                )
            self.acid_chunk = (acid_chunk, bool(chunk))
        return self.acid_chunk

    def get_inst_chunk(self) -> tuple[InstrumentChunk, bool]:
        """
        :return: (InstrumentChunk, True if it was already present in the file)
        """
        if not self.inst_chunk:
            chunk = self.riff_chunk.get_chunk("inst")
            inst_chunk: InstrumentChunk
            if chunk:
                inst_chunk = InstrumentChunk.from_generic_chunk(chunk)
            else:
                inst_chunk = InstrumentChunk()
            self.inst_chunk = (inst_chunk, bool(chunk))
        return self.inst_chunk

    def calculate_n_beats(self, bpm):
        # noinspection PyTypeChecker
        format_chunk: FormatChunk = self.riff_chunk.get_chunk("fmt ")
        # noinspection PyTypeChecker
        data_chunk: DataChunk = self.riff_chunk.get_chunk("data")

        duration_s = data_chunk.samples.shape[0] / format_chunk.sample_rate
        n_beats = round(bpm / 60.0 * duration_s)
        return n_beats

    def __exit__(self, exc_type, exc_value, traceback):
        # noinspection PyTypeChecker
        original_chunks: List[Chunk] = self.riff_chunk.sub_chunks
        to_replace = ([self.acid_chunk[0]] if self.acid_chunk else []) \
                     + ([self.inst_chunk[0]] if self.inst_chunk else [])
        chunks = []
        for chunk in original_chunks:
            for candidate in to_replace:
                if candidate.get_name == chunk.get_name:
                    to_replace.remove(candidate)
                    chunks.append(candidate)
                    break
            else:
                chunks.append(chunk)
        chunks.extend(to_replace)

        new_riff_chunk = RiffChunk(chunks)
        # noinspection PyTypeChecker
        wav_bytes: bytes = new_riff_chunk.to_bytes()
        self.fd.seek(0)
        self.fd.write(wav_bytes)
        self.fd.close()


class RiffMetadataTransformer(Transformer):
    """
    Adds Tempo and Key metadata to WAV files to be read by FL Studio.
    """

    def prepare_transform(self, filenames: List[str]) -> List[str]:
        return filenames

    def transform(self, filename: str) -> str:
        basename = os.path.basename(filename)
        basename_root, basename_ext = os.path.splitext(basename)
        if basename_ext == ".wav":
            bpm = self._get_bpm(basename_root)
            root_note = self._get_root_note(basename_root)
            if not bpm and not root_note:
                return filename

            with RiffChunkEditor(filename) as editor:
                if bpm:
                    n_beats = editor.calculate_n_beats(bpm)
                    acid_chunk, acid_chunk_existed = editor.get_acid_chunk()

                    acid_chunk.file_type = acid_chunk.file_type & ~0x01 | 0x04  # Loop, Stretch On
                    acid_chunk.n_beats = n_beats
                    acid_chunk.tempo = bpm
                    print(f"  {'!' if acid_chunk_existed else '+'} BPM: {bpm} + Tempo-sync")

                if root_note:
                    inst_chunk, inst_chunk_existed = editor.get_inst_chunk()
                    inst_chunk.unshifted_note = InstrumentChunk.UNSHIFTED_NOTE_C5 + get_note_offset(root_note)
                    print(f"  {'!' if inst_chunk_existed else '+'} Root: {root_note}")

        return filename

    @staticmethod
    def _get_bpm(basename_root):
        """
        Parses filenames such as "sample - 120 BPM C# Maj.wav"
        """
        match = re.search(r"[\s-]((\d+\.)?\d+)\s?bpm", basename_root, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def _get_root_note(basename_root):
        match = re.search((
            r"([\s-](?P<key1>[A-G][#b]?)((\s(Maj|Min))|([^A-Za-z0-9#][^#-]*)|$))"  # "sample - 120 BPM C# Maj.wav" or "sample - 120 BPM C#.wav"
            r"|"
            r"([\s-]\((?P<key2>[A-G][#b]?)\))"  # "Sample (D#).wav"
        ), basename_root, re.IGNORECASE)
        if match:
            return match.group("key1") or match.group("key2")
        return None
