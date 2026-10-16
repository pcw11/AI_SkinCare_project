# 시스템 통합 가이드

이 문서는 현재 프로젝트의 실제 구조와 통합 흐름을 기준으로 정리한 문서입니다.  
핵심 목표는 앱 → 백엔드 → AI 분석 → 제품 추천 → LLM 요약 → DB 저장까지 한 번에 연결하는 것입니다.


---

## 2. 역할 분리

### 2.1 algorithm/test.py
- 기존 피부 분석 로직을 담당합니다.
- 얼굴 ROI 추출, 전처리, 여드름/색소침착/모공/피지 분석, 점수 정규화, 피부 타입 판별이 포함됩니다.
- system_integrated/system_integration.py에서 이 모듈을 호출해 재사용합니다.

### 2.2 backend/test.py
- Flask 서버 역할을 합니다.
- 사용자 계정, 프로필, 히스토리, 분석 API를 관리합니다.
- 주요 엔드포인트:
  - GET /health
  - POST /llm-test
  - POST /analyze-skin
  - GET /history/<user_id>
  - POST /signup
  - POST /login
  - GET/PUT /users/<user_id>/profile

### 2.3 system_integrated/system_integration.py
- 실제 통합 계층입니다.
- AI 분석 결과를 표준 응답 구조로 묶고, 추천 제품과 LLM 리포트를 조합합니다.
- SQLite 저장까지 수행합니다.

### 2.4 system_integrated/llm_service.py
- OpenAI 또는 Claude를 사용해 피부 분석 리포트를 생성합니다.
- API 키가 없으면 로컬 fallback 응답을 반환합니다.
- JSON 마크다운 포맷 (` ```json ... ``` `)도 파싱하도록 처리합니다.

### 2.5 system_integrated/product_recommender.py
- 분석 결과와 사용자 프로필에 맞는 화장품을 추천합니다.
- 매치 점수와 추천 이유를 계산하여 리스트 형태로 반환합니다.

### 2.6 .env / .env.example
- 실제 API 키와 앱 설정을 담는 파일입니다.
- 예시 키 이름:
  - OPENAI_API_KEY
  - OpenAI
  - OPENAI_MODEL
  - ANTHROPIC_API_KEY
  - Claude
  - APP_ENV
  - APP_HOST
  - APP_PORT

---

## 3. 통합 실행 흐름

현재 구조는 아래 순서로 동작합니다.

```text
클라이언트 / 앱
    ↓
POST /analyze-skin
    ↓
backend/test.py
    ↓
system_integrated.system_integration.integrate_analysis()
    ↓
1) run_ai_analysis()
2) recommend_products()
3) generate_llm_report()
4) save_analysis_result()
    ↓
표준 JSON 응답 반환
```

### 실제 응답 구조

```json
{
  "success": true,
  "user_id": "test-user",
  "total_score": 73,
  "grade": "B",
  "skin_type": "oily",
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

추가로 다음 값도 포함될 수 있습니다.

- `products`
- `llm_report`
- `concerns`
- `interface_version`
- `analysis_id`

---

## 4. API 명세

### 4.1 GET /health

```http
GET /health
```

응답 예시:

```json
{
  "success": true,
  "status": "ok",
  "database": "sqlite"
}
```

### 4.2 POST /llm-test

LLM이 실제로 동작하는지 검증하는 테스트용 API입니다.

요청 예시:

```json
{
  "skin_profile": {
    "skin_type": "oily",
    "concerns": ["acne", "sebum"]
  },
  "analysis_result": {
    "skin_type": "oily",
    "scores": {
      "acne": 75,
      "pigmentation": 60,
      "pore": 78,
      "sebum": 88
    },
    "concerns": ["acne", "sebum"],
    "total_score": 80
  },
  "products": [
    {
      "product_id": "P1001",
      "product_name": "1025 Dokdo Cleanser",
      "brand": "Round Lab",
      "product_type": "cleanser"
    }
  ]
}
```

응답 예시:

```json
{
  "success": true,
  "llm_report": {
    "provider": "openai",
    "summary": "...",
    "key_points": ["..."],
    "caution": "..."
  }
}
```

### 4.3 POST /analyze-skin

실제 분석 API입니다.

요청 형식:

```http
Content-Type: multipart/form-data
key: image
```

추가 파라미터:

- user_id
- image_url (선택)
- skin_profile (선택)

응답 예시:

```json
{
  "success": true,
  "user_id": "test-user",
  "total_score": 73,
  "grade": "B",
  "skin_type": "oily",
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

---

## 5. 실행 방법

### 5.1 의존성 설치

```bash
pip install flask opencv-python numpy matplotlib ultralytics python-dotenv openai anthropic
```

필요한 최소 패키지 목록은 다음과 같습니다.

```bash
pip install flask opencv-python numpy matplotlib ultralytics python-dotenv
```

### 5.2 환경 변수 설정

```bash
cp .env.example .env
```

그 다음 `.env` 파일을 본인의 실제 키로 채웁니다.

```env
OPENAI_API_KEY=your_openai_api_key_here
OpenAI=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=your_claude_api_key_here
Claude=your_claude_api_key_here
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 5.3 서버 실행

권장 실행 방법:

```bash
python run_backend.py
```

---

## 6. 실제 검증 상태(현재 기준)

아래 항목은 현재 코드와 실제 실행 환경에서 확인된 상태입니다.

### 6.1 완료된 항목
- OpenAI 실제 키 연동 확인
  - [system_integrated/llm_service.py](llm_service.py)에서 실제 OPENAI_API_KEY를 로드하고 실 호출이 동작함
  - 실제 검증 결과: provider = openai, summary/key_points/caution가 정상 생성됨
- Flask 서버 실제 구동 확인
  - GET /, /health, /llm-test 모두 200 응답 확인
- 이미지 분석 API 실제 검증 완료
  - 실제 데이터셋 이미지 업로드로 POST /analyze-skin 호출 성공
  - 응답 예시: success = true, total_score = 80, user_id = test-user
- 통합 테스트 통과
  - [system_integrated/test_system_integration.py](test_system_integration.py)에서 4개 테스트 OK
- PostgreSQL 실제 연결 및 마이그레이션 검증 완료
  - PostgreSQL 서버를 기동한 뒤 SQLite → PostgreSQL 이관이 성공
  - 최종 확인: users = 1, analyses = 12

### 6.2 아직 완결되지 않은 항목
- 안드로이드 앱 실기기 E2E 시연
  - 서버/AI 로직은 검증되었지만, 실제 앱 촬영 → 업로드 → 렌더링까지의 디바이스 시연은 미완료
- 제품 적합성 판별 로직의 실제 추천 정확도 검증
  - 구조와 연결은 가능하지만, 사용자 알레르기/성분 대조까지 포함한 최종 맞춤 추천 성능은 추가 검증 필요
- 인터페이스 계약 최종 확정
  - 서버의 입력 파라미터와 출력 JSON 구조는 확인되었지만, 안드로이드 앱 측 요구사항과 완전 조율이 남음
- 프로덕션 운영 환경 정리
  - 백엔드와 DB 연결은 확인되었지만, 최종 운영 배포/배포 확인 절차는 남아 있음

### 6.3 현재 결론
이 프로젝트는 지금 기준으로 "백엔드 핵심 기능이 실제로 동작하는 상태"입니다. 즉,
- LLM 호출 가능
- 분석 API 동작
- DB 저장/이관 가능
- 테스트 통과

까지는 확인된 상태입니다. 다만,
- 앱 실기기 연동
- 제품 추천 정확도 검증
- 최종 인터페이스 명세 확정
- 운영 배포 준비

는 아직 마무리 단계로 남아 있습니다.

이 문서는 '기능 구현 완료'가 아닌 '실제 검증된 상태' 기준으로 정리된 문서이며, 지금까지 확인된 구현과 남은 작업을 구분해서 기록한 것입니다.

또는 backend 파일을 직접 실행할 수 있습니다.

```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 5.4 Python 버전 권장

- 추천: Python 3.10
- 이유: 일부 환경에서 Mediapipe 또는 라이브러리 호환성 문제가 발생할 수 있음
- 3.11 이상은 필요 시 추가 검증이 필요함

---

## 6. YOLO 모델 처리 방식

- 예상 경로: `models/acne_yolo.pt`
- 이 파일이 있으면 YOLO 기반으로 추가 분석을 시도할 수 있습니다.
- 파일이 없으면 현재 구조는 HSV 기반 자동 대체 로직으로 동작합니다.

즉, YOLO가 없어도 기본 AI 분석 기능은 유지됩니다.

---

## 7. Windows 경로 이슈 대응

Windows에서 한글 경로를 포함한 파일을 처리할 때 OpenCV가 경로를 읽지 못하는 문제가 발생할 수 있습니다.  
현재 구조는 다음 방식으로 보완합니다.

- `cv2.imread()` 시도
- 실패 시 `np.frombuffer` 기반 재시도
- 그래도 실패하면 PIL fallback

이 방식으로 경로 인코딩 문제를 완화합니다.

---

## 8. 현재 검증 상태

다음 항목은 실제로 확인된 상태입니다.

- AI 분석 로직 동작 확인
- 백엔드 API /health, /llm-test, /analyze-skin 정상 응답 확인
- LLM live 호출 확인 (`provider: "openai"`)
- 이미지 업로드 기반 분석 성공 확인
- Windows 한글 경로 처리 보완 완료

현재 통합 흐름은 로컬 개발 환경 기준으로 정상 동작 상태입니다.

---

## 9. 최종 판단
