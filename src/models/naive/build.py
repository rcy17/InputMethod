import sqlite3
import json
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm


def create_raw_table(connection: sqlite3.Connection):
    sql = """
        CREATE TABLE charset (
            char CHARACTER (1) UNIQUE,
            count INT
        );
        CREATE TABLE relation (
            left INT,
            right INT,
            count INT,
            FOREIGN KEY(left) REFERENCES charset(oid),
            FOREIGN KEY(right) REFERENCES charset(oid)
        );
        CREATE UNIQUE INDEX relation_index on relation(left, right);
        CREATE TABLE pinyin_set (
            pinyin CHARACTER (8) UNIQUE
        );
        CREATE TABLE pinyin_char (
            pinyin INT,
            char INT,
            FOREIGN KEY(pinyin) REFERENCES pinyin(oid),
            FOREIGN KEY(char) REFERENCES charset(oid)
        );
        CREATE INDEX pinyin_charset_index on pinyin_char(pinyin);
    """
    connection.executescript(sql)
    print('Finished table creation')


def read_charset(connection: sqlite3.Connection, path: Path):
    charset = open(str(path.joinpath('charset.txt')), encoding='gbk').read()
    if connection:
        with connection:
            sql = 'INSERT INTO charset values (?, 0)'
            cursor = connection.cursor()
            cursor.executemany(sql, charset)
            cursor.execute(sql, '^')
            cursor.execute(sql, '$')
        print('Finished charset initialization')
    return set(charset), {char: index + 1 for index, char in enumerate(charset)}


def read_pinyin(connection: sqlite3.Connection, path: Path, char_to_index: dict):
    pinyin_table = {l.split()[0]: l.split()[1:] for l in open(str(path.joinpath('table.txt')), encoding='gbk')}
    if connection:
        sql = f'INSERT INTO pinyin_set values (?)'
        connection.executemany(sql, ((pinyin,) for pinyin in pinyin_table.keys()))
        print('Finished pinyin_set insertion')
        sql = f'INSERT INTO pinyin_char values (?, ?)'
        for index, chars in enumerate(pinyin_table.values()):
            connection.executemany(sql, ((index + 1, char_to_index[char]) for char in chars))
        connection.commit()
        print('Finished pinyin_set and pinyin_char initialization')
    return pinyin_table


def read_data(path):
    for file in path.iterdir():
        if file.name[:4] != '2016':
            continue
        bar = tqdm(open(file, encoding='gbk'))
        bar.set_description(str(file))
        for line in bar:
            yield json.loads(line)


def regularize_relation(relation: dict):
    for key, value in relation.items():
        relation[key] = dict(sorted(value.items(), key=lambda x: x[1], reverse=True)[:100])


def insert_result(connection: sqlite3.Connection, record: dict, binary_record: dict):
    with connection:
        sql = 'UPDATE charset SET count=? WHERE oid=?'
        connection.executemany(sql, ((count, index) for index, count in record.items()))
    print('Finished word record insertion')
    regularize_relation(binary_record)
    with connection:
        sql = 'INSERT INTO relation values (?, ?, ?)'
        connection.executemany(sql, ((l, r, c) for l, d in binary_record.items() for r, c in d.items()))
    print('Finished relation insertion')


def deal_text(text: str, char_to_index: dict, record: dict, binary_record: dict):
    start = len(char_to_index) + 1
    stop = len(char_to_index) + 2
    left = start
    for right in text:
        right = char_to_index.get(right, start)
        record[right] += 1
        if right != start:
            binary_record[left][right] += 1
        elif left != start:
            binary_record[left][stop] += 1
        left = right
    return


def train(path: str, model_path: str):
    path = Path(path)
    connection = sqlite3.connect(model_path)
    create_raw_table(connection)
    charset, index_to_char = read_charset(connection, path)
    read_pinyin(connection, path, index_to_char)
    record = {i + 1: 0 for i in range(len(charset) + 1)}
    binary_record = {i + 1: defaultdict(int) for i in range(len(charset) + 1)}
    for data in read_data(path):
        deal_text(data['title'], index_to_char, record, binary_record)
        deal_text(data['html'], index_to_char, record, binary_record)
    insert_result(connection, record, binary_record)
    connection.close()
