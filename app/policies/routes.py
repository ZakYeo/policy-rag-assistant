from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.policies.library import get_library

router = APIRouter(prefix='/api/policies', tags=['policies'])


def library_dependency():
    return get_library()


def public_policy(policy):
    return {key: value for key, value in policy.items() if key != 'file'}


def find_policy(library, policy_id):
    try:
        return library.store.get(policy_id)
    except KeyError as exc:
        raise HTTPException(404, 'Policy not found.') from exc


@router.get('')
def list_policies(library=Depends(library_dependency)):
    return [public_policy(policy) for policy in library.store.list()]


@router.get('/{policy_id}')
def policy_detail(policy_id: str, library=Depends(library_dependency)):
    policy = find_policy(library, policy_id)
    revision = library.store.revision(policy['revision']) if policy['revision'] else None
    return {**public_policy(policy), 'content': [
        {'text': page['text'], 'location': f"Page {page['page_number']}"}
        for page in revision['content']
    ] if revision else []}


@router.get('/{policy_id}/chunks')
def policy_chunks(policy_id: str, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                  library=Depends(library_dependency)):
    policy = find_policy(library, policy_id)
    chunks = library.store.revision(policy['revision'])['chunks'] if policy['revision'] else []
    return chunk_page(chunks, offset, limit)


def chunk_page(chunks, offset, limit):
    return {'total': len(chunks), 'offset': offset, 'items': [
        {key: value for key, value in chunk.items() if key != 'source_path'}
        for chunk in chunks[offset:offset + limit]
    ]}


@router.get('/{policy_id}/original')
def policy_original(policy_id: str, library=Depends(library_dependency)):
    policy = find_policy(library, policy_id)
    return FileResponse(library.store.original(policy_id), filename=policy['filename'],
                        media_type='application/octet-stream',
                        headers={'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "sandbox"})
