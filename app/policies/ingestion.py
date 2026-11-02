from dataclasses import asdict
from uuid import uuid4

from app.ingest.chunker import Chunk
from app.policies.strategies import validate_settings, strategy_sections, split_section
from app.policies.extraction import extract_policy


def build_revision(store, policy, settings=None):
    settings = validate_settings(settings or policy['settings'], policy['format'])
    content = extract_policy(store.original(policy['id']), policy['format'])
    revision_id = uuid4().hex
    chunks = []
    for section in strategy_sections(content, settings):
        prefix = ''
        body = section['text']
        body_offset = 0
        split_settings = dict(settings)
        if settings['strategy'] == 'html' and section['heading']:
            prefix = section['heading'][:min(160, settings['size'] // 3)] + '\n\n'
            heading_prefix = section['heading'] + '\n\n'
            if body.startswith(heading_prefix):
                body_offset = len(heading_prefix)
                body = body[body_offset:]
            split_settings['size'] -= len(prefix)
            split_settings['overlap'] = min(settings['overlap'], split_settings['size'] - 1)
        for start, end, text in split_section(body, split_settings):
            if len(chunks) >= 10_000:
                raise ValueError('This configuration exceeds 10,000 chunks. Increase size or reduce overlap.')
            chunks.append(asdict(Chunk(
                chunk_id=f'{revision_id}:c{len(chunks)}', document_id=policy['id'],
                document_name=policy['filename'], source_path='',
                page_number=section['page_number'], chunk_index=len(chunks),
                char_start=start + body_offset, char_end=end + body_offset, text=prefix + text, revision=revision_id,
                location=section['location'],
            )))
    return {'id': revision_id, 'policy_id': policy['id'], 'version': policy['version'],
            'content': content, 'settings': dict(settings), 'chunks': chunks}
