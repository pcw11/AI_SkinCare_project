# MirrorMe API Interface Specification

## Overview

이 인터페이스는 이미지 기반 피부 진단, 제품 추천, LLM 설명을 하나의 통합 응답으로 묶어 전달하는 표준 계약입니다.

## Request / Response Contract

### 1) GET /health

```http
GET /health
```

Response:

```json
{
  "success": true,
  "status": "ok",
  "service": "ai-skincare-backend"
}
```

### 2) POST /analyze-skin

Request format (multipart/form-data):

```http
POST /analyze-skin
Content-Type: multipart/form-data
```

Form fields:
- `user_id`: 사용자 ID (string)
- `image`: 업로드 이미지 파일 (jpg/png)

Example:

```bash
curl -X POST "http://127.0.0.1:8000/analyze-skin" \
  -F "user_id=test-user" \
  -F "image=@/path/to/face.jpg"
```

Verified response shape:

```json
{
  "success": true,
  "user_id": "test-user",
  "total_score": 73,
  "scores": {
    "acne": 0,
    "pigmentation": 2,
    "pore": 48,
    "sebum": 58
  },
  "raw_values": {
    "acne_count": 0,
    "pigmentation_count": 5,
    "pore_variance": 13.0054,
    "sebum_ratio": 35.3
  }
}
```

### 3) Full integrated response (with recommendations + LLM report)

```json
{
  "success": true,
  "interface_version": "1.0",
  "analysis_id": "analysis_20261016_001",
  "user_id": "demo-user",
  "skin_type": "oily",
  "total_score": 82,
  "scores": {
    "acne": 73,
    "pigmentation": 65,
    "pore": 80,
    "sebum": 90
  },
  "raw_values": {
    "acne_count": 12,
    "pigmentation_count": 8,
    "pore_variance": 38.4,
    "sebum_ratio": 54.2
  },
  "concerns": ["acne", "sebum"],
  "products": [
    {
      "product_id": "P1001",
      "brand": "Round Lab",
      "product_name": "1025 Dokdo Cleanser",
      "product_type": "cleanser",
      "match_score": 85.0,
      "reason": "여드름 관리와 피지 조절에 적합"
    }
  ],
  "llm_report": {
    "provider": "openai",
    "summary": "여드름 및 피지 관리에 집중하는 루틴을 권장합니다.",
    "key_points": ["수분 유지", "여드름 관리", "민감성 보호"],
    "caution": "민감성 피부는 성분 테스트 후 사용해 주세요.",
    "generated_at": "2026-10-16T12:00:00+00:00"
  },
  "generated_at": "2026-10-16T12:00:00+00:00"
}
```

## Field Definition

- success: 요청 처리 성공 여부
- interface_version: 응답 스키마 버전
- analysis_id: 내부 분석 식별자
- user_id: 사용자 ID
- skin_type: oily / dry / combination / normal / sensitive
- total_score: 종합 점수 (0~100)
- scores: 각 항목 점수
- raw_values: 원시 수치값
- concerns: 이상 징후 목록
- products: 추천 상품 목록
- llm_report: LLM 생성 요약 결과
- generated_at: 응답 생성 시각 (UTC ISO-8601)

## Operational Notes

- API 키는 `.env`의 `OPENAI_API_KEY`로 관리
- 키가 없으면 로컬 fallback 방식으로 동작
- 프로덕션 배포 시에는 HTTPS, 서버 환경 변수, 고정 DB 경로로 전환
