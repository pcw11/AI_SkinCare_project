import os
import re
import pandas as pd

# 경로 설정 및 입력 파일 확인
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
input_file = os.path.join(desktop_path, "skincare_ product_rawdata.xlsx")
output_file = os.path.join(desktop_path, "skincare_ product_data.xlsx")

if not os.path.exists(input_file):
    print(f"[에러] 파일 누락: {input_file}")
    exit()

df_raw = pd.read_excel(input_file)
print(f"[로드 완료] 원본: {len(df_raw)}건\n")

# Products 테이블 구성
df_products = pd.DataFrame()
df_products["product_id"] = (
    df_raw["product_id"]
    if "product_id" in df_raw.columns
    else [f"P{i+1:04d}" for i in range(len(df_raw))]
)
df_products["brand"] = df_raw["brand"]
df_products["product_name"] = df_raw["product_name"]
df_products["product_type"] = df_raw["product_type"]
df_products["ingredients_raw"] = df_raw.get("ingredients_raw", "")
df_products["source_url"] = df_raw.get("source_url", "")
df_products["capacity"] = df_raw.get("capacity", "")
df_products["collected_at"] = df_raw.get("collected_at", "")
df_products["verification_status"] = "verified"

if "price" in df_raw.columns:
    df_products["notes"] = df_raw["price"].apply(
        lambda x: f"{int(x):,}원" if pd.notnull(x) and str(x).isdigit() else ""
    )
else:
    df_products["notes"] = ""


# 성분 정제 파서
def parse_ingredients(raw_text):
    if not isinstance(raw_text, str) or not raw_text.strip():
        return []

    text = raw_text.replace("\r", " ")

    # 안내 문구 및 고객센터 관련 텍스트 제거
    text = re.split(
        r"제공된\s*성분은|※|닥터자르트\s*고객|고객관리지원팀|고객센터", text
    )[0]

    # 맨 앞 영문 상품 코드/이름 제거
    text = re.sub(r"^[A-Z0-9\s\-]+(?=[가-힣])", "", text.strip())

    # 구분자 통일
    text = text.replace("[]", ",").replace("@", ",").replace("\n", ",")

    # 괄호 내 쉼표 보호
    def protect_parens(m):
        return m.group(0).replace(",", "__PCOMMA__")

    text = re.sub(r"\([^)]*\)", protect_parens, text)
    text = re.sub(r"\[[^\]]*\]", protect_parens, text)

    # 숫자 사이 쉼표 보호 (예: 1,2-헥산다이올)
    text = re.sub(r"(?<=\d),(?=\d)", "__NCOMMA__", text)

    # 분리 및 토큰화
    if "," in text:
        tokens = [t.strip() for t in text.split(",") if t.strip()]
    else:
        tokens = [t.strip() for t in text.split() if t.strip()]

    cleaned_list = []
    stop_words = {
        "제공된",
        "성분은",
        "동일",
        "제품이라도",
        "경우에",
        "따라",
        "변경될",
        "수",
        "있습니다",
        "최신정보는",
        "제품",
        "포장의",
        "성분을",
        "참고하시거나",
        "본사",
        "연락",
        "부탁",
        "드립니다",
    }

    for token in tokens:
        token = token.replace("__PCOMMA__", ",").replace("__NCOMMA__", ",")

        # 괄호 및 함량 표기 제거
        clean_name = re.sub(r"\[.*?\]|\(.*?\)", "", token)
        clean_name = re.sub(
            r"\*|\d+(\.\d+)?%|\d{1,3}(,\d{3})*\s*ppm", "", clean_name
        )
        clean_name = clean_name.strip(" .*-~_\"'#")

        if not clean_name or clean_name in stop_words or clean_name.isdigit():
            continue

        cleaned_list.append(clean_name)

    return cleaned_list


# Ingredients 및 관계 테이블 매핑
ingredients_dict = {}
product_ingredients_records = []
ing_counter = 1

for idx, row in df_products.iterrows():
    p_id = row["product_id"]
    raw_text = str(row["ingredients_raw"])

    items = parse_ingredients(raw_text)

    for order, clean_name in enumerate(items, start=1):
        if clean_name not in ingredients_dict:
            ing_id = f"I{ing_counter:04d}"
            ingredients_dict[clean_name] = ing_id
            ing_counter += 1
        else:
            ing_id = ingredients_dict[clean_name]

        product_ingredients_records.append(
            {
                "product_id": p_id,
                "ingredient_id": ing_id,
                "ingredient_order": order,
            }
        )

df_ingredients = pd.DataFrame(
    [
        {
            "ingredient_id": v,
            "ingredient_name": k,
            "inci_name": "",
            "source_url": "올리브영 전성분 고시",
        }
        for k, v in ingredients_dict.items()
    ]
)

df_prod_ing = pd.DataFrame(product_ingredients_records)

# Data_Dictionary 시트 정의
data_dict = [
    {
        "table_name": "Products",
        "column_name": "product_id",
        "data_type": "TEXT",
        "description": "제품 ID",
        "example": "P0001",
    },
    {
        "table_name": "Products",
        "column_name": "brand",
        "data_type": "TEXT",
        "description": "브랜드명",
        "example": "A브랜드",
    },
    {
        "table_name": "Products",
        "column_name": "product_name",
        "data_type": "TEXT",
        "description": "제품명",
        "example": "수분 크림",
    },
    {
        "table_name": "Products",
        "column_name": "product_type",
        "data_type": "TEXT",
        "description": "제품 유형",
        "example": "크림",
    },
    {
        "table_name": "Products",
        "column_name": "ingredients_raw",
        "data_type": "TEXT",
        "description": "원본 전성분",
        "example": "정제수, 글리세린",
    },
    {
        "table_name": "Products",
        "column_name": "source_url",
        "data_type": "TEXT",
        "description": "출처 URL",
        "example": "공식 홈페이지 주소",
    },
    {
        "table_name": "Products",
        "column_name": "capacity",
        "data_type": "TEXT",
        "description": "용량",
        "example": "50ml",
    },
    {
        "table_name": "Products",
        "column_name": "collected_at",
        "data_type": "DATE",
        "description": "수집일시",
        "example": "2026-09-17 00:00:00",
    },
    {
        "table_name": "Products",
        "column_name": "verification_status",
        "data_type": "TEXT",
        "description": "검증 상태",
        "example": "verified",
    },
    {
        "table_name": "Products",
        "column_name": "notes",
        "data_type": "TEXT",
        "description": "비고",
        "example": "공식 홈페이지 확인",
    },
    {
        "table_name": "Ingredients",
        "column_name": "ingredient_id",
        "data_type": "TEXT",
        "description": "성분 ID",
        "example": "I0001",
    },
    {
        "table_name": "Ingredients",
        "column_name": "ingredient_name",
        "data_type": "TEXT",
        "description": "한글 성분명",
        "example": "글리세린",
    },
    {
        "table_name": "Ingredients",
        "column_name": "inci_name",
        "data_type": "TEXT",
        "description": "INCI명",
        "example": "Glycerin",
    },
    {
        "table_name": "Ingredients",
        "column_name": "source_url",
        "data_type": "TEXT",
        "description": "출처 URL",
        "example": "공식 자료 주소",
    },
    {
        "table_name": "Product_Ingredients",
        "column_name": "product_id",
        "data_type": "TEXT",
        "description": "제품 ID",
        "example": "P0001",
    },
    {
        "table_name": "Product_Ingredients",
        "column_name": "ingredient_id",
        "data_type": "TEXT",
        "description": "성분 ID",
        "example": "I0001",
    },
    {
        "table_name": "Product_Ingredients",
        "column_name": "ingredient_order",
        "data_type": "INTEGER",
        "description": "성분 표시 순서",
        "example": 1,
    },
]
df_dictionary = pd.DataFrame(data_dict)

# 엑셀 파일 저장
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_products.to_excel(writer, sheet_name="Products", index=False)
    df_ingredients.to_excel(writer, sheet_name="Ingredients", index=False)
    df_prod_ing.to_excel(writer, sheet_name="Product_Ingredients", index=False)
    df_dictionary.to_excel(writer, sheet_name="Data_Dictionary", index=False)

print(f"[저장 완료] {output_file}")
print(f"- 정제된 고유 성분: {len(df_ingredients)}건")