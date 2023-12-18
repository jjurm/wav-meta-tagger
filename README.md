# Music Sample Tagger for FL Studio

This script reads music samples from one directory and writes them with added tags/metadata to a new folder structure.

* Tags WAV files with the correct metadata to be read by **FL Studio**

  The following values are extracted from file names:
    - **BPM**: Drag-and-dropping files with BPM value into FL Studio will automatically stretch them to fit the project tempo.
    - **Root Note**: Samples with Root Note or Key in their name will be tagged with the correct Root Note value. This is useful for sampler instruments, as they will automatically pitch the sample to the correct note.

* Organises your music samples into a new folder structure (by patter-matching on paths)

Usage:

```bash
python main.py [-h] SOURCE_DIR [--restructure TARGET_DIR] [--add-metadata]
```

Sample output:
```bash
python main.py Samples --restructure Samples_gen --add-metadata
```
```
---  /Samples/Loops/Cymatics - Oracle Sample Pack/Melodies/Cymatics - Oracle Nostalgic Melody Loop 1 - 97 BPM G# Maj.wav
  >  /Samples_gen/Loops/Melody Loops/Cymatics - Oracle Nostalgic Melody Loop 1 - 97 BPM G# Maj.wav
  + BPM: 97.0 + Tempo-sync
  + Key: G#
---  /Samples/Kits/Cymatics - Orchid Sample Pack/Drum One Shots/Cymatics - Orchid Kick - Clean (F).wav
  >  /Samples_gen/Kits/Drum One Shots/Cymatics - Orchid Kick - Clean (F).wav
  + Key: F
---  /Samples/Loops/Looperman/Drum Loops/Ambient/looperman-l-2247732-0267144-hbs-vintage-psychedelica-bonk-110bpm.wav
  >  /Samples_gen/Loops/Drum Loops/Ambient/looperman-l-2247732-0267144-hbs-vintage-psychedelica-bonk-110bpm.wav
  + BPM: 110.0 + Tempo-sync
```

Running `python main.py DIR --add-metadata` will add metadata to the original files in-place.

Metadata are stored using the RIFF format. More details in the `src/riff_metadata_transformer.py` file.

_This is a personal script that I decided to share in a public repository, it is not intended to be used as a library.
However, feel free to use it as an inspiration for your own projects, or contribute if you want to improve it._
