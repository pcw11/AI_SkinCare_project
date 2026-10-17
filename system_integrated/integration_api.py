import json
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request

try:
    from .system_integration import process_uploaded_image
except ImportError:  # pragma: no cover
    from system_integration import process_uploaded_image


def _coerce_skin_profile(raw_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if raw_profile is None:
        return {}
    if isinstance(raw_profile, str):
        try:
            raw_profile = json.loads(raw_profile)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw_profile, dict):
        return {}
    return {key: value for key, value in raw_profile.items() if value not in (None, "")}


def create_integration_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health_check():
        return jsonify({
            "success": True,
            "status": "ok",
            "service": "ai-skincare-system-integrated",
            "interface_version": "1.0",
        }), 200

    @app.post("/api/v1/analyze")
    def analyze_skin():
        payload = request.get_json(silent=True) or {}
        form_data = request.form.to_dict()

        user_id = payload.get("user_id") or form_data.get("user_id") or "demo-user"
        skin_profile = _coerce_skin_profile(payload.get("skin_profile") or form_data.get("skin_profile"))

        for key in ["skin_type", "concerns", "allergy_ingredients", "preferred_formulations", "age"]:
            if key in payload:
                skin_profile[key] = payload[key]
            elif key in form_data and form_data[key] not in (None, ""):
                value = form_data[key]
                if key in {"concerns", "allergy_ingredients", "preferred_formulations"}:
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = [item.strip() for item in str(value).split(",") if item.strip()]
                skin_profile[key] = value

        image_file = request.files.get("image") or request.files.get("file")
        if image_file is None:
            return jsonify({"success": False, "message": "이미지 파일이 필요합니다."}), 400

        try:
            result = process_uploaded_image(
                image_file,
                user_id=user_id,
                skin_profile=skin_profile,
            )
            return jsonify(result), 200
        except Exception as exc:  # pragma: no cover
            return jsonify({"success": False, "message": str(exc)}), 500

    return app


app = create_integration_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
