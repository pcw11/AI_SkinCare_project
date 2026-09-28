## 📄 파일 구성 및 설명

| 파일명 | 파일 구분 | 설명 |
| :--- | :---: | :--- |
| **`oliveyoung_crawler.py`** | `Python Script` | **반자동 올리브영 수집 스크립트**<br>- Selenium 및 단축키(F3/F4)를 이용해 상품 상세 정보(브랜드, 가격, 용량, 고시정보, 전성분 등)를 크롤링하여 `skincare_ product_rawdata.xlsx`로 실시간 누적 저장 |
| **`skincare_ product_rawdata.xlsx`** | `Dataset (Excel)` | **크롤러가 1차 수집한 원본 데이터셋**<br>- 가공되지 않은 상품별 메타데이터, 원본 전성분 텍스트, 수집 URL 및 타임스탬프가 단일 테이블 형태로 보관 |
| **`export_to_mirrorme.py`** | `Python Script` | **데이터 전처리 및 정규화(ETL) 스크립트**<br>- `skincare_ product_rawdata.xlsx`를 읽어 성분명 내 노이즈 및 불용어를 정제하고, RDBMS 연동이 가능하도록 4개 시트로 분리하여 `skincare_ product_data.xlsx` 생성 |
| **`skincare_ product_data.xlsx`** | `Dataset (Excel)` | **최종 정규화 데이터셋 (Final Blueprint)**<br>- `Products` (상품 정보)<br>- `Ingredients` (정제된 고유 성분 사전)<br>- `Product_Ingredients` (상품-성분 매핑 관계 및 순서)<br>- `Data_Dictionary` (테이블/컬럼 명세서) |

---

## 🔄 데이터 흐름 (Workflow)

```
[올리브영 웹페이지]
       │
       ▼  (oliveyoung_crawler.py)
[skincare_ product_rawdata.xlsx]  (수집 원본 데이터)
       │
       ▼  (export_to_mirrorme.py)
[skincare_ product_data.xlsx]  (정규화 및 RDB 대응 최종본)
```