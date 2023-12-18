import os
import sys

from src.rename_transformer import RenameTransformer
from src.riff_metadata_transformer import RiffMetadataTransformer

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <source path> <target path>")
        sys.exit(1)
    working_dir = os.getcwd()
    source_path = sys.argv[1]
    target_path = sys.argv[2]
    os.chdir(source_path)

    transformers = [
        RenameTransformer(target_path),
        RiffMetadataTransformer(),
    ]

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
