from models import PinyinBinaryModel, NaiveBinaryModel, TrigramModel
from utils import exception


def main():
    model = PinyinBinaryModel(force_create=False)
    result = None
    correct = 0
    char_count = 0
    for line in open('input/input.txt'):
        line = line.strip()
        if not line:
            continue
        try:
            # print(line, end='')
            result = model.predict(line)
            print(result)
        except exception.StrangePinyinError as e:
            # print('遇到了超出数据库的拼音', e.args[0])
            char_count += len(line)
            for a, b in zip(result, line):
                correct += a == b
    if char_count:
        print(correct, char_count, correct / char_count)


if __name__ == '__main__':
    main()
