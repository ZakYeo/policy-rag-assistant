"""Explicit paid demo run: python -m app.evals.demo_cli."""
import asyncio
import argparse

from app.config import get_settings
from app.evals.demo_service import create_run, execute_run
from app.evals.routes import get_store
from app.policies.library import get_library


def main():
    parser = argparse.ArgumentParser(description='Run a paid RAG evaluation or judge challenge check.')
    parser.add_argument('--calibrate', action='store_true', help='Run separate developer-labeled judge challenges, not the benchmark.')
    args = parser.parse_args()
    if args.calibrate:
        from app.evals.calibration import run_calibration
        settings = get_settings()
        report = asyncio.run(run_calibration(settings, settings.vector_store_dir.parent / 'evaluations'))
        print(f"Judge challenge agreement: {sum(item['agrees'] for item in report['results'])}/{len(report['results'])}. Human calibration remains pending.")
        return 0
    settings, library, store = get_settings(), get_library(), get_store()
    run = create_run(store, library, settings)
    print(f"Evaluation {run['id']} started; results in {store.path}", flush=True)
    asyncio.run(execute_run(store, run, library, settings))
    print(f"{run['status']}: {run['progress']}/{run['total']} results", flush=True)
    if run['error']:
        print(run['error'], flush=True)
    return 0 if run['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
