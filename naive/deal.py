def deal_text_naive(text: str, char_to_index: dict, record: dict, binary_record: dict):
    start = 0
    stop = len(char_to_index) + 1
    left = start
    for right in text:
        right = char_to_index.get(right, start)
        if right:
            record[right] += 1
            binary_record[left][right] += 1
        elif left:
            binary_record[left][stop] += 1
        left = right
    return
