import streamlit as st
import os
from pathlib import Path
import base64
from streamlit_pdf_viewer import pdf_viewer


st.set_page_config(layout="wide")

# SESSION STATE
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
    st.session_state.selected_name = None
    st.session_state.selected_meta = None

# HEADER TITLE
st.markdown("""
<div style='background-color:#bbdefb;
            padding:20px;
            border-radius:12px;
            margin-bottom:15px;
            text-align:center;'>
    <h1 style='color:#0d47a1;margin:0;'>
        HỆ THỐNG TÀI LIỆU AN TOÀN SINH HỌC - PHÒNG CÔNG NGHỆ SINH HỌC Y DƯỢC
    </h1>
</div>
""", unsafe_allow_html=True)
# ==========================
# CUSTOM STYLE (PASTEL BLUE)
# ==========================

st.markdown("""
<style>
    .main {
        background-color: #f4faff;
    }
    section[data-testid="stSidebar"] {
        background-color: #e3f2fd;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #bbdefb;
        color: #0d47a1;
        border: none;
        padding: 6px;
    }
    .stButton>button:hover {
        background-color: #90caf9;
        color: #0d47a1;
    }
    .doc-box {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# CONFIG PATHS
# ==========================

BASE_DIR = Path("data")
PDF_DIR = BASE_DIR / "pdf"
DOCX_DIR = BASE_DIR / "docx"

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
    structure = {
        "Sổ tay an toàn": {},
        "Quy định": {},
        "Quy trình thực hành chuẩn": {
            "Quy trình kỹ thuật": {},
            "Quy trình quản lý": {}
        }
    }

    def match(file):
        return search_term.lower() in file.stem.lower()

    for file in (PDF_DIR / "notebook").glob("*.pdf"):
        if match(file):
            structure["Sổ tay an toàn"][file.stem] = file

    for file in (PDF_DIR / "rule").glob("*.pdf"):
        if match(file):
            structure["Quy định"][file.stem] = file

    for sub in ["technical", "management"]:
        folder = PDF_DIR / "sop" / sub
        for file in folder.glob("*.pdf"):
            if match(file):
                key = "Quy trình kỹ thuật" if sub == "technical" else "Quy trình quản lý"
                structure["Quy trình thực hành chuẩn"][key][file.stem] = file

    return structure


def display_pdf(file_path):
    pdf_viewer(file_path)

def get_docx_files(name):
    if not name:
        return []
    return [f for f in DOCX_DIR.glob("*.docx") if name.lower() in f.stem.lower()]

# ==========================
# LAYOUT (WIDER CENTER)
# ==========================

col1, col2, col3 = st.columns([1.2, 3.5, 1.3])

search_term = st.text_input("🔍 Tìm kiếm tài liệu", "")
structure = get_file_tree(search_term)

selected_file = None
selected_name = None
selected_meta = None

# ==========================
# LEFT MENU
# ==========================

with col1:
    st.markdown("### 📂 Danh mục")

    for level1, content1 in structure.items():
        with st.expander(level1, expanded=True):

            # 🔹 CASE 1: KHÔNG có cấp con (file trực tiếp)
            if level1 in ["Quy định", "Sổ tay an toàn"]:
                for name, path in content1.items():
                    code, version, title = parse_filename(path)
                    label = f"{title}\n({code} | {version})"

                    if st.button(label, key=f"{level1}_{name}"):
                        st.session_state.selected_file = path
                        st.session_state.selected_name = name
                        st.session_state.selected_meta = (code, version, title)

            # 🔹 CASE 2: CÓ cấp con (SOP)
            else:
                for level2, content2 in content1.items():
                    with st.expander(level2):
                        for name, path in content2.items():
                            code, version, title = parse_filename(path)
                            label = f"{title}\n({code} | {version})"

                            if st.button(label, key=f"{level2}_{name}"):
                                st.session_state.selected_file = path
                                st.session_state.selected_name = name
                                st.session_state.selected_meta = (code, version, title)

# ==========================
# CENTER PDF VIEW
# ==========================

with col2:
    st.markdown("### 📄 Nội dung tài liệu")

    if st.session_state.selected_file:
        code, version, title = st.session_state.selected_meta

        st.markdown(f"""
        <div class="doc-box">
        <b>{title}</b><br>
        Mã: {code} | Phiên bản: {version}
        </div>
        """, unsafe_allow_html=True)
        pdf_viewer(st.session_state.selected_file, width="100%", height=1000)
    else:
        st.info("Chọn tài liệu từ menu bên trái")

# ==========================
# RIGHT PANEL
# ==========================

with col3:
    st.markdown("### 📥 Biểu mẫu")

    if st.session_state.selected_name:
        files = get_docx_files(st.session_state.selected_name)

        if files:
            for file in files:
                with open(file, "rb") as f:
                    st.download_button(
                        label=f"⬇ {file.name}",
                        data=f,
                        file_name=file.name
                    )
        else:
            st.warning("Không có biểu mẫu")
    else:
        st.info("Chọn tài liệu")

# ==========================
# FOOTER
# ==========================

st.markdown("---")
st.markdown("<center style='color:gray'>Hệ thống tài liệu An toàn sinh học</center>", unsafe_allow_html=True)
