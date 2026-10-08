# 시스템 통합 가이드

이 문서는 현재 프로젝트의 구조를 유지한 채, 통합 포인트를 추가하는 방법을 설명합니다.

## 목표
- 기존 파일을 크게 수정하지 않는다.
- 앱 → 백엔드 → AI → DB 흐름을 안전하게 연결한다.
- 각 모듈의 역할을 유지하면서 통합만 추가한다.

## 현재 구조 기준 연결 방식

- 앱: frontend/
- 백엔드: backend/test.py
- AI 분석: algorithm/test.py
- 통합 계층: system_integrated/system_integration.py
- 추천 데이터: dataset/skincare_products_data/

## 추가된 통합 모듈
- system_integrated/system_integration.py

이 파일은 다음 역할을 수행합니다.

1. AI 분석 모듈 로드
2. 기존 AI 함수 재사용
3. 표준 JSON 응답 구조로 변환
4. SQLite 저장
5. 전체 분석 흐름 실행

## 실행 예시

다른 컴퓨터에서도 동작하도록, 로컬 절대 경로를 사용하지 않고 프로젝트 루트 기준으로 실행하는 예시입니다.

### 1) 프로젝트 루트에서 실행

```bash
cd 프로젝트_루트
python system_integrated/system_integration.py --image dataset/acne_front_samples/images/H0_17717_P2_L0.png --user-id demo-user
```

### 2) 다른 이미지 파일로 테스트

```bash
cd 프로젝트_루트
python system_integrated/system_integration.py --image dataset/acne_front_samples/images/H0_205877_P10_L1.png --user-id test-user
```

### 3) PowerShell에서 실행

```powershell
cd 프로젝트_루트
python .\system_integrated\system_integration.py --image .\dataset\acne_front_samples\images\H0_17717_P2_L0.png --user-id demo-user
```

주의:
- `프로젝트_루트`는 이 저장소의 루트 폴더를 의미한다.
- 절대 경로(`C:\...`)를 사용하지 않는다.
- `--image` 경로는 프로젝트 안의 상대 경로로 적어야 한다.
- 현재 구현은 파일 경로를 읽어 AI 분석을 수행하고 결과를 SQLite에 저장한다.
- 추후 배포 단계에서는 이 로컬 경로를 서버 경로로 교체해야 한다.

## 테스트 절차

1. 프로젝트 루트로 이동한다.
2. 파일 경로를 프로젝트 내부 상대 경로로 작성한다.
3. `--user-id`를 지정한다.
4. 명령을 실행한다.
5. JSON 응답이 출력되면 통합 흐름이 정상 동작하는 것으로 확인한다.

```bash
cd 프로젝트_루트
python system_integrated/system_integration.py --image dataset/acne_front_samples/images/H0_17717_P2_L0.png --user-id demo-user
```

## 필요 패키지

다른 컴퓨터에서 직접 실행하려면 최소한 다음 패키지가 설치되어야 한다.

```bash
pip install flask opencv-python numpy matplotlib
```

이 조건을 만족하면 로컬 컴퓨터 전용 경로 없이도 프로젝트 루트 기준으로 실행할 수 있는 형태가 된다.

## 응답 예시

```json
{
  "success": true,
  "user_id": "demo-user",
  "total_score": 78,
  "scores": {
    "acne": 72,
    "pigmentation": 60,
    "pore": 70,
    "sebum": 55
  },
  "raw_values": {
    "acne_count": 12,
    "pigmentation_count": 20,
    "pore_variance": 31.2,
    "sebum_ratio": 44.1
  },
  "skin_type": "oily"
}
```

## 통합 포인트

- 앱은 백엔드 API만 호출
- 백엔드는 system_integration.py를 통해 AI와 DB를 연결
- AI는 기존 algorithm/test.py의 함수 재사용
- DB는 기존 backend/test.py 구조와 호환

## 주의사항

- 기존 코드 수정 없이 추가 파일만 사용한다.
- 실제 서비스에서는 앱이 10.0.2.2:5000 또는 실제 서버 IP를 통해 backend/test.py를 호출한다.
- 추천 기능은 이후 단계에서 제품 데이터와 연결하면 된다.

## 현재 상태 점검표

| 항목 | 상태 | 비고 |
|---|---|---|
| 기존 구조 유지 | 완료 | backend/test.py, algorithm/test.py, dataset 유지 |
| 통합 계층 추가 | 완료 | system_integrated/system_integration.py 추가 |
| AI와 백엔드 연결 | 완료 | 통합 모듈이 AI 로직 호출 및 결과 반환 |
| DB 저장 연결 | 완료 | SQLite 저장 확인 |
| API 응답 검증 | 완료 | /analyze-skin, /history, /signup, /login, /profile 응답 확인 |
| 실제 서비스 배포 | 미완료 | 로컬 개발 서버 상태 |
| 외부 네트워크 접속 | 미완료 | 공인 IP/포트포워딩/배포 서버 필요 |
| HTTPS 적용 | 미완료 | 실제 운영 환경에서 필요 |
| 학교/다른 네트워크 확인 | 미완료 | 로컬 네트워크 또는 배포 서버 필요 |

## 최종 판단

| 구분 | 상태 |
|---|---|
| 기능 통합 | 완료 |
| 실서비스 배포 | 미완료 |
| 외부 접근 가능 여부 | 미완료 |
| HTTPS 적용 | 미완료 |

현재 상태는 기능 통합은 동작하지만, 실제 외부 서비스 운영 단계는 아직 남아 있습니다.
