import json
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "dataset" / "skincare_products_data" / "products_sample.json"


def _default_product_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "product_id": "P1001",
            "brand": "Round Lab",
            "product_name": "1025 Dokdo Cleanser",
            "product_type": "cleanser",
            "ingredients": ["glycerin", "salicylic acid", "centella asiatica", "tea tree"],
            "skin_types": ["oily", "combination"],
            "target_concerns": ["acne", "sebum"],
            "sensitive_safe": True,
            "notes": "가벼운 세정과 여드름 관리에 적합",
        },
        {
            "product_id": "P1002",
            "brand": "Cosrx",
            "product_name": "BHA Blackhead Power Liquid",
            "product_type": "essence",
            "ingredients": ["salicylic acid", "butylene glycol", "niacinamide"],
            "skin_types": ["oily", "acne-prone"],
            "target_concerns": ["acne", "pore", "sebum"],
            "sensitive_safe": False,
            "notes": "모공 및 피지 관리에 도움",
        },
        {
            "product_id": "P1003",
            "brand": "The Face Shop",
            "product_name": "Rice Water Bright Cleansing Foam",
            "product_type": "cleanser",
            "ingredients": ["rice extract", "niacinamide", "hyaluronic acid"],
            "skin_types": ["dry", "normal", "combination"],
            "target_concerns": ["pigmentation", "dryness"],
            "sensitive_safe": True,
            "notes": "민감도 낮고 보습과 광채 관리에 적합",
        },
        {
            "product_id": "P1004",
            "brand": "Anua",
            "product_name": "Heartleaf Silky Moisture Cream",
            "product_type": "cream",
            "ingredients": ["hyaluronic acid", "centella asiatica", "panthenol"],
            "skin_types": ["dry", "sensitive", "combination"],
            "target_concerns": ["hydration", "sensitivity"],
            "sensitive_safe": True,
            "notes": "민감성 피부에 보습과 진정 효과",
        },
        {
            "product_id": "P1005",
            "brand": "Ildong",
            "product_name": "Acnederm Multi Essence",
            "product_type": "serum",
            "ingredients": ["niacinamide", "centella asiatica", "tea tree", "betaine"],
            "skin_types": ["oily", "combination"],
            "target_concerns": ["acne", "pigmentation", "sebum"],
            "sensitive_safe": True,
            "notes": "여드름 진정과 잡티 관리에 균형적",
        },
        {
            "product_id": "P1006",
            "brand": "numbuzin",
            "product_name": "No. 3 Skin Softening Serum",
            "product_type": "serum",
            "ingredients": ["niacinamide", "panthenol", "hyaluronic acid", "betaine"],
            "skin_types": ["normal", "dry", "combination"],
            "target_concerns": ["pigmentation", "hydration"],
            "sensitive_safe": True,
            "notes": "톤업과 보습을 함께 고려한 제품",
        },
    ]


def load_product_catalog(product_db_path: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    target = Path(product_db_path) if product_db_path else DEFAULT_CATALOG_PATH
    if not target.exists():
        return _default_product_catalog()

    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_product_catalog()

    if isinstance(data, dict):
        products = data.get("products", [])
    else:
        products = data

    return products if isinstance(products, list) else _default_product_catalog()


def _normalize_ingredient_names(product: Dict[str, Any]) -> List[str]:
    raw = product.get("ingredients") or []
    if isinstance(raw, str):
        return [item.strip().lower() for item in raw.replace("/", ",").split(",") if item.strip()]
    return [str(item).strip().lower() for item in raw]


def recommend_products(
    skin_profile: Dict[str, Any],
    analysis_result: Dict[str, Any],
    limit: int = 5,
    product_db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """사용자 피부 프로필과 분석 결과를 기반으로 제품 추천을 계산한다."""
    catalog = load_product_catalog(product_db_path)
    if not catalog:
        return []

    profile = dict(skin_profile or {})
    skin_type = str(profile.get("skin_type") or analysis_result.get("skin_type") or "normal").lower()
    concerns = [str(c).lower() for c in (analysis_result.get("concerns") or profile.get("concerns") or [])]
    if not concerns:
        concerns = ["acne"]

    scored: List[Dict[str, Any]] = []
    for product in catalog:
        ingredients = _normalize_ingredient_names(product)
        product_text = " ".join([product.get("product_name", ""), product.get("brand", ""), *ingredients]).lower()
        match_score = 0

        for concern in concerns:
            target_concerns = {str(item).lower() for item in (product.get("target_concerns") or [])}
            if concern in target_concerns:
                match_score += 30
            if concern == "acne" and any(item in product_text for item in ["salicylic acid", "niacinamide", "tea tree", "centella"]):
                match_score += 20
            if concern == "sebum" and any(item in product_text for item in ["salicylic acid", "niacinamide", "tea tree"]):
                match_score += 15
            if concern == "pigmentation" and any(item in product_text for item in ["niacinamide", "hyaluronic acid", "panthenol"]):
                match_score += 10

        if skin_type in {"oily", "combination"} and any(item in product_text for item in ["salicylic acid", "tea tree"]) :
            match_score += 10
        if skin_type in {"dry", "sensitive"} and any(item in product_text for item in ["hyaluronic acid", "centella asiatica", "panthenol"]) :
            match_score += 12

        if profile.get("sensitive"):
            if any(item in product_text for item in ["alcohol", "fragrance", "essential oil"]):
                match_score -= 20
            if product.get("sensitive_safe"):
                match_score += 10

        product_name = product.get("product_name") or "Unknown product"
        scored.append(
            {
                "product_id": product.get("product_id", "P0000"),
                "brand": product.get("brand", "Unknown brand"),
                "product_name": product_name,
                "product_type": product.get("product_type", "unknown"),
                "ingredients": ingredients,
                "match_score": max(0, round(match_score, 1)),
                "reason": product.get("notes", "사용자 피부 상태에 적합한 제품"),
            }
        )

    ranked = sorted(scored, key=lambda item: item["match_score"], reverse=True)
    return ranked[:limit]
