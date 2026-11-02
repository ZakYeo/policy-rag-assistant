"""Conservative byte budgets bound byte-level BPE tokens without tokenizer downloads."""

INPUT_BYTES = 8000
REQUEST_BYTES = 200_000
REQUEST_ITEMS = 128


def text_pieces(text):
    if not text.strip():
        raise ValueError('Cannot embed empty policy text.')
    start = 0
    size = 0
    for index, character in enumerate(text):
        width = len(character.encode('utf-8'))
        if size + width > INPUT_BYTES:
            yield text[start:index], size
            start, size = index, 0
        size += width
    if start < len(text):
        yield text[start:], size


def embedding_batches(texts):
    batch = []
    size = 0
    for owner, text in enumerate(texts):
        for piece, weight in text_pieces(text):
            if batch and (size + weight > REQUEST_BYTES or len(batch) >= REQUEST_ITEMS):
                yield batch
                batch, size = [], 0
            batch.append((owner, piece, weight))
            size += weight
    if batch:
        yield batch
