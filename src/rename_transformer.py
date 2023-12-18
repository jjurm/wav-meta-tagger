import os
import sys
import shutil
from typing import List

from .transformer import Transformer

INSTRUMENTS_MAP = {
    "808": "808s",
    "808s & Basses": "808s & Bass",
    "Basses": "Bass",
    "Full Loops": "Drum Loops",
    "Guitars": "Guitar Loops",
    "Hi-Hats": "Hihat Loops",
    "Hihat MIDI": "Hihat Loops/MIDI",
    "Melodies": "Melody Loops",
    "MIDI": "Melody Loops/MIDI",
    "Top Loops": "Percussion Loops",
}


class RenameTransformer(Transformer):
    """
    Renames files from:
    ./Type/Pack/Instrument/**/sample.wav
    to:
    ./Type/Instrument/**/sample.wav
    """
    def __init__(self, target_path: str):
        self.target_path = target_path

        self._types = set()
        self._instruments = set()
        self._renames = {}

    def prepare_transform(self, filenames: List[str]) -> List[str]:
        renames = {
            path: self._get_new_path(path)
            for path in filenames
        }

        # check duplicates
        target_paths = set()
        duplicates = []
        for s, t in renames.items():
            if t in target_paths:
                duplicates.append(t)
            target_paths.add(t)
        if duplicates:
            print("DUPLICATES:", file=sys.stderr)
            for t in sorted(duplicates):
                print(t, file=sys.stderr)
            sys.exit(1)

        print("Types: ", self._types)
        print("Instruments: ", sorted(map(str, self._instruments)))

        self._renames = renames
        return list(renames.values())

    def _get_new_path(self, path):
        type, instrument, rest = self._parse_path(path)
        components = [type] + ([instrument] if instrument else []) + rest
        new_path = os.path.normpath(os.path.join(".", *components))
        return new_path

    def _parse_path(self, path):
        parts = os.path.normpath(os.path.dirname(path)).split(os.sep)
        type = parts[0]
        instrument = parts[2] if len(parts) > 2 else None
        if instrument in INSTRUMENTS_MAP:
            instrument = INSTRUMENTS_MAP[instrument]
        self._types.add(type)
        self._instruments.add(instrument.split("/")[0] if instrument else None)
        rest = parts[3:] + [os.path.basename(path)]
        return type, instrument, rest

    def transform(self, filename: str) -> str:
        new_path = self._renames[filename]
        new_path_full = os.path.normpath(os.path.join(self.target_path, new_path))
        os.makedirs(os.path.dirname(new_path_full), exist_ok=True)
        shutil.copy2(filename, new_path_full)
        print("  > ", os.path.abspath(new_path_full))
        return new_path_full
