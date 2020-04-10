import sqlite3
from pathlib import Path
from collections import defaultdict

from utils.load import load_db_into_memory
from utils.exception import *
from naive.statistic import entry
from settings import smooth


class NaiveBinaryModel:
    """
    Naive binary model with viterbi algorithm
    """
    def __init__(self, model_path='db.sqlite3'):
        if not Path(model_path).exists():
            entry('data', model_path)
        self.connection = sqlite3.connect(model_path)
        self.chars = ()
        self.char_to_count = {}
        self.char_to_likelihood = {}
        self.relation = defaultdict(dict)
        self.table = {}
        self.pinyin_to_index = {}
        self.char_related_count = {}
        self.initialize()
        self.connection.close()

    def _load_charset(self):
        sql = 'SELECT oid, * FROM charset ORDER BY oid'
        data = self.connection.execute(sql).fetchall()
        self.chars = ('', ) + tuple(each[1] for each in data)
        self.char_to_count = {each[0]: each[2] for each in data}
        total_char_count = sum(self.char_to_count.values())
        self.char_to_likelihood = {k: v / total_char_count for k, v in self.char_to_count.items()}

    def _load_pinyin(self):
        sql = 'SELECT oid, * FROM pinyin_set ORDER BY oid'
        data = self.connection.execute(sql).fetchall()
        self.pinyin_to_index = {each[1]: each[0] for each in data}
        for index in self.pinyin_to_index.values():
            sql = 'SELECT char from pinyin_char WHERE pinyin=%d' % index
            data = self.connection.execute(sql).fetchall()
            self.table[index] = sum(data, ())

    def _load_relation(self):
        for index in self.char_to_likelihood:
            sql = 'SELECT right, count FROM relation WHERE left=%d' % index
            data = self.connection.execute(sql).fetchall()
            relation = dict(data)
            # total = sum(relation.values())
            # for each in relation:
            #    relation[each] /= total
            self.relation[index] = relation

    def initialize(self):
        print('Loading model...')
        self._load_charset()
        self._load_pinyin()
        self._load_relation()
        print('Finished load model')

    def _get_init_state(self, index):
        return {char: {0: self.char_to_likelihood[char]} for char in self.table[index]}

    def _get_next_state(self, last_state, index):
        state = {current: {} for current in self.table[index]}
        for right in state:
            for left in last_state:
                if not self.char_to_count[left]:
                    continue
                p_last = last_state[left][0]
                related = self.relation[left].get(right, 0)
                p_related = related / self.char_to_count[left]
                p_char = self.char_to_likelihood[right]
                state[right][left] = p_last * (smooth * p_related + (1 - smooth) * p_char)
        for current in state:
            state[current][0] = sum(state[current].values())
        return state

    def predict(self, pinyin: str):
        states = []
        for each in pinyin.split():
            index = self.pinyin_to_index.get(each)
            if not index:
                raise StrangePinyinError(each)
            states.append(self._get_next_state(states[-1], index) if states else self._get_init_state(index))

        result = []
        last = []
        for state in reversed(states):
            if last:
                result.append(max(filter(lambda x: x in last, state), key=lambda x: state[x][0])[0])
                last = state[result[-1]]
            else:
                result.append(max(state, key=lambda x: state[x][0]))
        return ''.join(map(lambda x: self.chars[x], reversed(result)))
