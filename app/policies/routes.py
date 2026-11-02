from fastapi import BackgroundTasks
from urllib.parse import unquote
from app.policies.operations import MAX_UPLOAD_BYTES, PolicyOperations, validate_filename

from fastapi import Request
from pydantic import BaseModel, Field
from app.policies.store import PolicyConflict

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
        {'text': page['text'], 'location': page.get('location') or f"Page {page['page_number']}"}
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


def same_origin(request):
    from urllib.parse import urlsplit
    origin = request.headers.get('origin')
    if request.headers.get('sec-fetch-site') == 'cross-site' or (
        origin and (urlsplit(origin).scheme, urlsplit(origin).netloc) != (request.url.scheme, request.url.netloc)
    ):
        raise HTTPException(403, 'Policy changes must come from this application.')




class RenamePolicy(BaseModel):
    title: str = Field(max_length=160)
    version: int = Field(ge=1)


@router.patch('/{policy_id}')
def rename_policy(policy_id: str, payload: RenamePolicy, request: Request,
                  library=Depends(library_dependency)):
    same_origin(request)
    find_policy(library, policy_id)
    try:
        return public_policy(library.store.rename(policy_id, payload.title, payload.version))
    except PolicyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


class PolicyVersion(BaseModel):
    version: int = Field(ge=1)


@router.delete('/{policy_id}')
def delete_policy(policy_id: str, payload: PolicyVersion, request: Request,
                  library=Depends(library_dependency)):
    same_origin(request)
    find_policy(library, policy_id)
    try:
        library.delete(policy_id, payload.version)
    except PolicyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'deleted': True}



operation_router = APIRouter(prefix='/api/operations', tags=['policies'])


@router.post('', status_code=202)
async def upload_policy(request: Request, background: BackgroundTasks,
                        library=Depends(library_dependency)):
    same_origin(request)
    filename = unquote(request.headers.get('x-filename', ''))
    try:
        validate_filename(filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    content = bytearray()
    async for block in request.stream():
        if len(content) + len(block) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, 'Upload a file of at most 20 MiB.')
        content.extend(block)
    try:
        operations = PolicyOperations(library)
        operation = operations.upload(filename, bytes(content))
    except PolicyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    background.add_task(operations.run, operation['id'])
    return operation


@operation_router.get('/{operation_id}')
def operation_status(operation_id: str, library=Depends(library_dependency)):
    try:
        return PolicyOperations(library).get(operation_id)
    except KeyError as exc:
        raise HTTPException(404, 'Operation not found.') from exc


@router.post('/{policy_id}/retry', status_code=202)
def retry_policy(policy_id: str, payload: PolicyVersion, request: Request, background: BackgroundTasks,
                 library=Depends(library_dependency)):
    same_origin(request)
    with library.store.lock:
        policy = find_policy(library, policy_id)
        if policy['version'] != payload.version or policy['status'] != 'failed':
            raise HTTPException(409, 'Refresh the policy before retrying processing.')
        policy['status'] = 'processing'
        library.store.save(policy)
        operations = PolicyOperations(library)
        operation = operations.start(policy)
    background.add_task(operations.run, operation['id'])
    return operation
