"""
这是拼音输入法的入口文件，应助教要求专程放在bin目录下
但我不得不指出这种文件结构对Python项目是非常不适合的
也不知道助教会不会看，如果看到的话希望明年能重新要求
比如说下面我要先调整一下工作路径，否则会出现路径问题
并且我甚至要考虑助教是在bin目录下运行的还是根目录下
"""
import sys
import os
try:
    from tqdm import tqdm
except ImportError:
    # 谨防助教没有 tqdm
    def tqdm(iteratable):
        length = iteratable.__len__()
        for current, each in enumerate(iteratable):
            print('Finished %d / %d' % (current, length), end='', file=sys.stderr)
            yield each
        print('Finished %d / %d' % (length, length))

os.chdir('../src')
sys.path.append('.')
import models
from utils.exception import StrangePinyinError


def usage():
    print("Usage: python pinyin.py <path/to/input_file> <path/to/output_file>")


def main(input_file, output_file=sys.stdout):
    model = models.TrigramModel()
    file_out = open(output_file, 'w')
    lines = [line.strip() for line in open(input_file) if line.strip()]
    for line in tqdm(lines):
        try:
            print(model.predict(line), file=file_out)
        except StrangePinyinError as e:
            print('遇到了无法处理的拼音', e.args[0])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
    else:
        main(sys.argv[1], sys.argv[2])
