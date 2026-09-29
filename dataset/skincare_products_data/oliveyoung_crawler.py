import os
import random
import re
import time
import tkinter as tk
from bs4 import BeautifulSoup
import keyboard
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 저장 경로 및 카운트 초기화
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
EXCEL_FILE = os.path.join(desktop_path, "skincare_product_rawdata.xlsx")
if os.path.exists(EXCEL_FILE):
    try:
        prev_df = pd.read_excel(EXCEL_FILE)
        captured_count = len(prev_df)
        print(f"\n[기존 데이터] {captured_count}건 로드 완료 (다음: P{captured_count + 1:04d})\n")
    except Exception as e:
        print(f"[오류] 파일 읽기 실패 (엑셀 종료 확인 필요): {e}")
        captured_count = 0
else:
    captured_count = 0

# 브라우저 세팅 (봇 감지 우회)
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
)

driver.maximize_window()
driver.get("https://www.oliveyoung.co.kr/")


def show_toast(title, message, duration=1200, bg_color="#1e1e1e", fg_color="#00e676"):
    root = tk.Tk()
    root.title(title)
    root.attributes("-topmost", True)
    root.overrideredirect(True)

    frame = tk.Frame(root, bg=bg_color, bd=2, relief="solid", highlightthickness=0)
    frame.pack(fill="both", expand=True)

    header_lbl = tk.Label(
        frame,
        text=f"✔ {title}",
        font=("맑은 고딕", 11, "bold"),
        fg=fg_color,
        bg=bg_color,
    )
    header_lbl.pack(anchor="w", padx=15, pady=(10, 2))

    body_lbl = tk.Label(
        frame,
        text=message,
        font=("맑은 고딕", 9),
        fg="#ffffff",
        bg=bg_color,
        justify="left",
    )
    body_lbl.pack(anchor="w", padx=15, pady=(0, 10))

    root.update_idletasks()
    width = max(340, body_lbl.winfo_reqwidth() + 40)
    height = body_lbl.winfo_reqheight() + 40
    x = root.winfo_screenwidth() - width - 30
    y = 50
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.after(duration, root.destroy)
    root.mainloop()


def go_back_page():
    try:
        driver.back()
        show_toast("뒤로가기", "이전 화면 이동", 800)
    except Exception as e:
        print(f"뒤로가기 에러: {e}")


def scroll_to_notice_info():
    try:
        driver.execute_script("""
            let target = document.querySelector("#buyInfo, a[name='buyInfo'], .prd_detail_info, table.cpt_table");
            if(target) {
                target.scrollIntoView({behavior: 'smooth', block: 'center'});
            } else {
                let targetY = document.body.scrollHeight * 0.76;
                window.scrollTo({top: targetY, behavior: 'smooth'});
            }
            setTimeout(() => {
                let buyTab = document.querySelector("#buyInfo, a[name='buyInfo'], #tabBuyInfo");
                if(buyTab) buyTab.click();
            }, 300);
        """)
        show_toast("화면 이동", "고시정보 포커스", 800)
    except Exception as e:
        print(f"스크롤 이동 에러: {e}")


def get_real_price():
    # 팝업 레이어 및 내부 변수 확인
    try:
        js_price = driver.execute_script("""
            let popups = document.querySelectorAll(".layer_pop, .pop_layer, [class*='benefit'], [class*='layer'], .ly_box, div[style*='block']");
            for (let pop of popups) {
                if (pop.innerText && pop.innerText.includes("판매가")) {
                    let match = pop.innerText.match(/판매가[^\d]*?([\d,]+)\s*원/);
                    if (match) return match[1].replace(/,/g, '');
                }
            }
            if (window.goodsDetail && window.goodsDetail.custPrc) return String(window.goodsDetail.custPrc);
            if (window.goodsInfo && window.goodsInfo.normPrc) return String(window.goodsInfo.normPrc);
            return null;
        """)
        if js_price and str(js_price).isdigit():
            val = int(js_price)
            if 1000 <= val <= 1500000:
                return str(val)
    except Exception:
        pass

    # 본문 텍스트 정규식
    try:
        body_text = driver.find_element("tag name", "body").text
        sale_match = re.search(r"판매가[^\d\n]*?([\d,]{4,7})\s*원", body_text)
        if sale_match:
            val = int(sale_match.group(1).replace(",", ""))
            if 1000 <= val <= 1500000:
                return str(val)
    except Exception:
        pass

    # HTML 태그 fallback
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for sel in ["span.price-1 strike", ".price-1 strike", "strike", ".price-1"]:
        pel = soup.select_one(sel)
        if pel:
            m = re.search(r"([\d,]{4,7})\s*원", pel.text)
            if m:
                val = int(m.group(1).replace(",", ""))
                if 1000 <= val <= 1500000:
                    return str(val)

    for sel in ["span.price-2 strong", ".price-2 strong", ".price strong", "#total_price"]:
        pel = soup.select_one(sel)
        if pel:
            m = re.search(r"([\d,]{4,7})\s*원", pel.text)
            if m:
                val = int(m.group(1).replace(",", ""))
                if 1000 <= val <= 1500000:
                    return str(val)

    return "0"


def capture_current_page():
    global captured_count
    current_url = driver.current_url

    if "getGoodsDetail" not in current_url and "goodsNo=" not in current_url.lower():
        show_toast("안내", "상품 상세 페이지 진입 필요", 1500)
        return
    print("\n[추출 시작]")

    # 고시정보 아코디언 오픈
    already_open = "모든 성분" in driver.page_source or "전성분" in driver.page_source
    if not already_open:
        driver.execute_script("""
            let elements = Array.from(document.querySelectorAll("button, a, dt, div, p, span, h3, h4"));
            let target = elements.find(el => el.innerText && el.innerText.trim().startsWith("상품정보 제공고시"));
            if(target) {
                target.scrollIntoView({behavior: 'instant', block: 'center'});
                target.click();
            }
        """)
        time.sleep(1.0)

    soup_table = BeautifulSoup(driver.page_source, "html.parser")

    capacity = ""
    skin_type = ""
    expiry_date = ""
    how_to_use = ""
    country = ""
    ingredients_raw = ""
    contact_phone = ""

    # 고시정보 파싱
    for tr in soup_table.find_all("tr"):
        th = tr.find(["th", "dt"])
        td = tr.find(["td", "dd"])
        if not th or not td:
            continue

        header = th.get_text(strip=True)
        content = td.get_text(separator=" ", strip=True)

        if ("용량" in header or "중량" in header) and not capacity:
            capacity = content
        elif "주요 사양" in header and not skin_type:
            skin_type = content
        elif "사용기한" in header or "사용기간" in header:
            if not expiry_date:
                expiry_date = content
        elif "사용방법" in header and not how_to_use:
            how_to_use = content
        elif "제조국" in header and not country:
            country = content
        elif "모든 성분" in header or "전성분" in header:
            if not ingredients_raw:
                ingredients_raw = content
        elif "소비자상담" in header or "전화번호" in header:
            if not contact_phone:
                found_numbers = re.findall(r"(\d{2,4}-\d{3,4}-\d{4}|\d{4}-\d{4})", content)
                if found_numbers:
                    contact_phone = ", ".join(found_numbers)
                else:
                    contact_phone = re.sub(r"[^\d\-]", "", content)

    # 기획 세트(+) 스킵
    if "+" in capacity:
        print(f"\n[기획 세트 제외] 용량: '{capacity}'")
        time.sleep(random.uniform(0.5, 0.8))
        driver.back()
        show_toast("기획 세트 제외", f"용량: {capacity}\n(+) 포함 스킵", 1500, fg_color="#ff5252")
        return

    # 상품명 파싱
    raw_name = ""
    for sel in ["#goodsNm", "p.prd_name", "h2.prd_name", ".prd_name"]:
        el = soup_table.select_one(sel)
        if el and el.text.strip():
            raw_name = el.text.strip()
            break

    if not raw_name:
        og_title = soup_table.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            raw_name = og_title["content"].split("|")[0].replace("[올리브영]", "").strip()

    # 브랜드 / 상품명 분리
    without_brackets = re.sub(r"\[.*?\]", "", raw_name).strip()
    tokens = without_brackets.split(maxsplit=1)
    brand = tokens[0] if tokens else "기타"
    product_name = tokens[1] if len(tokens) > 1 else without_brackets

    price = get_real_price()

    # 카테고리 태깅
    p_type = "기초"
    for t in ["토너", "스킨", "패드", "로션", "에멀젼", "세럼", "에센스", "앰플", "크림", "선크림", "미스트"]:
        if t in raw_name:
            p_type = t
            break

    # 필수값 검증
    price_val = int(price) if str(price).isdigit() else 0
    missing_fields = []

    if price_val <= 0:
        missing_fields.append("가격(0원)")
    if not brand or brand == "기타":
        missing_fields.append("브랜드")
    if not product_name or product_name == "상품명 확인불가":
        missing_fields.append("상품명")
    if not capacity.strip():
        missing_fields.append("용량")
    if not ingredients_raw.strip():
        missing_fields.append("전성분")

    if missing_fields:
        err_msg = ", ".join(missing_fields)
        print(f"\n[데이터 누락] {err_msg}")
        show_toast("수집 보류", f"누락 항목: {err_msg}", 2000, fg_color="#ffb300")
        return

    # 엑셀 누적 저장
    new_data = {
        "product_id": f"P{captured_count + 1:04d}",
        "brand": brand,
        "product_name": product_name,
        "product_type": p_type,
        "price": price_val,
        "capacity": capacity,
        "skin_type": skin_type,
        "expiry_date": expiry_date,
        "how_to_use": how_to_use,
        "country": country,
        "contact_phone": contact_phone,
        "ingredients_raw": ingredients_raw,
        "source_url": current_url,
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    new_df = pd.DataFrame([new_data])
    try:
        if os.path.exists(EXCEL_FILE):
            existing_df = pd.read_excel(EXCEL_FILE)
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            final_df = new_df

        final_df.to_excel(EXCEL_FILE, index=False)
        captured_count += 1
    except PermissionError:
        print("\n[에러] 엑셀 파일 열림 상태. 파일 종료 후 재시도 필요.")
        show_toast("저장 실패", "엑셀 파일 열림 상태\n파일 닫고 F4 재시도", 2500, fg_color="#ff5252")
        return

    print(f"\n[저장 완료 - 누적 {captured_count}건]")
    print(f"브랜드: {brand} | 상품명: {product_name[:20]} | 판매가: {price_val:,}원")

    time.sleep(random.uniform(1.0, 1.6))
    driver.back()
    show_toast("저장 완료", f"P{captured_count:04d} [{brand}] 저장 완료", 1200)


print("\n" + "=" * 50)
print(f" [올리브영 크롤러: 현재 {captured_count}건]")
print(f" * 저장 경로: {EXCEL_FILE}")
print(" * 주의: 엑셀 파일 오픈 금지 (충돌 방지)")
print(" * [ F3 ] : 고시정보 포커스")
print(" * [ F4 ] : 데이터 저장 & 뒤로가기")
print(" * [ Esc ]: 뒤로가기")
print("=" * 50 + "\n")

keyboard.add_hotkey("F3", scroll_to_notice_info)
keyboard.add_hotkey("F4", capture_current_page)
keyboard.add_hotkey("esc", go_back_page)

try:
    keyboard.wait()
except (KeyboardInterrupt, SystemExit):
    try:
        driver.quit()
    except:
        pass
    print("\n종료.")
