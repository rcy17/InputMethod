from pathlib import Path

from naive.models import NaiveBinaryModel
from utils import exception


def main():
    model = NaiveBinaryModel('db.sqlite3')
    for line in open('input/input.txt'):
        if not line.strip():
            continue
        try:
            print(model.predict(line))
        except exception.StrangePinyinError as e:
            print('遇到了超出数据库的拼音', e.args[0])


if __name__ == '__main__':
    main()
