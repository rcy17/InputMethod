import sqlite3
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from pypinyin import lazy_pinyin, STYLE_NORMAL, load_single_dict, load_phrases_dict
from tqdm import tqdm

import settings

REGULAR_PINYIN = {
    'lve': 'lue',
    'nve': 'nue',
}

FORCE_PINYIN = {
    '哪': 'na',
    '加': 'jia',
    '嗯': 'en',
    '帧': 'zhen',
    '寻': 'xun',
}


def create_raw_table(connection: sqlite3.Connection):
    if not connection:
        print('Database already exists')
        return
    sql = """
        CREATE TABLE IF NOT EXISTS char_set (
            pinyin CHARACTER (7),
            char CHARACTER (1),
            count INT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS pinyin_char on char_set(pinyin, char);
        CREATE TABLE IF NOT EXISTS relation (
            left INT,
            middle INT,
            right INT,
            count INT,
            FOREIGN KEY(left) REFERENCES char_set(oid),
            FOREIGN KEY(middle) REFERENCES char_set(oid),
            FOREIGN KEY(right) REFERENCES char_set(oid)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS relation_index on relation(left, middle, right);
    """
    connection.executescript(sql)
    print('Finished table creation')


def read_pinyin(connection: sqlite3.Connection, path: Path):
    pinyin_table = {l.split()[0]: l.split()[1:] for l in open(str(path.joinpath('table.txt')), encoding='gbk')}
    pinyin_char_table = {data: index + 1 for index, data in enumerate(
        (pinyin, char) for pinyin, chars in pinyin_table.items() for char in chars)}
    if connection:
        print('Finished pinyin_set insertion')
        sql = f'INSERT INTO char_set values (?, ?, 0)'
        connection.executemany(sql, pinyin_char_table)
        connection.execute(sql, ('', '^'))
        connection.execute(sql, ('', '$'))
        connection.commit()
        print('Finished pinyin_set and pinyin_char initialization')
    return pinyin_table, pinyin_char_table


def read_data(path):
    keyword = settings.key
    for file in path.iterdir():
        if keyword not in str(file):
            continue
        bar = tqdm(open(file, encoding='gbk'))
        bar.set_description(str(file))
        for line in bar:
            yield json.loads(line)


def regularize_relation(relation: dict):
    for key, value in relation.items():
        relation[key] = dict(sorted(value.items(), key=lambda x: x[1], reverse=True)[:100])


def insert_result(connection: sqlite3.Connection, record: dict, binary_record: dict):
    now = datetime.now()
    with connection:
        sql = 'UPDATE char_set SET count=count+? WHERE oid=?'
        connection.executemany(sql, ((count, index) for index, count in record.items()))
    print('Finished word record insertion in', (datetime.now() - now).total_seconds(), 's')
    now = datetime.now()
    with connection:
        sql = 'INSERT OR IGNORE INTO relation values (?, ?, ?, 0) '
        connection.executemany(sql, ((*k, r) for k, d in binary_record.items() for r, c in d.items()))
        sql = 'UPDATE relation SET count=count+? where left=? and middle=? and right=?'
        connection.executemany(sql, ((c, *k, r) for k, d in binary_record.items() for r, c in d.items()))
    print('Finished relation insertion in', (datetime.now() - now).total_seconds(), 's')


def register_pinyin():
    """
    register pypinyin for some special character
    """
    single_dict = {
        ord('哪'): 'na'
    }
    phrases_dict = {
        '哪些': [['na'], ['xie']]
    }
    load_single_dict(single_dict)
    load_phrases_dict(phrases_dict)


def deal_text(text: str, pinyin_char_table: dict, record: dict, ternary_record: dict):
    start = len(pinyin_char_table) + 1
    stop = len(pinyin_char_table) + 2
    left = start
    middle = start
    notation = lazy_pinyin(text, style=STYLE_NORMAL, errors=lambda x: [None] * len(x))
    for pinyin, char in zip(notation, text):
        if pinyin is None:
            right = start
        else:
            pinyin = REGULAR_PINYIN.get(pinyin, pinyin)
            pinyin = FORCE_PINYIN.get(char, pinyin)
            right = pinyin_char_table.get((pinyin, char), start)
            if settings.warning and right == start:
                print('WARNING: strang (pinyin, char):', pinyin, char)
        record[right] += 1
        if right != start:
            ternary_record[(left, middle)][right] += 1
        else:
            if left != start:
                ternary_record[(left, middle)][stop] += 1
            ternary_record[(middle, stop)][stop] += 1
            # Impossible for left != start but middle == start
            middle = start
        left, middle = middle, right
    return


def train(path: str, model_path: str):
    register_pinyin()
    path = Path(path)
    connection = not Path(model_path).exists() and sqlite3.connect(model_path)
    create_raw_table(connection)
    pinyin_table, pinyin_char_table = read_pinyin(connection, path)
    record = {i + 1: 0 for i in range(len(pinyin_char_table) + 1)}
    ternary_record = defaultdict(lambda: defaultdict(int))
    for data in read_data(path):
        deal_text(data['title'], pinyin_char_table, record, ternary_record)
        deal_text(data['html'], pinyin_char_table, record, ternary_record)
    regularize_relation(ternary_record)
    connection = connection or sqlite3.connect(model_path, timeout=300)
    insert_result(connection, record, ternary_record)
    connection.close()
