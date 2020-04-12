from sys import argv
from zipfile import ZipFile


def uncompress(target, output):
    target = ZipFile(target)
    target.extractall(output)
    target.close()


if __name__ == '__main__':
    uncompress(argv[1], argv[2])
