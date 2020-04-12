import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from sys import stderr

from utils.exception import *
from .build import train
import settings


class PinyinBinaryModel:
    """
    Naive binary model with viterbi algorithm
    """

    def __init__(self, model_path='pinyin.sqlite3', force_create=False):
        if not Path(model_path).exists() or force_create:
            try:
                from sys import stderr
                print('WARNING: no model file at', model_path, 'and try to build model')
                train('data', model_path)
            except Exception as e:
                Path(model_path).unlink()
                raise e
        self.smooth = settings.smooth
        self.candidates = settings.candidates
        self.occurrence_bound = settings.occurrence_bound
        self.connection = sqlite3.connect(model_path)
        self.char_pinyin = ()
        self.chars = ()
        self.char_to_count = {}
        self.char_to_likelihood = {}
        self.relation = {}
        self.table = defaultdict()
        self.pinyin_to_index = {}
        self.char_related_count = {}
        self.initialize()
        self.connection.close()

    def _load_charset(self):
        sql = 'SELECT * from char_set ORDER BY oid'
        data = self.connection.execute(sql).fetchall()
        self.chars = ('',) + tuple(each[1] for each in data)
        self.char_to_count = (0,) + tuple(each[2] for each in data)
        total_char_count = sum(self.char_to_count[:-2])
        self.char_to_likelihood = [count / total_char_count for count in self.char_to_count]
        for index, (pinyin, char, count) in enumerate(data):
            self.table.setdefault(pinyin, []).append(index + 1)

    def _load_relation(self):
        sql = 'SELECT left, group_concat(right), group_concat(count) FROM relation GROUP BY left'
        self.relation = {left: dict(zip(map(int, rights.split(',')), map(int, counts.split(',')))) for
                         left, rights, counts in self.connection.execute(sql)}

    def initialize(self):
        print('Loading model...', file=stderr)
        now = datetime.now()
        self._load_charset()
        self._load_relation()
        print('Finished load model, cost ', (datetime.now() - now).total_seconds(), 's', file=stderr)

    def _update_next_state(self, last_state, state):
        smooth = self.smooth
        for right in state:
            for left in last_state:
                p_last = last_state[left][0]
                p1 = self.char_to_likelihood[right]
                count_left_right = self.relation.get(left, {}).get(right, 0)
                p2 = count_left_right and count_left_right / self.char_to_count[left]
                state[right][left] = p_last * (smooth * p2 + (1 - smooth) * p1)
            state[right][0] = max(state[right].values())
        return state

    def predict(self, pinyin: str):
        stop = len(self.chars) - 1  # for $
        start = stop - 1  # for ^
        states = [{start: {0: 1}}]
        for each in pinyin.split():
            each = each.lower()
            candidates = self.table.get(each)
            if not candidates:
                raise StrangePinyinError(each)
            states.append(self._update_next_state(states[-1], {current: {} for current in candidates}))
        end_state = self._update_next_state(states[-1], {stop: {}})[stop]
        end_state.pop(0)
        result = [max(end_state, key=lambda x: end_state[x])]
        for state in states[:0:-1]:
            result.append(max(filter(lambda x: x, state[result[-1]]), key=lambda x: state[result[-1]][x]))
        return ''.join(map(lambda x: self.chars[x], reversed(result[:-1])))
