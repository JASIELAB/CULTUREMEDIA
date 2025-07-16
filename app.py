import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de archivos CSV ---
INV_FILE  = "inventario_medios.csv"
MOV_FILE  = "movimientos.csv"
SOL_FILE  = "soluciones_stock.csv"

inv_cols  = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final","Litros_preparar",
    "Dosificar_por_frasco","Fecha"
]
mov_cols  = ["Timestamp","Tipo","Código","Cantidad","Detalles"]
sol_cols  = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def save_df(path, df):
    df.to_csv(path, index=False)

# --- Carga inicial ---
inv_df = load_df(INV_FILE, inv_cols)
mov_df = load_df(MOV_FILE, mov_cols)
sol_df = load_df(SOL_FILE, sol_cols)

# --- Helpers QR y etiquetas ---
def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf

def make_label(lines, qr_buf, size=(250,120)):
    w,h = size
    img = Image.new("RGB", (w,h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
    except IOError:
        font = ImageFont.load_default()
    y = 5
    for L in lines:
        draw.text((5,y), L, fill="black", font=font)
        _, th = draw.textsize(L, font=font)
        y += th + 2
    qr = Image.open(qr_buf).resize((80,80))
    img.paste(qr, (w-qr.width-5, (h-qr.height)//2))
    return img

# --- Interfaz ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

# --- Menú en grid 2×3 secciones ---
if "choice" not in st.session_state:
    st.session_state.choice = None

# Fila 1
r1 = st.columns(3)
with r1[0]:
    st.subheader("📦 Stock Control")
    if st.button("Stock List Lab", key="stock_lab"):
        st.session_state.choice = "Stock List Lab"
    if st.button("Stock List Greenhouse", key="stock_green"):
        st.session_state.choice = "Stock List Greenhouse"
    if st.button("Mobile Scanner", key="mobile_scanner"):
        st.session_state.choice = "Mobile Scanner"
with r1[1]:
    st.subheader("🧪 Production Processes")
    if st.button("Entry Registration", key="entry_reg"):
        st.session_state.choice = "Entry Registration"
    if st.button("Production", key="production"):
        st.session_state.choice = "Production"
    if st.button("Culture Testing", key="culture_test"):
        st.session_state.choice = "Culture Testing"
with r1[2]:
    st.subheader("⚙️ Additional Functions")
    if st.button("Register Breaktimes", key="breaktimes"):
        st.session_state.choice = "Register Breaktimes"
    if st.button("Planning", key="planning_main"):
        st.session_state.choice = "Planning Main"
    if st.button("Media Production", key="media_prod"):
        st.session_state.choice = "Media Production"

# Fila 2
r2 = st.columns(3)
with r2[0]:
    st.subheader("📊 Reports")
    if st.button("Production Control", key="rep_prod"):
        st.session_state.choice = "Production Control"
    if st.button("Evaluations", key="rep_eval"):
        st.session_state.choice = "Evaluations"
with r2[1]:
    st.subheader("🚚 Reduce Stock")
    if st.button("Deliveries", key="deliveries"):
        st.session_state.choice = "Deliveries"
    if st.button("Losses", key="losses"):
        st.session_state.choice = "Losses"
with r2[2]:
    st.subheader("🗄 Basic Data")
    if st.button("Basic Data", key="basic_data"):
        st.session_state.choice = "Basic Data"
    if st.button("Media Management", key="media_mgmt"):
        st.session_state.choice = "Media Management"
    if st.button("Breeding", key="breeding"):
        st.session_state.choice = "Breeding"

st.markdown("---")
choice = st.session_state.choice

# --- Lógica según elección ---
# 1) Stock List Lab
if choice == "Stock List Lab":
    st.header("📦 Stock List Lab")
    st.dataframe(inv_df, use_container_width=True)

# 2) Stock List Greenhouse
elif choice == "Stock List Greenhouse":
    st.header("📦 Stock List Greenhouse")
    st.info("Aquí iría tu lógica para invernadero.")

# 3) Mobile Scanner
elif choice == "Mobile Scanner":
    st.header("📱 Mobile Scanner")
    st.info("Funcionalidad de escáner móvil pendiente.")

# 4) Entry Registration
elif choice == "Entry Registration":
    st.header("📋 Entry Registration")
    # Puedes mapear esto a tu “Registrar Lote”
    # Reusa el bloque de Registrar Lote de abajo si quieres

# 5) Production
elif choice == "Production":
    st.header("🧪 Production")
    st.info("Proceso de producción pendiente.")

# 6) Culture Testing
elif choice == "Culture Testing":
    st.header("🔬 Culture Testing")
    st.info("Test de cultivos pendiente.")

# 7) Register Breaktimes
elif choice == "Register Breaktimes":
    st.header("⏱ Register Breaktimes")
    st.info("Registro de pausas pendiente.")

# 8) Planning Main
elif choice == "Planning Main":
    st.header("📅 Planning")
    st.info("Usa la sección Planning del menú original.")

# 9) Media Production
elif choice == "Media Production":
    st.header("⚗️ Media Production")
    st.info("Producción de medios pendiente.")

# 10) Production Control
elif choice == "Production Control":
    st.header("📈 Production Control")
    st.info("Reporte de control de producción.")

# 11) Evaluations
elif choice == "Evaluations":
    st.header("📋 Evaluations")
    st.info("Reporte de evaluaciones.")

# 12) Deliveries
elif choice == "Deliveries":
    st.header("🚚 Deliveries")
    st.info("Registro de entregas pendiente.")

# 13) Losses
elif choice == "Losses":
    st.header("🌱 Losses")
    st.info("Registro de mermas pendiente.")

# 14) Basic Data
elif choice == "Basic Data":
    st.header("🗄 Basic Data")
    st.info("Gestión de datos básicos pendiente.")

# 15) Media Management
elif choice == "Media Management":
    st.header("⚗️ Media Management")
    st.info("Gestión de medios pendiente.")

# 16) Breeding
elif choice == "Breeding":
    st.header("🌿 Breeding")
    st.info("Gestión de reproducción pendiente.")

# 17) Recetas de Medios (puedes enlazar aquí)
elif choice == "Media Production":  # o ajusta al original “Recetas de Medios”
    pass  # ...

# Si quieres recuperar tu antiguo menú completo, reubica aquí:
# elif choice == "Registrar Lote": …
# elif choice == "Consultar Stock": …
# etc., copiando los bloques de la versión CSV simplificada.

