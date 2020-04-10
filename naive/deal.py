def deal_text_naive(text: str, char_to_index: dict, record: dict, binary_record: dict):
    left = None
    for right in text:
        right = char_to_index.get(right)
        if right:
            record[right] += 1
            if left:
                binary_record[left][right] += 1
        left = right
    return
