from json import loads

LAMBDA = 0.5


class Analyzer:
    def __init__(self, _lambda=LAMBDA):
        self.characters = ''
        self.character_index = {}
        self.character_count = {}
        self.pinyin_to_characters = {}
        self.pinyin_to_indexes = {}
        self.related_count = {}
        self.possibilities = {}
        self._lambda = _lambda

    def load_character(self, file_path, encoding='utf-8'):
        self.characters = open(file_path, encoding=encoding).read().strip()
        self.character_index = {character: index for index, character in enumerate(self.characters)}
        self.related_count = {index: {} for index in range(len(self.characters))}
        self.possibilities = {index: {} for index in range(len(self.characters))}
        self.character_count = {index: 0 for index in range(len(self.characters))}

    def load_pinyin(self, file_path, encoding='utf-8'):
        for line in open(file_path, encoding=encoding):
            tokens = line.split()
            self.pinyin_to_characters[tokens[0]] = tokens[1:]
            self.pinyin_to_indexes[tokens[0]] = [self.character_index[token] for token in tokens[1:] if
                                                 token in self.characters]

    def _analyze(self, data):
        last = None
        for each in data:
            index = self.character_index.get(each)
            if index is None:
                last = None
                continue
            elif last is not None:
                self.related_count[last].setdefault(index, 0)
                self.related_count[last][index] += 1
            self.character_count[index] += 1
            last = index

    def load_dataset(self, file_path, encoding='utf-8'):
        for line in open(file_path, encoding=encoding):
            data = loads(line)
            self._analyze(data['title'])
            self._analyze(data['html'])

    def build(self):
        for last, d in self.related_count.items():
            last_occur = self.character_count[last]
            for current, joint_occur in d.items():
                # current_occur = self.character_count[]
                self.possibilities[last][current] = joint_occur / last_occur
        from IPython import embed
        embed()

    def search(self, history, last, current_record, pinyin):
        if not pinyin:
            return current_record, [], max(current_record, history)
        record = 0
        sentence = []
        for index in self.pinyin_to_indexes[pinyin[0]]:
            new_record = current_record * self.possibilities[str(last)].get(str(index), 0)
            if new_record <= history:
                continue
            new_record, new_sentence, history = self.search(history, last, new_record, pinyin[1:])
            if new_record > record:
                record, sentence = new_record, [index] + new_sentence
        return record, sentence, history

    def predict(self, line: str):
        pinyin = line.split()
        record = 0
        sentence = []
        for index in self.pinyin_to_indexes[pinyin[0]]:
            new_record, new_sentence, history = self.search(record, index, 1, pinyin[1:])
            if new_record > record:
                record, sentence = new_record, [index] + new_sentence
        sentence = [self.characters[index] for index in sentence]
        return record, sentence
