from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.policies.operations import PolicyOperations
from app.policies.preview import PolicyPreviews
from app.policies.routes import chunk_page, find_policy, library_dependency, same_origin
from app.policies.store import PolicyConflict

router = APIRouter(prefix='/api/policies', tags=['policies'])


class ChunkSettings(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    strategy: Literal['characters', 'sentences', 'paragraphs', 'html']
    size: int = Field(ge=100, le=20_000)
    overlap: int = Field(ge=0)
    heading_depth: int = Field(ge=1, le=6)


class PreviewRequest(BaseModel):
    settings: ChunkSettings
    version: int = Field(ge=1)


class ApplyRequest(BaseModel):
    preview_id: str
    version: int = Field(ge=1)


@router.post('/{policy_id}/previews')
def preview_policy(policy_id: str, payload: PreviewRequest, request: Request,
                   library=Depends(library_dependency)):
    same_origin(request)
    find_policy(library, policy_id)
    try:
        preview = PolicyPreviews(library).create(policy_id, payload.settings.model_dump(), payload.version)
        return {'id': preview['id'], 'version': preview['version'], 'settings': preview['settings'],
                'chunks': chunk_page(preview['chunks'], 0, 20)}
    except PolicyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def find_preview(library, policy_id, preview_id):
    find_policy(library, policy_id)
    try:
        preview = library.store.revision(preview_id)
        if preview['policy_id'] != policy_id:
            raise KeyError('Preview not found')
        return preview
    except KeyError as exc:
        raise HTTPException(404, 'Preview not found.') from exc


@router.get('/{policy_id}/previews/{preview_id}/chunks')
def preview_chunks(policy_id: str, preview_id: str, offset: int = Query(0, ge=0),
                   limit: int = Query(20, ge=1, le=100), library=Depends(library_dependency)):
    preview = find_preview(library, policy_id, preview_id)
    return chunk_page(preview['chunks'], offset, limit)


@router.post('/{policy_id}/apply', status_code=202)
def apply_preview(policy_id: str, payload: ApplyRequest, request: Request, background: BackgroundTasks,
                  library=Depends(library_dependency)):
    same_origin(request)
    find_preview(library, policy_id, payload.preview_id)
    try:
        operation = PolicyPreviews(library).apply(policy_id, payload.preview_id, payload.version)
    except PolicyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    background.add_task(PolicyOperations(library).run, operation['id'])
    return operation
