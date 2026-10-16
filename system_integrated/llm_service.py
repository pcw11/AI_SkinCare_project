import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env_file()


def _get_env_value(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value and str(value).strip():
            return str(value).strip()
    return None


def _safe_json_loads(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        cleaned = text
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        if cleaned:
            return json.loads(cleaned)
    except Exception:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
    except Exception:
        pass

    return {}


def _build_fallback_summary(skin_profile: Dict[str, Any], analysis_result: Dict[str, Any], products: List[Dict[str, Any]]) -> str:
    skin_type = str(skin_profile.get("skin_type") or analysis_result.get("skin_type") or "normal").upper()
    concerns = ", ".join(str(item) for item in (analysis_result.get("concerns") or skin_profile.get("concerns") or ["acne"]))
    top_product = products[0]["product_name"] if products else "기본 보습 케어 제품"
    return (
        f"{skin_type} 피부 기준으로 {concerns} 고민을 우선적으로 관리하는 방향으로 설계했습니다. "
        f"주요 점수는 전체 {analysis_result.get('total_score', 0)}점이며, "
        f"추천 제품은 {top_product}을 우선 고려할 수 있습니다."
    )


def _call_openai_json(prompt: str) -> Optional[Dict[str, Any]]:
    api_key = _get_env_value("OPENAI_API_KEY", "OPENAI_KEY", "OpenAI")
    if not api_key:
        return None

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        model = _get_env_value("OPENAI_MODEL", "MODEL") or "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 피부 관리 코치입니다. JSON만 반환하세요. 한국어로 답하세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        content = response.choices[0].message.content or "{}"
        parsed = _safe_json_loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def _call_claude_json(prompt: str) -> Optional[Dict[str, Any]]:
    api_key = _get_env_value("ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "Claude")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            temperature=0.3,
            system="당신은 피부 관리 코치입니다. JSON만 반환하세요. 한국어로 답하세요.",
            messages=[{"role": "user", "content": prompt}],
        )
        content = "".join(block.text for block in message.content if getattr(block, "type", None) == "text")
        parsed = _safe_json_loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def generate_llm_report(
    skin_profile: Dict[str, Any],
    analysis_result: Dict[str, Any],
    products: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prompt = (
        "당신은 피부과 전문 테라피스트입니다. "
        "아래 사용자의 피부 상태를 바탕으로 3개의 핵심 포인트를 한국어 JSON으로 작성하세요. "
        "절대 과장된 의료 진단을 하지 마세요.\n"
        f"- 피부 타입: {skin_profile.get('skin_type') or analysis_result.get('skin_type')}\n"
        f"- 고민: {analysis_result.get('concerns') or skin_profile.get('concerns')}\n"
        f"- 피부 점수: {analysis_result.get('scores')}\n"
        f"- 추천 제품: {[p.get('product_name') for p in products[:3]]}\n"
        "반드시 다음 키를 포함하세요: summary, key_points, caution."
    )

    parsed: Optional[Dict[str, Any]] = _call_openai_json(prompt)
    provider = "openai"
    if not parsed:
        parsed = _call_claude_json(prompt)
        provider = "claude"

    if not parsed:
        return {
            "provider": "local",
            "summary": _build_fallback_summary(skin_profile, analysis_result, products),
            "key_points": ["수분 유지", "여드름 관리", "민감성 보호"],
            "caution": "민감성 피부는 성분 테스트 후 사용해 주세요.",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    return {
        "provider": provider,
        "summary": parsed.get("summary") or _build_fallback_summary(skin_profile, analysis_result, products),
        "key_points": parsed.get("key_points") or ["세정 강화", "진정 관리", "보습 유지"],
        "caution": parsed.get("caution") or "민감한 부위는 테스트 후 사용을 권장합니다.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
                                                