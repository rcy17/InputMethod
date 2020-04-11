import models
from utils import exception
try:
    from tqdm import tqdm
    raise ImportError
except ImportError:
    tqdm = lambda x: x


def main():
    model = models.TrigramModel(force_create=False)
    result = None
    char_correct = 0
    char_count = 0
    line_correct = 0
    line_count = 0
    for line in tqdm(open('input/input.txt')):
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
            line_count += 1
            line_correct += result == line
            for a, b in zip(result, line):
                char_correct += a == b
        except KeyboardInterrupt:
            break
    if char_count:
        print(char_correct, char_count, char_correct / char_count)
    if line_count:
        print(line_correct, line_count, line_correct / line_count)


if __name__ == '__main__':
    main()
