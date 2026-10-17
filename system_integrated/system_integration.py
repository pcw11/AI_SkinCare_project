import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

try:
    from .llm_service import generate_llm_report
    from .product_recommender import recommend_products
except ImportError:  # pragma: no cover
    from llm_service import generate_llm_report
    from product_recommender import recommend_products


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_MODULE_PATH = PROJECT_ROOT / "algorithm" / "test.py"
BACKEND_DB_PATH = PROJECT_ROOT / "backend" / "skincare.db"


def _load_ai_module():
    """algorithm/test.py를 불러와 분석 로직을 재사용한다."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ai_skin_module", AI_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"AI 모듈 로딩 실패: {AI_MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_image_from_path(image_path: str | os.PathLike[str]) -> np.ndarray:
    """한글 경로를 포함한 이미지 경로를 안전하게 로드한다."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"이미지 없음: {image_path}")

    img_bgr = cv2.imread(str(path))
    if img_bgr is not None:
        return img_bgr

    try:
        from PIL import Image as PILImage
        with PILImage.open(str(path)) as pil_image:
            rgb = np.array(pil_image.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        raise ValueError(f"이미지 디코딩 실패: {image_path}") from exc


def normalize_scores(raw_values):
    """백엔드/앱이 공통으로 쓰는 스키마로 변환한다."""
    ai = _load_ai_module()

    scores = {
        "acne": ai.normalize("acne", raw_values["acne"]),
        "pigmentation": ai.normalize("pigmentation", raw_values["pigmentation"]),
        "pore": ai.normalize("pore", raw_values["pore"]),
        "sebum": ai.normalize("sebum", raw_values["sebum"]),
    }
    total_score = max(0, 100 - round(sum(scores.values()) / len(scores)))

    return {
        "success": True,
        "total_score": total_score,
        "scores": scores,
        "raw_values": raw_values,
    }


def infer_concerns(scores: Dict[str, Any]) -> List[str]:
    """점수 기반으로 주 고민을 추론한다."""
    concern_order = [
        ("acne", scores.get("acne", 0)),
        ("sebum", scores.get("sebum", 0)),
        ("pigmentation", scores.get("pigmentation", 0)),
        ("pore", scores.get("pore", 0)),
    ]
    concerns = [name for name, value in concern_order if value >= 60]
    return concerns or ["balanced"]


def build_analysis_response(ai_result: Dict[str, Any], products: Optional[List[Dict[str, Any]]] = None, llm_report: Optional[Dict[str, Any]] = None, user_id: str = "demo-user") -> Dict[str, Any]:
    """앱-백엔드-LLM-추천을 하나의 표준 응답으로 통합한다."""
    response = {
        "success": bool(ai_result.get("success", True)),
        "interface_version": "1.0",
        "analysis_id": ai_result.get("analysis_id") or f"analysis_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "user_id": user_id,
        "skin_type": ai_result.get("skin_type", "normal"),
        "total_score": ai_result.get("total_score", 0),
        "scores": ai_result.get("scores", {}),
        "raw_values": ai_result.get("raw_values", {}),
        "concerns": ai_result.get("concerns") or infer_concerns(ai_result.get("scores", {})),
        "products": products or [],
        "llm_report": llm_report or {
            "provider": "local",
            "summary": "기본 루틴으로 세정, 진정, 보습을 유지하는 방식으로 관리해 주세요.",
            "key_points": ["수분 유지", "여드름 관리", "민감성 보호"],
            "caution": "민감성 피부는 성분 테스트 후 사용해 주세요.",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return response


def run_ai_analysis(image_path=None, image_bytes=None):
    """기존 AI 로직을 그대로 호출해 결과를 표준 응답 형태로 변환한다.
    파일 경로 또는 메모리 바이트 둘 다 허용한다.
    """
    ai = _load_ai_module()

    if image_bytes is not None:
        file_bytes = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    else:
        img_bgr = load_image_from_path(image_path)

    if img_bgr is None:
        raise ValueError("이미지 디코딩 실패")

    roi_bgr_processed, roi_gray = ai.preprocess(ai.extract_roi_mediapipe(img_bgr))
    raw = {
        "acne": ai.detect_acne(roi_bgr_processed),
        "pigmentation": ai.detect_pigmentation(roi_gray),
        "pore": ai.detect_pore(roi_gray),
        "sebum": ai.detect_sebum(roi_gray),
    }

    scores = {
        "acne": ai.normalize("acne", raw["acne"]),
        "pigmentation": ai.normalize("pigmentation", raw["pigmentation"]),
        "pore": ai.normalize("pore", raw["pore"]),
        "sebum": ai.normalize("sebum", raw["sebum"]),
    }

    total_score = max(0, 100 - round(sum(scores.values()) / len(scores)))
    result = {
        "success": True,
        "skin_type": ai.get_skin_type(roi_gray),
        "total_score": total_score,
        "scores": scores,
        "raw_values": {
            "acne_count": raw["acne"],
            "pigmentation_count": raw["pigmentation"],
            "pore_variance": round(raw["pore"], 4),
            "sebum_ratio": round(raw["sebum"] * 100, 1),
        },
    }
    result["concerns"] = infer_concerns(scores)
    return result


def ensure_db(db_path=BACKEND_DB_PATH):
    """기존 백엔드 DB 구조를 그대로 사용한다."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email VARCHAR UNIQUE,
            password_hash VARCHAR,
            nickname VARCHAR,
            gender VARCHAR,
            birth_year INTEGER,
            skin_type VARCHAR,
            skin_concern TEXT,
            allergy_ingredients TEXT,
            preferred_formulations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS skin_analyses (
            analyses_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            image_url VARCHAR,
            score_total INTEGER,
            score_acne INTEGER,
            score_pore INTEGER,
            score_pigmentation INTEGER,
            score_sebum INTEGER,
            raw_values TEXT,
            bbox_coordinates TEXT,
            llm_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis_result(user_id, ai_result, image_url=None, db_path=BACKEND_DB_PATH):
    """분석 결과를 기존 테이블 구조에 맞춰 저장한다."""
    db_path = Path(db_path)
    ensure_db(db_path)

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO skin_analyses (
            user_id, image_url, score_total, score_acne, score_pore,
            score_pigmentation, score_sebum, raw_values, llm_report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            image_url,
            ai_result["total_score"],
            ai_result["scores"]["acne"],
            ai_result["scores"]["pore"],
            ai_result["scores"]["pigmentation"],
            ai_result["scores"]["sebum"],
            json.dumps(ai_result.get("raw_values", {}), ensure_ascii=False),
            json.dumps(ai_result.get("llm_report", {}), ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def integrate_analysis(
    image_path=None,
    user_id="demo-user",
    image_url=None,
    db_path=BACKEND_DB_PATH,
    image_bytes=None,
    skin_profile: Optional[Dict[str, Any]] = None,
    product_db_path: Optional[str] = None,
):
    """AI 분석, 제품 추천, LLM 요약을 하나의 표준 흐름으로 조합한다."""
    ai_result = run_ai_analysis(image_path=image_path, image_bytes=image_bytes)
    profile = {
        "user_id": user_id,
        "skin_type": ai_result.get("skin_type", "normal"),
        "concerns": ai_result.get("concerns", ["balanced"]),
    }
    if skin_profile:
        profile.update(skin_profile)

    products = recommend_products(profile, ai_result, limit=5, product_db_path=product_db_path)
    llm_report = generate_llm_report(profile, ai_result, products)
    ai_result["user_id"] = user_id
    ai_result["llm_report"] = llm_report
    ai_result["products"] = products
    save_analysis_result(user_id, ai_result, image_url=image_url, db_path=db_path)

    response = build_analysis_response(ai_result, products=products, llm_report=llm_report, user_id=user_id)
    return response


def process_uploaded_image(
    uploaded_file,
    user_id="demo-user",
    image_url=None,
    db_path=BACKEND_DB_PATH,
    product_db_path=None,
    skin_profile: Optional[Dict[str, Any]] = None,
):
    """앱/플라스크 업로드 파일 객체를 표준 통합 응답으로 처리한다.

    file-like object, bytes, 또는 로컬 파일 경로를 모두 허용한다.
    """
    if uploaded_file is None:
        raise ValueError("업로드할 이미지 파일이 필요합니다.")

    if hasattr(uploaded_file, "read"):
        payload = uploaded_file.read()
        if not payload:
            raise ValueError("빈 이미지 파일입니다.")
        return integrate_analysis(
            user_id=user_id,
            image_url=image_url,
            db_path=db_path,
            image_bytes=payload,
            skin_profile=skin_profile,
            product_db_path=product_db_path,
        )

    if isinstance(uploaded_file, (bytes, bytearray)):
        return integrate_analysis(
            user_id=user_id,
            image_url=image_url,
            db_path=db_path,
            image_bytes=bytes(uploaded_file),
            skin_profile=skin_profile,
            product_db_path=product_db_path,
        )

    if isinstance(uploaded_file, (str, os.PathLike)):
        return integrate_analysis(
            image_path=str(uploaded_file),
            user_id=user_id,
            image_url=image_url,
            db_path=db_path,
            skin_profile=skin_profile,
            product_db_path=product_db_path,
        )

    raise TypeError("지원하지 않는 업로드 데이터 형식입니다.")


def main():
    parser = argparse.ArgumentParser(description="MirrorMe 통합 분석 실행기")
    parser.add_argument("--image", required=True, help="분석할 이미지 경로")
    parser.add_argument("--user-id", default="demo-user", help="사용자 ID")
    parser.add_argument("--db-path", default=str(BACKEND_DB_PATH), help="SQLite DB 경로")
    parser.add_argument("--product-db", default=None, help="제품 DB JSON 경로")
    args = parser.parse_args()

    try:
        response = integrate_analysis(
            image_path=args.image,
            user_id=args.user_id,
            db_path=args.db_path,
            product_db_path=args.product_db,
        )
        print(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
