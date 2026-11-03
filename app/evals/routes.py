from functools import lru_cache

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.config import get_settings
from app.evals.demo_store import RunStore, RunConflict
from app.policies.library import get_library
from app.policies.routes import same_origin

router = APIRouter(prefix='/api/evaluations', tags=['evaluations'])


@lru_cache
def store_for(directory):
    return RunStore(directory)


def get_store():
    return store_for(get_settings().vector_store_dir.parent / 'evaluations')


@router.get('')
def metadata():
    from app.evals.demo_metrics import METRICS, CHECKS, CLARITY, RUBRIC_VERSION
    from app.evals.demo_dataset import DATASET_VERSION
    settings = get_settings()
    return {'metrics': METRICS, 'checks': CHECKS, 'clarity_rubric': CLARITY,
            'dataset_version': DATASET_VERSION, 'rubric_version': RUBRIC_VERSION,
            'judge_model': settings.eval_judge_model, 'answer_model': settings.openai_chat_model,
            'configured': bool(settings.openai_api_key), 'case_count': 18, 'eligible_count': 16}


@router.get('/runs')
def list_runs(store=Depends(get_store)):
    return store.list()


@router.get('/runs/{id}')
def get_run(id: str, store=Depends(get_store)):
    try:
        return store.get(id)
    except KeyError as exc:
        raise HTTPException(404, 'Evaluation not found.') from exc


@router.post('/runs', status_code=202)
def start_run(request: Request, background: BackgroundTasks, store=Depends(get_store), library=Depends(get_library)):
    from app.evals.demo_service import create_run, run_in_background
    same_origin(request)
    try:
        run = create_run(store, library, get_settings())
    except RunConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    background.add_task(run_in_background, store, run, library, get_settings())
    return run
