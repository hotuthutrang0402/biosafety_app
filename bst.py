import streamlit as st
import os
from pathlib import Path
import base64
from streamlit_pdf_viewer import pdf_viewer
import subprocess

st.set_page_config(layout="wide")

# ==========================
# CONFIG PATHS & INIT
# ==========================

BASE_DIR = Path("data")
PDF_DIR = BASE_DIR / "pdf"
DOCX_DIR = BASE_DIR / "docx"
INFO_DIR = BASE_DIR / "info"  # Thêm dòng này
PREVIEW_CACHE_DIR = BASE_DIR / "preview_cache"
PREVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
INFO_DIR.mkdir(parents=True, exist_ok=True)

# SESSION STATE
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
    st.session_state.selected_name = None
    st.session_state.selected_meta = None

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# HEADER TITLE
banner_img = get_img_as_base64("biosafety_banner.jpeg") # Thay tên file của bạn ở đây

st.markdown(f"""
<div style="width: 100%; margin-bottom: 20px;">
    <img src="data:image/png;base64,{banner_img}" style="width: 100%; border-radius: 12px;">
    <div style='background-color:#bbdefb; padding:20px; border-radius:0 0 12px 12px; text-align:center; margin-top:-5px;'>
        <h1 style='color:#0d47a1; margin:0; font-size: 54px; font-weight: 900; letter-spacing: 1px;'>
            HỆ THỐNG TÀI LIỆU AN TOÀN SINH HỌC
        </h1>
        <p style='color:#1565c0; margin: 10px 0 0 0; font-size: 32px; font-weight: 600;'>
            PHÒNG CÔNG NGHỆ SINH HỌC Y DƯỢC
        </p>
    </div>
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
    parts = file_path.stem.split("_")
    code = parts[0] if len(parts) > 0 else "N/A"
    version = parts[1] if len(parts) > 1 else "v?"
    date = parts[2] if len(parts) > 2 else "e?"
    title = "_".join(parts[3:]) if len(parts) > 3 else file_path.stem
    return code, version, date, title

def get_file_tree(search_term=""):
    # Định nghĩa lại hàm match ngay bên trong để chắc chắn nó có phạm vi hoạt động
    def match(file):
        if not search_term:
            return True
        keyword = search_term.strip().lower()
        # Nếu là file TXT → search trực tiếp tên file
        if file.suffix == ".txt":
            return keyword in file.stem.lower()
        # Các file khác → dùng parse
        code, version, date, title = parse_filename(file)
        return (
            keyword in title.lower() or
            keyword in code.lower()
        )
    structure = {
        "Thông tin chung": {}, 
        "Sổ tay an toàn": {}, 
        "Quy định": {}, 
        "Quy trình thực hành chuẩn": {
            "Quy trình kỹ thuật": {}, 
            "Quy trình quản lý": {}
        }
    }
    
    # 1. Xử lý Thông tin chung (.txt)
    info_dir = BASE_DIR / "info"
    if info_dir.exists():
        for file in info_dir.glob("*.txt"):
            if match(file): 
                structure["Thông tin chung"][file.stem] = file

    # 2. Xử lý Sổ tay và Quy định (.pdf)
    for folder_name, sub_path in [("notebook", "Sổ tay an toàn"), ("rule", "Quy định")]:
        folder = PDF_DIR / folder_name
        if folder.exists():
            for file in sorted(folder.glob("*.pdf"), key=lambda f: parse_filename(f)):
                if match(file): 
                    structure[sub_path][file.stem] = file
                
    # 3. Xử lý SOP (.pdf)
    for sub, key in [("technical", "Quy trình kỹ thuật"), ("management", "Quy trình quản lý")]:
        folder = PDF_DIR / "sop" / sub
        if folder.exists():
            for file in sorted(folder.glob("*.pdf"), key=lambda f: parse_filename(f)):
                if match(file): 
                    structure["Quy trình thực hành chuẩn"][key][file.stem] = file     
    return structure

def get_docx_files(code):
    if not code or not DOCX_DIR.exists():
        return []
    matched_files = []
    for f in DOCX_DIR.glob("*.docx"):
        # Phải hứng đủ 4 biến
        f_code, _, _, _ = parse_filename(f) 
        if f_code.lower() == code.lower():
            matched_files.append(f)
    return matched_files

# --- HÀM DIALOG XEM TRƯỚC (ĐÃ FIX) ---
@st.dialog("Xem trước biểu mẫu", width="large")
def preview_docx_dialog(docx_file):
    st.write(f"Đang xem: **{docx_file.name}**")
    pdf_cache_path = PREVIEW_CACHE_DIR / f"{docx_file.stem}_preview.pdf"
    
    if not pdf_cache_path.exists():
        with st.spinner("Đang chuyển đổi sang PDF..."):
            try:
                # Lệnh chuyển đổi dùng LibreOffice (Chạy được trên Linux/Cloud)
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(PREVIEW_CACHE_DIR),
                    str(docx_file)
                ]
                subprocess.run(cmd, check=True)
                # LibreOffice sẽ tạo file trùng tên nhưng đuôi .pdf, ta đổi tên lại cho đúng cache
                temp_output = PREVIEW_CACHE_DIR / f"{docx_file.stem}.pdf"
                if temp_output.exists():
                    os.rename(temp_output, pdf_cache_path)
            except Exception as e:
                st.error(f"Lỗi hệ thống: {e}. Vui lòng tải file trực tiếp.")
                return
    if pdf_cache_path.exists():
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
    st.markdown("""
        <style>
            .custom-label {
                font-size: 22px !important;
                font-weight: bold !important;
                color: #0d47a1 !important; /* Màu xanh đậm cho nổi bật */
                margin-bottom: 5px !important;
                padding-top: 10px !important;
            }
        </style>
        <div class="custom-label">🔍 Tìm kiếm tài liệu</div>
    """, unsafe_allow_html=True)
    search_term = st.text_input("", label_visibility="collapsed", placeholder="Nhập từ khóa...")
    structure = get_file_tree(search_term)
    st.markdown("### 📂 Danh mục")
    for level1, content1 in structure.items():
        with st.expander(f"**{level1}**", expanded=True):
            if level1 in ["Thông tin chung", "Sổ tay an toàn", "Quy định"]:
                for name, path in content1.items():
                    code, version, date, title = parse_filename(path)
                    if st.button(f"{title}\n({code} | {version})", key=f"{level1}_{name}"):
                        st.session_state.selected_file = path
                        st.session_state.selected_name = name
                        st.session_state.selected_meta = (code, version, date, title)
            else:
                for level2, content2 in content1.items():
                    with st.expander(f"**{level2}**"):
                        for name, path in content2.items():
                            code, version, date, title = parse_filename(path)
                            if st.button(f"{title}\n({code} | {version})", key=f"{level2}_{name}"):
                                st.session_state.selected_file = path
                                st.session_state.selected_name = name
                                st.session_state.selected_meta = (code, version, date, title)

with col2:
    st.markdown("### 📄 Nội dung tài liệu")
    if st.session_state.selected_file:
        file_path = st.session_state.selected_file
        
        # KIỂM TRA ĐUÔI FILE
        if file_path.suffix == ".txt":
            # Đọc nội dung file text
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.text_area("Nội dung:", value=content, height=800)
        else:
            # Hiển thị PDF như cũ
            code, version, date, title = st.session_state.selected_meta
            st.markdown(f"<div class='doc-box'><b>{title}</b><br>Mã số tài liệu: {code} | Phiên bản: {version} | Ngày hiệu lực: {date}</div>", unsafe_allow_html=True)
            pdf_viewer(str(file_path), width="100%", height=1000)
    else:
        st.info("Chọn tài liệu từ menu bên trái")

with col3:
    st.markdown("### 📥 Biểu mẫu")
    if st.session_state.selected_name:
        code, version, date, title = st.session_state.selected_meta
        
        files = get_docx_files(code)
        if files:
            for file in files:
                if st.button(f"👁️ Xem: {file.name}", key=f"btn_{file.name}"):
                    preview_docx_dialog(file)
        else:
            st.warning(f"Không tìm thấy biểu mẫu cho mã: {code}")

st.markdown("---")
st.markdown("<center style='color:gray'>Hệ thống tài liệu An toàn sinh học</center>", unsafe_allow_html=True)
st.markdown("<center style='color:gray'>Phòng Công nghệ sinh học Y Dược, Trung tâm Công nghệ sinh học Thành phố Hồ Chí Minh</center>", unsafe_allow_html=True)
st.markdown("<center style='color:gray'>2374 Đỗ Mười, Khu phố 10, Phường Trung Mỹ Tây, Thành phố Hồ Chí Minh</center>", unsafe_allow_html=True)
# THÊM LOGO VÀO CHÂN TRANG
logo_img = get_img_as_base64("logo.png") # Thay tên file logo của bạn ở đây

st.markdown(f"""
<div style="display: flex; justify-content: center; align-items: center; margin-top: 30px;">
    <img src="data:image/png;base64,{logo_img}" style="width: 100px; height: auto;">
</div>
""", unsafe_allow_html=True)
