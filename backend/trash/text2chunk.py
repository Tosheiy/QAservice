def text2chunk(target_text, num=5):
    length = len(target_text)
    chunk_size = (length + num - 1) // num
    return [target_text[i * chunk_size: (i + 1) * chunk_size] for i in range(num)]