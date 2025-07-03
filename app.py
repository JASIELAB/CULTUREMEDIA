import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont
from streamlit_option_menu import option_menu

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#D32F2F"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    .option-menu {{ padding: 0; }}
    .nav-link {{ font-size: 14px; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos y DataFrames ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)[inv_cols]
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)[sol_cols]
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Funciones auxiliares ---

def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def make_label(info: list, qr_bytes: bytes) -> Image.Image:
    width, height = 500, 150
    label = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    x_text, y_text = 10, 10
    for line in info:
        draw.text((x_text, y_text), line, fill="black", font=font)
        y_text += 20
    qr_img = Image.open(BytesIO(qr_bytes)).resize((80, 80))
    qr_x = width - qr_img.width - 10
    qr_y = (height - qr_img.height) // 2
    label.paste(qr_img, (qr_x, qr_y))
    return label

# --- Menú principal estilo grid ---
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=[
            "Stock Control", "Entry Registration", "Production", "Culture Testing", "Harvesting Bag", "Activities",
            "Register Breaktimes","Planning","Sales","Media Production",
            "Production Control","Evaluations",
            "Deliveries","Losses",
            "Basic Data","Media Management","Breeding"
        ],
        icons=[
            "clipboard-check","clipboard-plus","factory","microscope","truck-loading","list-task",
            "clock-history","calendar","bar-chart-line","beaker","bag-heart","people-fill",
            "box-seam","exclamation-triangle",
            "file-earmark-text","book","seedling"
        ],
        menu_icon="app-indicator",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#FFFFFF"},
            "icon": {"color": "#4CAF50", "font-size": "16px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px","--hover-color":"#E8F5E9"},
            "nav-link-selected": {"background-color": "#C8E6C9"}
        }
    )

st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")

# Aquí seguirían los bloques para cada sección, usando `selected` en lugar de `choice`...
