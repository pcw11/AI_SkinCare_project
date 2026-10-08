import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import cv2
import numpy as np


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


def run_ai_analysis(image_path=None, image_bytes=None):
    """기존 AI 로직을 그대로 호출해 결과를 표준 응답 형태로 변환한다.
    파일 경로 또는 메모리 바이트 둘 다 허용한다.
    """
    ai = _load_ai_module()

    if image_bytes is not None:
        file_bytes = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    else:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 없음: {image_path}")
        img_bgr = cv2.imread(image_path)

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

    return {
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
            score_pigmentation, score_sebum, raw_values
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            image_url,
            ai_result["total_score"],
            ai_result["scores"]["acne"],
            ai_result["scores"]["pore"],
            ai_result["scores"]["pigmentation"],
            ai_result["scores"]["sebum"],
            json.dumps(ai_result["raw_values"], ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def integrate_analysis(image_path=None, user_id="demo-user", image_url=None, db_path=BACKEND_DB_PATH, image_bytes=None):
    """기존 구조는 건드리지 않고, 통합 흐름만 추가한다.
    파일 경로 또는 업로드 바이트 둘 다 처리 가능하다.
    """
    ai_result = run_ai_analysis(image_path=image_path, image_bytes=image_bytes)
    save_analysis_result(user_id, ai_result, image_url=image_url, db_path=db_path)

    return {
        "success": True,
        "user_id": user_id,
        "total_score": ai_result["total_score"],
        "scores": ai_result["scores"],
        "raw_values": ai_result["raw_values"],
        "skin_type": ai_result["skin_type"],
    }


def main():
    parser = argparse.ArgumentParser(description="MirrorMe 통합 분석 실행기")
    parser.add_argument("--image", required=True, help="분석할 이미지 경로")
    parser.add_argument("--user-id", default="demo-user", help="사용자 ID")
    parser.add_argument("--db-path", default=str(BACKEND_DB_PATH), help="SQLite DB 경로")
    args = parser.parse_args()

    try:
        response = integrate_analysis(
            image_path=args.image,
            user_id=args.user_id,
            db_path=args.db_path,
        )
        print(json.dumps(response, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
