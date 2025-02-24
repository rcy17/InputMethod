import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import settings


class NaiveBinaryModel:
    """
    Naive binary model with viterbi algorithm
    """
    def __init__(self, model_path='naive.sqlite3'):
        if not Path(model_path).exists():
            try:
                from sys import stderr
                from .build import train
                print('WARNING: no model file at', model_path, 'and try to build model')
                train('data', model_path)
            except Exception as e:
                Path(model_path).unlink()
                raise e
        self.smooth = settings.smooth
        self.candidates = settings.candidates
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
        sql = 'SELECT * FROM charset ORDER BY oid'
        data = self.connection.execute(sql).fetchall()
        self.chars = ('', ) + tuple(each[0] for each in data)
        self.char_to_count = (0, ) + tuple(each[1] for each in data)
        total_char_count = sum(self.char_to_count[:-2])
        self.char_to_likelihood = [count / total_char_count for count in self.char_to_count]

    def _load_pinyin(self):
        sql = 'SELECT oid, * FROM pinyin_set ORDER BY oid'
        data = self.connection.execute(sql).fetchall()
        self.pinyin_to_index = {each[1]: each[0] for each in data}
        for index in self.pinyin_to_index.values():
            sql = 'SELECT char from pinyin_char WHERE pinyin=%d' % index
            data = self.connection.execute(sql).fetchall()
            self.table[index] = sum(data, ())

    def _load_relation(self):
        for index in range(1, 1 + len(self.chars) + 1):
            sql = 'SELECT right, count FROM relation ' \
                  'WHERE left=%d AND count>0 ' \
                  'ORDER BY count DESC LIMIT %d' % (index, self.candidates)
            data = self.connection.execute(sql).fetchall()
            relation = dict(data)
            self.relation[index] = relation

    def initialize(self):
        print('Loading model...')
        now = datetime.now()
        self._load_charset()
        self._load_pinyin()
        self._load_relation()
        print('Finished load model, cost ', (datetime.now() - now).total_seconds(), 's')

    def _update_next_state(self, last_state, state):
        smooth = self.smooth
        for right in state:
            for left in last_state:
                if not self.char_to_count[left]:
                    continue
                p_last = last_state[left][0]
                p_related = self.relation[left].get(right, 0) / self.char_to_count[left]
                p_char = self.char_to_likelihood[right]
                state[right][left] = p_last * (smooth * p_related + (1 - smooth) * p_char)
            state[right][0] = max(state[right].values())
        return state

    def predict(self, pinyin: str):
        stop = len(self.chars) - 1  # for $
        start = stop - 1            # for ^
        states = [{start: {0: 1}}]
        for each in pinyin.split():
            index = self.pinyin_to_index.get(each.lower())
            if not index:
                raise StrangePinyinError(each)
            states.append(self._update_next_state(states[-1], {current: {} for current in self.table[index]}))
        end_state = self._update_next_state(states[-1], {stop: {}})[stop]
        end_state.pop(0)
        result = [max(end_state, key=lambda x: end_state[x])]
        for state in states[:0:-1]:
            result.append(max(filter(lambda x: x, state[result[-1]]), key=lambda x: state[result[-1]][x]))
        return ''.join(map(lambda x: self.chars[x], reversed(result[:-1])))
