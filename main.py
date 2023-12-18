import argparse
import os

from src.rename_transformer import RenameTransformer
from src.riff_metadata_transformer import RiffMetadataTransformer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", metavar="SOURCE_DIR", type=str)
    parser.add_argument('--restructure', metavar='TARGET_DIR', type=str,
                        help='Copy files to a new folder structure inside the target directory')
    parser.add_argument('--add-metadata', action='store_true',
                        help='Add BPM and Root Note metadata to WAV files (in-place)')
    args = parser.parse_args()

    working_dir = os.getcwd()
    source_path = args.source
    os.chdir(source_path)

    transformers = []
    if args.restructure:
        transformers.append(RenameTransformer(args.restructure))
    if args.add_metadata:
        transformers.append(RiffMetadataTransformer())

    # Collect filenames
    source_filenames = []
    for root, dirs, files in os.walk("."):
        for filename in files:
            if filename.startswith("."):
                continue  # hidden file
            source_filenames.append(os.path.join(root, filename))

    # Prepare
    filenames = source_filenames
    for transformer in transformers:
        filenames = transformer.prepare_transform(filenames)

    # Transform
    for filename in source_filenames:
        print("--- ", os.path.abspath(filename))
        for transformer in transformers:
            filename = transformer.transform(filename)

    print("DONE")
