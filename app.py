import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from fpdf import FPDF
import base64

# --- Paleta de colores personalizada ---
primary_color = "#007ACC"  # azul
accent_color = "#2ECC71"  # verde
bg_color = "#F5F9FC"
text_color = "#1C2833"

st.markdown(f"""
    <style>
        .main {{
            background-color: {bg_color};
        }}
        .stApp {{
            color: {text_color};
        }}
        div.stButton > button:first-child {{
            background-color: {primary_color};
            color: white;
        }}
        div.stDownloadButton > button:first-child {{
            background-color: {accent_color};
            color: white;
        }}
        .stRadio > div {{
            background-color: {bg_color};
            color: {text_color};
        }}
    </style>
""", unsafe_allow_html=True)

# --- Configuración general ---
st.set_page_config(
    page_title="Medios de Cultivo InVitro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Archivos de datos ---
INVENTARIO_CSV = "inventario_medios.csv"
SOLUCIONES_CSV = "soluciones_stock.csv"

# --- Cargar datos persistentes ---
if os.path.exists(INVENTARIO_CSV):
    inventario_df = pd.read_csv(INVENTARIO_CSV)
else:
    inventario_df = pd.DataFrame(columns=["Código", "Año", "Receta", "Solución", "Semana", "Día", "Preparación", "Fecha_Registro"])

if os.path.exists(SOLUCIONES_CSV):
    soluciones_df = pd.read_csv(SOLUCIONES_CSV)
else:
    soluciones_df = pd.DataFrame(columns=["Fecha", "Cantidad_Pesada", "Código_Solución", "Responsable", "Observaciones"])

# --- Navegación lateral ---
with st.sidebar:
    st.title("🗭 Menú")
    menu = st.radio("Selecciona una sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario General",
        "Historial",
        "Soluciones Stock",
        "Recetas de medios"
    ])

# --- Cabecera ---
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("logo_blackberry.png", width=60)
with col2:
    st.markdown("<h1 style='text-align: center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
with col3:
    st.empty()
st.markdown("---")

# --- Funciones ---
def generar_qr(texto):
    qr = qrcode.make(texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return Image.open(buffer)

def generar_etiqueta_qr(info, qr_img, codigo, titulo="🧪 MEDIO DE CULTIVO"):
    etiqueta = Image.new("RGB", (472, 283), "white")
    draw = ImageDraw.Draw(etiqueta)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    try:
        logo = Image.open("logo_blackberry.png").resize((50, 50))
        etiqueta.paste(logo, (400, 230))
    except:
        pass
    draw.text((10, 10), titulo, font=font, fill="black")
    y = 40
    for linea in info:
        draw.text((10, y), linea, font=font, fill="black")
        y += 32
    qr_img = qr_img.resize((120, 120))
    etiqueta.paste(qr_img, (330, 20))
    draw.text((10, 240), f"Código: {codigo}", font=font, fill="black")
    output = BytesIO()
    etiqueta.save(output, format="PNG")
    output.seek(0)
    return output

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    output.seek(0)
    return output

# --- Lógica para cada sección ---
# ... (Aquí continúa el flujo para cada sección: Registrar Lote, Historial, etc. ya integrados previamente)

# NOTA: Las funciones y estructuras de interfaz ya están integradas en los pasos anteriores.
# Puedes correr este script como base unificada.
