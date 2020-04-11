from sys import argv
from zipfile import ZipFile, ZIP_LZMA


def compress(files, output):
    target = ZipFile(output, 'w')
    for file in files:
        target.write(file, compress_type=ZIP_LZMA)
    target.close()


if __name__ == '__main__':
    compress(argv[2:], argv[1])
