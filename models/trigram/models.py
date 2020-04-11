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
                print(datetime.now(), 'Meet error', type(e), e)
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
        self.relation2 = {(left, right): count for left, rights, counts in self.connection.execute(sql) for
                          right, count in zip(map(int, rights.split(',')), map(int, counts.split(',')))}

        # total_relation_count = sum(self.relation2.values())
        # self.relation_to_likelihood = {key: count / total_relation_count for key, count in self.relation2.items()}

        sql = 'SELECT left, middle, group_concat(right), group_concat(count)' \
              ' FROM relation3 WHERE count>%d GROUP BY left, middle' % (self.occurrence_bound,)
        self.relation3 = {(left, mid): dict(zip(map(int, rights.split(',')), map(int, counts.split(','))))
                          for left, mid, rights, counts in self.connection.execute(sql)}

    def initialize(self):
        print('Loading model...')
        now = datetime.now()
        self._load_charset()
        self._load_relation()
        print('Finished load model, cost ', (datetime.now() - now).total_seconds(), 's')

    def _get_next_state(self, last_state, candidates):
        smooth_1 = self.smooth_1
        smooth_2 = self.smooth_2
        state = defaultdict(dict)
        for right in candidates:
            for mid, left in last_state:
                if (left, mid, right) in [
                    (5236, 2232, 7498),
                    (5239, 2289, 5880)
                ]:
                    left = left
                p_last = last_state[mid, left][0]
                p1 = self.char_to_likelihood[right]
                p2 = self.relation2.get((mid, right), 0) / (self.char_to_count[mid] or 1)
                count_left_mid = self.relation2.get((left, mid), 0)
                count_left_mid_right = self.relation3.get((left, mid), {}).get(right, 0)
                p3 = count_left_mid and count_left_mid_right / count_left_mid
                p = p_last * (smooth_1 * p1 + smooth_2 * p2 + (1 - smooth_1 - smooth_2) * p3)
                if p == 0:
                    continue
                state[right, mid][left] = p
                state[right, mid][0] = max(state[right, mid].get(0, 0), p)
        return state

    def predict(self, pinyin: str):
        stop = len(self.chars) - 1  # for $
        start = stop - 1  # for ^
        states = [{(start, start): {0: 1}}]
        for each in pinyin.split():
            each = each.lower()
            candidates = self.table.get(each)
            if not candidates:
                raise StrangePinyinError(each)
            states.append(self._get_next_state(states[-1], candidates))
        states.append(self._get_next_state(states[-1], [stop]))
        states.append(self._get_next_state(states[-1], [stop]))
        result = [stop, stop]
        for state in states[:1:-1]:
            right, mid = result[-2:]
            transition = state[right, mid]
            transition.pop(0)
            result.append(max(transition, key=lambda x: transition[x]))
        return ''.join(map(lambda x: self.chars[x], reversed(result[2:-1])))
