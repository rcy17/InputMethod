from naive.analyze import Analyzer
from json import load


def train():
    analyzer = Analyzer()
    analyzer.load_character('data/一二级汉字表.txt', 'gb2312')
    analyzer.load_pinyin('data/拼音汉字表.txt', 'gb2312')
    '''for i in range(1, 13):
        file = 'data/2016-0%d.txt' % i
        print('Processing file', file)
        try:
            analyzer.load_dataset(file, 'gbk')
        except FileNotFoundError:
            pass
    analyzer.build()'''
    analyzer.possibilities = load(open('data/model.json'))
    return analyzer
