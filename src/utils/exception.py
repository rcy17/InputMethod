
class StrangePinyinError(Exception):

    def __init__(self, pinyin):
        super().__init__(pinyin)
