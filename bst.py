import streamlit as st
import os
from pathlib import Path
import base64
from streamlit_pdf_viewer import pdf_viewer
from docx2pdf import convert
import pythoncom

st.set_page_config(layout="wide")

# ==========================
# CONFIG PATHS & INIT
# ==========================
BASE_DIR = Path("data")
PDF_DIR = BASE_DIR / "pdf"
DOCX_DIR = BASE_DIR / "docx"
PREVIEW_CACHE_DIR = BASE_DIR / "preview_cache"
PREVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# SESSION STATE
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
    st.session_state.selected_name = None
    st.session_state.selected_meta = None

# HEADER TITLE
st.markdown("""
<div style='background-color:#bbdefb; padding:20px; border-radius:12px; margin-bottom:15px; text-align:center;'>
    <h1 style='color:#0d47a1;margin:0;'>HỆ THỐNG TÀI LIỆU AN TOÀN SINH HỌC - PHÒNG CÔNG NGHỆ SINH HỌC Y DƯỢC</h1>
</div>
""", unsafe_allow_html=True)

# CUSTOM STYLE
st.markdown("""
<style>
    .main { background-color: #f4faff; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #bbdefb; color: #0d47a1; border: none; padding: 6px; }
    .stButton>button:hover { background-color: #90caf9; }
    .doc-box { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================
# FUNCTIONS
# ==========================
def parse_filename(file_path):
    parts = file_path.stem.split("__")
    code = parts[0] if len(parts) > 0 else "N/A"
    version = parts[1] if len(parts) > 1 else "v?"
    title = parts[2] if len(parts) > 2 else file_path.stem
    return code, version, title

def get_file_tree(search_term=""):
    structure = {"Sổ tay an toàn": {}, "Quy định": {}, "Quy trình thực hành chuẩn": {"Quy trình kỹ thuật": {}, "Quy trình quản lý": {}}}
    def match(file): return search_term.lower() in file.stem.lower()
    
    for folder_name, sub_path in [("notebook", "Sổ tay an toàn"), ("rule", "Quy định")]:
        if (PDF_DIR / folder_name).exists():
            for file in (PDF_DIR / folder_name).glob("*.pdf"):
                if match(file): structure[sub_path][file.stem] = file
                
    for sub, key in [("technical", "Quy trình kỹ thuật"), ("management", "Quy trình quản lý")]:
        folder = PDF_DIR / "sop" / sub
        if folder.exists():
            for file in folder.glob("*.pdf"):
                if match(file): structure["Quy trình thực hành chuẩn"][key][file.stem] = file
    return structure

def get_docx_files(name):
    if not name or not DOCX_DIR.exists(): return []
    return [f for f in DOCX_DIR.glob("*.docx") if name.lower() in f.stem.lower()]

# --- HÀM DIALOG XEM TRƯỚC (ĐÃ FIX) ---
@st.dialog("Xem trước biểu mẫu", width="large")
def preview_docx_dialog(docx_file):
    st.write(f"Đang xem: **{docx_file.name}**")
    pdf_cache_path = PREVIEW_CACHE_DIR / f"{docx_file.stem}_preview.pdf"
    
    if not pdf_cache_path.exists():
        with st.spinner("Đang chuyển đổi sang PDF..."):
            try:
                # Khởi tạo COM cho luồng hiện tại
                pythoncom.CoInitialize() 
                convert(str(docx_file), str(pdf_cache_path))
            except Exception as e:
                st.error(f"Lỗi chuyển đổi: {e}")
                # Hủy khởi tạo nếu lỗi để tránh rò rỉ bộ nhớ
                pythoncom.CoUninitialize() 
                return
            finally:
                # Luôn đóng khởi tạo sau khi xong
                pythoncom.CoUninitialize() 

    pdf_viewer(str(pdf_cache_path), width="100%", height=600)
    
    if st.button("Đóng"):
        st.rerun()

    with open(docx_file, "rb") as f:
        st.download_button("⬇ Tải xuống file gốc (.docx)", f, file_name=docx_file.name)

# ==========================
# LAYOUT & UI
# ==========================
col1, col2, col3 = st.columns([1.2, 3.5, 1.3])

with col1:
    search_term = st.text_input("🔍 Tìm kiếm tài liệu", "")
    structure = get_file_tree(search_term)
    st.markdown("### 📂 Danh mục")
    for level1, content1 in structure.items():
        with st.expander(level1, expanded=True):
            if level1 in ["Quy định", "Sổ tay an toàn"]:
                for name, path in content1.items():
                    code, version, title = parse_filename(path)
                    if st.button(f"{title}\n({code} | {version})", key=f"{level1}_{name}"):
                        st.session_state.selected_file = path
                        st.session_state.selected_name = name
                        st.session_state.selected_meta = (code, version, title)
            else:
                for level2, content2 in content1.items():
                    with st.expander(level2):
                        for name, path in content2.items():
                            code, version, title = parse_filename(path)
                            if st.button(f"{title}\n({code} | {version})", key=f"{level2}_{name}"):
                                st.session_state.selected_file = path
                                st.session_state.selected_name = name
                                st.session_state.selected_meta = (code, version, title)

with col2:
    st.markdown("### 📄 Nội dung tài liệu")
    if st.session_state.selected_file:
        code, version, title = st.session_state.selected_meta
        st.markdown(f"<div class='doc-box'><b>{title}</b><br>Mã: {code} | Phiên bản: {version}</div>", unsafe_allow_html=True)
        pdf_viewer(st.session_state.selected_file, width="100%", height=1000)
    else:
        st.info("Chọn tài liệu từ menu bên trái")

with col3:
    st.markdown("### 📥 Biểu mẫu")
    if st.session_state.selected_name:
        files = get_docx_files(st.session_state.selected_name)
        if files:
            for file in files:
                # Key duy nhất cho nút để tránh xung đột
                if st.button(f"👁️ Xem: {file.name}", key=f"btn_{file.name}"):
                    preview_docx_dialog(file)
        else:
            st.warning("Không có biểu mẫu")
    else:
        st.info("Chọn tài liệu")

st.markdown("---")
st.markdown("<center style='color:gray'>Hệ thống tài liệu An toàn sinh học</center>", unsafe_allow_html=True)
