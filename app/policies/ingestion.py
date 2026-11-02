from dataclasses import asdict
from uuid import uuid4

from app.ingest.chunker import Chunk, split_text
from app.policies.extraction import extract_policy


def build_revision(store, policy, settings=None):
    settings = settings or policy['settings']
    content = extract_policy(store.original(policy['id']), policy['format'])
    revision_id = uuid4().hex
    chunks = []
    for section in content:
        for start, end, text in split_text(section['text'], settings['size'], settings['overlap']):
            chunks.append(asdict(Chunk(
                chunk_id=f'{revision_id}:c{len(chunks)}', document_id=policy['id'],
                document_name=policy['filename'], source_path='',
                page_number=section['page_number'], chunk_index=len(chunks),
                char_start=start, char_end=end, text=text, revision=revision_id,
                location=section['location'],
            )))
    return {'id': revision_id, 'policy_id': policy['id'], 'version': policy['version'],
            'content': content, 'settings': dict(settings), 'chunks': chunks}
