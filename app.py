import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from difflib import get_close_matches
import json
from PIL import Image
import matplotlib.pyplot as plt
import re
import base64
import os

# --- Cấu hình trang ---
st.set_page_config(page_title="Chatbot Phạm Hồng Long", layout="centered")

# --- Hiển thị logo ---
logo = Image.open("logo_hinh_tron.png")
st.image(logo, width=200)
st.markdown("""
<h1 style='text-align: center; color: orange;'>🤖 Chatbot PHẠM HỒNG LONG</h1>
<h4 style='text-align: center; color: gray;'>Trợ lý hỏi – đáp dữ liệu tự động</h4>
""", unsafe_allow_html=True)

# --- Giải mã KEY bí mật an toàn ---
try:
    key_json = st.secrets["gspread_secret"]
    key_decoded = base64.b64decode(key_json).decode("utf-8")
    key_dict = json.loads(key_decoded)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/13MqQzvV3Mf9bLOAXwICXclYVQ-8WnvBDPAR8VJfOGJg")
    worksheet = sheet.worksheet("Hỏi-Trả lời")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
    st.stop()

# --- Hiển thị gợi ý câu hỏi ---
with open("sample_questions.json", "r", encoding="utf-8") as f:
    sample_questions = json.load(f)

with st.expander("📌 Gợi ý câu hỏi mẫu"):
    for q in sample_questions:
        st.markdown(f"- {q}")

question = st.text_input("💬 Nhập câu hỏi của bạn")

# --- Tra lãnh đạo xã ---
def handle_lanh_dao():
    try:
        if "lãnh đạo" in question.lower() and any(xa in question.lower() for xa in ["định hóa", "kim phượng", "phượng tiến", "trung hội", "bình yên", "phú đình", "bình thành", "lam vỹ"]):
            sheet_ld = sheet.worksheet("Danh sách lãnh đạo xã, phường")
            df_ld = pd.DataFrame(sheet_ld.get_all_records())

            xa_match = re.search(r'xã|phường ([\w\s]+)', question.lower())
            if xa_match:
                ten_xa = xa_match.group(1).strip().upper()
            else:
                for row in df_ld['Thuộc xã/phường'].unique():
                    if row.lower() in question.lower():
                        ten_xa = row.upper()
                        break
                else:
                    st.warning("❗ Không xác định được tên xã/phường trong câu hỏi.")
                    return True

            df_loc = df_ld[df_ld['Thuộc xã/phường'].str.upper().str.contains(ten_xa)]
            if df_loc.empty:
                st.warning(f"❌ Không tìm thấy dữ liệu lãnh đạo cho xã/phường: {ten_xa}")
            else:
                st.success(f"📋 Danh sách lãnh đạo xã/phường {ten_xa}")
                st.dataframe(df_loc.reset_index(drop=True))
            return True
    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu lãnh đạo xã: {e}")
    return False

# --- TBA theo đường dây ---
def handle_tba():
    if "tba" in question.lower() and "đường dây" in question.lower():
        try:
            sheet_tba = sheet.worksheet("Tên các TBA")
            df_tba = pd.DataFrame(sheet_tba.get_all_records())
            match = re.search(r'(\d{3}E6\.22)', question.upper())
            if match:
                dd = match.group(1)
                df_dd = df_tba[df_tba['STT đường dây'].astype(str).str.contains(dd)]
                if not df_dd.empty:
                    st.success(f"📄 Danh sách TBA trên đường dây {dd}")
                    st.dataframe(df_dd.reset_index(drop=True))
                else:
                    st.warning(f"❌ Không tìm thấy TBA trên đường dây {dd}")
                return True
        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu TBA: {e}")
            return True
    return False

# --- Gọi hàm ---
if question:
    matches = get_close_matches(question, df['Câu hỏi'], n=1, cutoff=0.6)
    if matches:
        matched_question = matches[0]
        answer_row = df[df['Câu hỏi'] == matched_question].iloc[0]
        st.success(f"**Trả lời:** {answer_row['Câu trả lời']}")
    elif "lãnh đạo" in question.lower():
        matched = handle_lanh_dao()
    elif "tba" in question.lower():
        matched = handle_tba()
    else:
        fallback_matches = get_close_matches(question, sample_questions, n=1, cutoff=0.6)
        if fallback_matches:
            st.info(f"❔ Câu hỏi gần giống: '{fallback_matches[0]}'\n\nHiện tại câu trả lời đang được cập nhật. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.")
        else:
            st.warning("❌ Không tìm thấy câu trả lời phù hợp trong dữ liệu. Hãy thử lại với cách diễn đạt khác.")