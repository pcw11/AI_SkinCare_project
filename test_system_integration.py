import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from backend.db_config import is_postgres_enabled, resolve_database_url
from system_integrated.system_integration import (
    build_analysis_response,
    load_image_from_path,
    process_uploaded_image,
)
from system_integrated.integration_api import create_integration_app
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

    def test_process_uploaded_image_returns_integrated_response(self):
        with tempfile.TemporaryDirectory(prefix="업로드테스트_") as temp_dir:
            image_path = Path(temp_dir) / "face.jpg"
            sample = Image.new("RGB", (64, 64), color=(200, 180, 160))
            sample.save(image_path)

            with image_path.open("rb") as handle:
                response = process_uploaded_image(handle, user_id="upload-user")

            self.assertTrue(response["success"])
            self.assertEqual(response["user_id"], "upload-user")
            self.assertIn("interface_version", response)
            self.assertIn("products", response)
            self.assertIn("llm_report", response)
            self.assertIn("generated_at", response)

    def test_integration_app_upload_route_returns_standard_response(self):
        app = create_integration_app()
        client = app.test_client()

        with tempfile.TemporaryDirectory(prefix="라우트테스트_") as temp_dir:
            image_path = Path(temp_dir) / "face.jpg"
            Image.new("RGB", (64, 64), color=(200, 180, 160)).save(image_path)

            with image_path.open("rb") as handle:
                response = client.post(
                    "/api/v1/analyze",
                    data={"user_id": "route-user", "image": (handle, "face.jpg")},
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["user_id"], "route-user")
        self.assertIn("products", payload)
        self.assertIn("llm_report", payload)

    def test_load_image_from_path_handles_unicode_directory(self):
        with tempfile.TemporaryDirectory(prefix="테스트_이미지_") as temp_dir:
            image_path = Path(temp_dir) / "테스트_샘플.jpg"
            sample = Image.new("RGB", (32, 32), color=(255, 0, 0))
            sample.save(image_path)

            loaded = load_image_from_path(str(image_path))

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.shape[:2], (32, 32))

    def test_recommend_products_filters_allergy_ingredients_and_prefers_formulation(self):
        with tempfile.TemporaryDirectory(prefix="추천테스트_") as temp_dir:
            catalog_path = Path(temp_dir) / "catalog.json"
            catalog_path.write_text(
                """[
                {
                    "product_id": "SAFE_SERUM",
                    "brand": "BrandA",
                    "product_name": "Safe Serum",
                    "product_type": "serum",
                    "ingredients": ["niacinamide", "hyaluronic acid", "panthenol"],
                    "skin_types": ["sensitive"],
                    "target_concerns": ["sensitivity", "pigmentation"],
                    "sensitive_safe": true,
                    "notes": "민감성에 안전한 세럼"
                },
                {
                    "product_id": "BAD_CREAM",
                    "brand": "BrandB",
                    "product_name": "Bad Cream",
                    "product_type": "cream",
                    "ingredients": ["fragrance", "alcohol", "centella asiatica"],
                    "skin_types": ["sensitive"],
                    "target_concerns": ["sensitivity"],
                    "sensitive_safe": false,
                    "notes": "알레르기 유발 성분 포함"
                },
                {
                    "product_id": "NORMAL_LOTION",
                    "brand": "BrandC",
                    "product_name": "Normal Lotion",
                    "product_type": "lotion",
                    "ingredients": ["glycerin", "centella asiatica"],
                    "skin_types": ["sensitive"],
                    "target_concerns": ["dryness"],
                    "sensitive_safe": true,
                    "notes": "보습용 로션"
                }
            ]""",
                encoding="utf-8",
            )

            skin_profile = {
                "skin_type": "sensitive",
                "concerns": ["sensitivity", "pigmentation"],
                "allergy_ingredients": ["fragrance", "alcohol"],
                "preferred_formulations": ["serum"],
            }
            analysis_result = {
                "scores": {"acne": 40, "pigmentation": 70, "pore": 50, "sebum": 30},
                "concerns": ["sensitivity", "pigmentation"],
                "skin_type": "sensitive",
            }

            products = recommend_products(skin_profile, analysis_result, limit=5, product_db_path=catalog_path)

            self.assertTrue(products)
            self.assertEqual(products[0]["product_name"], "Safe Serum")
            self.assertNotIn("Bad Cream", [p["product_name"] for p in products])
            self.assertTrue(all("fragrance" not in p["ingredients"] and "alcohol" not in p["ingredients"] for p in products))

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
