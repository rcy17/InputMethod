from pathlib import Path

from naive.models import NaiveBinaryModel
from utils import exception


def main():
    model = NaiveBinaryModel('db.sqlite3')
    for line in open('input/wlxt.txt'):
        if not line.strip():
            continue
        try:
            print(line, end='')
            print(model.predict(line))
        except exception.StrangePinyinError as e:
            # print('遇到了超出数据库的拼音', e.args[0])
            pass


if __name__ == '__main__':
    main()
