import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from backend.db_config import is_postgres_enabled, resolve_database_url
from system_integrated.system_integration import build_analysis_response, load_image_from_path
from system_integrated.product_recommender import recommend_products


class SystemIntegrationTest(unittest.TestCase):
    def test_build_analysis_response_has_required_fields(self):
        payload = {
            "success": True,
            "user_id": "demo-user",
            "skin_type": "oily",
            "total_score": 82,
            "scores": {"acne": 73, "pigmentation": 65, "pore": 80, "sebum": 90},
            "raw_values": {
                "acne_count": 12,
                "pigmentation_count": 8,
                "pore_variance": 38.4,
                "sebum_ratio": 54.2,
            },
            "concerns": ["acne", "sebum"],
        }

        response = build_analysis_response(payload)

        self.assertTrue(response["success"])
        self.assertEqual(response["interface_version"], "1.0")
        self.assertEqual(response["products"], [])
        self.assertIn(response["llm_report"]["provider"], {"local", "openai"})
        self.assertIn("scores", response)
        self.assertIn("generated_at", response)

    def test_recommend_products_returns_ranked_list(self):
        skin_profile = {
            "age": 28,
            "skin_type": "oily",
            "concerns": ["acne", "sebum"],
            "sensitive": False,
        }
        analysis_result = {
            "scores": {"acne": 73, "pigmentation": 65, "pore": 80, "sebum": 90},
            "concerns": ["acne", "sebum"],
            "skin_type": "oily",
        }

        products = recommend_products(skin_profile, analysis_result, limit=3)

        self.assertIsInstance(products, list)
        self.assertLessEqual(len(products), 3)
        self.assertTrue(all("product_name" in product for product in products))
        self.assertTrue(all("match_score" in product for product in products))

    def test_load_image_from_path_handles_unicode_directory(self):
        with tempfile.TemporaryDirectory(prefix="테스트_이미지_") as temp_dir:
            image_path = Path(temp_dir) / "테스트_샘플.jpg"
            sample = Image.new("RGB", (32, 32), color=(255, 0, 0))
            sample.save(image_path)

            loaded = load_image_from_path(str(image_path))

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.shape[:2], (32, 32))

    def test_database_url_switches_between_sqlite_and_postgres(self):
        original = os.environ.get("DATABASE_URL")
        try:
            os.environ["DATABASE_URL"] = "sqlite:///backend/skincare.db"
            self.assertFalse(is_postgres_enabled())
            self.assertIn("sqlite", resolve_database_url())

            os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/skincare"
            self.assertTrue(is_postgres_enabled())
            self.assertIn("postgresql", resolve_database_url())
        finally:
            if original is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = original


if __name__ == "__main__":
    unittest.main()
