import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from IPython import embed

from utils.exception import *
from .build import train
import settings


class TrigramModel:
    """
    Naive binary model with viterbi algorithm
    """

    def __init__(self, model_path='trigram.sqlite3', force_create=False):
        if not Path(model_path).exists() or force_create:
            try:
                from sys import stderr
                print('INFO: try to build model', model_path)
                train('data', model_path)
                embed()
            except Exception as e:
                # Path(model_path).unlink()
                embed()
                raise e
        self.smooth_1 = settings.smooth_1
        self.smooth_2 = settings.smooth_2
        self.candidates = settings.candidates
        self.occurrence_bound = settings.occurrence_bound
        self.connection = sqlite3.connect(model_path)
        self.char_pinyin = ()
        self.chars = ()
        self.char_to_count = {}
        self.char_to_likelihood = {}
        self.relation_to_likelihood = {}
        self.relation2 = {}
        self.relation3 = {}
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
        sql = 'SELECT left, group_concat(right), group_concat(count) FROM relation2 GROUP BY left'
        self.relation2 = {left: dict(zip(map(int, rights.split(',')), map(int, counts.split(',')))) for
                          left, rights, counts in self.connection.execute(sql)}
        total_relation_count = sum(self.relation2.values())
        self.relation_to_likelihood = {key: count / total_relation_count for key, count in self.relation2.items()}

        sql = 'SELECT left, middle, group_concat(right), group_concat(count)' \
              ' FROM relation3 WHERE count>%d GROUP BY left, middle' % (self.occurrence_bound,)
        cursor = self.connection.execute(sql)
        self.relation3 = {(left, middle): dict(zip(map(int, rights.split(',')), map(int, counts.split(',')))) for
                          left, middle, rights, counts in cursor.fetchall()}

    def initialize(self):
        print('Loading model...')
        now = datetime.now()
        self._load_charset()
        self._load_relation()
        print('Finished load model, cost ', (datetime.now() - now).total_seconds(), 's')

    def _update_next_state(self, left_state, middle_state, state):
        smooth_1 = self.smooth_1
        smooth_2 = self.smooth_2
        for right in state:
            for mid in middle_state:
                for left in left_state:
                    p_last = middle_state[left][0]
                    p1 = self.char_to_likelihood[right]
                    p2 = self.relation2.get((mid, right), 0) / self.char_to_count.get(mid, 1)
                    count_left_mid = self.relation2.get((left, mid), 0)
                    p3 = count_left_mid and self.relation3[left, mid].get(right, 0) / count_left_mid
                    state[right][left] = p_last * (smooth_1 * p1 + smooth_2 * p2 + (1 - smooth_1 - smooth_2) * p3)
                state[right][0] = sum(state[right].values())
        return state

    def predict(self, pinyin: str):
        stop = len(self.chars) - 1  # for $
        start = stop - 1  # for ^
        states = [{start: {0: 1}}, {start: {0: 1, start: 1}}]
        for each in pinyin.split():
            each = each.lower()
            candidates = self.table.get(each)
            if not candidates:
                raise StrangePinyinError(each)
            states.append(self._update_next_state(states[-2], states[-1], {current: {} for current in candidates}))
        end_state = self._update_next_state(states[-1], {stop: {}})[stop]
        end_state.pop(0)
        result = [max(end_state, key=lambda x: end_state[x])]
        for state in states[:0:-1]:
            result.append(max(filter(lambda x: x, state[result[-1]]), key=lambda x: state[result[-1]][x]))
        return ''.join(map(lambda x: self.chars[x], reversed(result[:-1])))
