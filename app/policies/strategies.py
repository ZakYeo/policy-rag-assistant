"""Deterministic, character-bounded splitters with source offsets."""
import re
from bisect import bisect_right

from app.ingest.chunker import split_text

STRATEGIES = {'characters', 'sentences', 'paragraphs', 'html'}


def validate_settings(settings, format):
    if set(settings) != {'strategy', 'size', 'overlap', 'heading_depth'}:
        raise ValueError('Provide strategy, size, overlap and heading depth.')
    if settings['strategy'] not in STRATEGIES:
        raise ValueError('Choose a supported chunking strategy.')
    if any(type(settings[key]) is not int for key in ('size', 'overlap', 'heading_depth')):
        raise ValueError('Chunk size, overlap and heading depth must be whole numbers.')
    if not 100 <= settings['size'] <= 20_000:
        raise ValueError('Chunk size must be between 100 and 20,000 characters.')
    if not 0 <= settings['overlap'] < settings['size']:
        raise ValueError('Overlap must be zero or greater and smaller than chunk size.')
    if not 1 <= settings['heading_depth'] <= 6:
        raise ValueError('HTML heading depth must be between 1 and 6.')
    if settings['strategy'] == 'html' and format not in {'html', 'htm'}:
        raise ValueError('HTML section splitting is available only for HTML policies.')
    return dict(settings)


def strategy_sections(sections, settings):
    if settings['strategy'] != 'html':
        return sections
    grouped = []
    for section in sections:
        if not grouped or 0 < section['level'] <= settings['heading_depth']:
            grouped.append(dict(section))
        else:
            grouped[-1]['text'] += '\n\n' + section['text']
    return grouped


def split_section(text, settings):
    if settings['strategy'] == 'characters':
        return split_text(text, settings['size'], settings['overlap'], max_chunks=10_000)
    expression = r'[.!?…。！？][\"”’\']?(?=\s|$)' if settings['strategy'] == 'sentences' else r'\n\s*\n'
    boundaries = [match.end() if settings['strategy'] == 'sentences' else match.start()
                  for match in re.finditer(expression, text)]
    boundaries.append(len(text))
    chunks = []
    start = 0
    while start < len(text):
        while start < len(text) and text[start].isspace():
            start += 1
        if start == len(text):
            break
        limit = min(start + settings['size'], len(text))
        minimum = start + (settings['overlap'] if chunks else 0)
        index = bisect_right(boundaries, limit) - 1
        boundary = boundaries[index] if index >= 0 else 0
        possible = boundary > minimum
        end = boundary if possible else limit
        if not possible and limit < len(text):
            space = text.rfind(' ', minimum, limit)
            if space > minimum:
                end = space
        while end > start and text[end - 1].isspace():
            end -= 1
        if end <= start:
            end = limit
        chunks.append((start, end, text[start:end]))
        if len(chunks) > 10_000:
            raise ValueError("This configuration produces too many chunks. Increase size or reduce overlap.")
        if end == len(text):
            break
        next_start = end - settings['overlap']
        start = next_start if next_start > start else end
    return chunks
