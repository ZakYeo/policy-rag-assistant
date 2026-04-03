import os
import unittest

from app.config import get_settings
from app.main import create_app


class AppSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = os.environ.copy()
        os.environ["APP_ENV"] = "test"
        get_settings.cache_clear()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        get_settings.cache_clear()

    def test_healthcheck_returns_environment(self) -> None:
        app = create_app()
        health_route = next(route for route in app.routes if route.path == "/health")

        payload = health_route.endpoint()

        self.assertEqual(payload, {"status": "ok", "environment": "test"})

    def test_root_returns_setup_status(self) -> None:
        app = create_app()
        root_route = next(route for route in app.routes if route.path == "/")

        payload = root_route.endpoint()

        self.assertEqual(payload["name"], "Policy RAG Assistant")
        self.assertEqual(payload["status"], "setup-complete")
        self.assertTrue(payload["documents_dir"].endswith("documents"))
        self.assertTrue(payload["vector_store_dir"].endswith("data/chroma"))
