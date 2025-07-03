import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
import json
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#D32F2F"
ACCENT_COLOR = "#FFFFFF"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    div.stButton>button, div.stDownloadButton>button {{ background-color: {PRIMARY_COLOR}; color: {ACCENT_COLOR}; }}
</style>
""", unsafe_allow_html=True)

# --- Rutas de archivos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
USERS_FILE = "users.json"

# --- Carga inicial de datos ---
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
inv_df = pd.read_csv(INV_FILE)[inv_cols] if os.path.exists(INV_FILE) else pd.DataFrame(columns=inv_cols)
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
sol_df = pd.read_csv(SOL_FILE)[sol_cols] if os.path.exists(SOL_FILE) else pd.DataFrame(columns=sol_cols)

# --- Carga de recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Gestión de usuarios con roles ---
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"admin":{"pwd":"1234","role":"admin"}}, f)
    with open(USERS_FILE) as f:
        return json.load(f)
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
users = load_users()

# --- Funciones auxiliares ---
def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
def make_label(info: list, qr_bytes: bytes) -> Image.Image:
    label = Image.new("RGB", (400, 130), "white")
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    y = 10
    for line in info:
        draw.text((10, y), line, fill="black", font=font)
        y += 18
    qr_img = Image.open(BytesIO(qr_bytes)).resize((80, 80))
    label.paste(qr_img, (310, 10))
    return label
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Login")
    usr = st.sidebar.text_input("Usuario")
    pwd = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Ingresar"):
        if usr in users and users[usr]['pwd'] == pwd:
            st.session_state.logged_in = True
            st.session_state.user = usr
            st.session_state.role = users[usr]['role']
            st.experimental_rerun()
        else:
            st.sidebar.error("Credenciales inválidas")
    st.stop()

# --- Menú lateral ---
base_sections = ["Registrar Lote","Consultar Stock","Inventario","Historial","Soluciones Stock","Recetas","Imprimir Etiquetas"]
admin_sections = ["Bajas Inventario","Administrar Sistema"]
sections_list = base_sections + (admin_sections if st.session_state.role == 'admin' else [])
choice = st.sidebar.selectbox("Menú", sections_list)

# --- Cabecera ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones (definir según versiones previas) ---
def section_bajas():
    st.subheader("⚠️ Dar de baja Inventarios")
    pass
def section_admin():
    st.subheader("⚙️ Administración del Sistema")
    st.write(f"Usuario: {st.session_state.user} (rol: {st.session_state.role})")
    st.markdown("---")
    st.subheader("👥 Gestión de Usuarios")
    st.write("Usuarios:", users)
    new_u = st.text_input("Nuevo usuario")
    new_p = st.text_input("Contraseña", type="password")
    new_r = st.selectbox("Rol", ["user","admin"])
    if st.button("Agregar usuario"):
        users[new_u] = {"pwd": new_p, "role": new_r}
        save_users(users)
        st.experimental_rerun()
    to_del = st.multiselect("Eliminar usuario", [u for u in users if u != st.session_state.user])
    if st.button("Eliminar"):
        for u in to_del: users.pop(u, None)
        save_users(users)
        st.experimental_rerun()

# --- Dispatcher ---
dispatch = {
    "Bajas Inventario": section_bajas,
    "Administrar Sistema": section_admin,
}
dispatch.get(choice, lambda: st.write(f"Sección '{choice}' aún no implementada."))()

# Footer
txt = f"**Usuario**: {st.session_state.user}  \n**Rol**: {st.session_state.role}"
st.sidebar.markdown(txt)
