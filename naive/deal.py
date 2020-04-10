def deal_text_naive(text: str, char_to_index: dict, record: dict, binary_record: dict):
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
