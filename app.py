import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#007ACC"
ACCENT_COLOR = "#2ECC71"
BG_COLOR = "#F5F9FC"
TEXT_COLOR = "#1C2833"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    div.stButton>button {{ background-color: {PRIMARY_COLOR}; color: white; }}
    div.stDownloadButton>button {{ background-color: {ACCENT_COLOR}; color: white; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Cargar o inicializar DataFrames ---
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE).reindex(columns=inv_cols)
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE).reindex(columns=sol_cols)
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Cargar recetas ---
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


def make_label(info: list, qr_bytes: bytes) -> bytes:
    # Crear etiqueta 300x150 px con texto y QR
    label = Image.new("RGB", (300, 150), "white")
    draw = ImageDraw.Draw(label)
    font = ImageFont.load_default()
    y = 10
    for line in info:
        draw.text((10, y), line, fill="black", font=font)
        y += 18
    qr_img = Image.open(BytesIO(qr_bytes)).resize((80, 80))
    label.paste(qr_img, (300 - 90, 10))
    buf = BytesIO()
    label.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Sidebar ---
with st.sidebar:
    st.title("🗭 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario",
        "Historial",
        "Soluciones Stock",
        "Recetas",
        "Bajas Inventario"
    ])

# --- Encabezado ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones ---
# Registrar Lote
def section_registrar_lote():
    st.subheader("📋 Registrar Nuevo Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].fillna("").tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, value=1)
    ph_aj = st.number_input("pH ajustado", value=5.8, format="%.2f")
    ph_fin = st.number_input("pH final", value=5.8, format="%.2f")
    ce = st.number_input("CE final (mS/cm)", value=1.0, format="%.2f")
    if st.button("Registrar lote"):
        cod = f"{año}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(' ', '')
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [cod, año, receta, solucion, semana, dia, prep, frascos, ph_aj, ph_fin, ce, fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado exitosamente.")
        info = [
            f"Código: {cod}", f"Año: {año}", f"Receta: {receta}",
            f"Frascos: {frascos}", f"pH ajustado: {ph_aj}", f"pH final: {ph_fin}", f"CE: {ce}"
        ]
        qr_bytes = make_qr("\n".join(info))
        label_bytes = make_label(info, qr_bytes)
        st.image(label_bytes, width=300)
        st.download_button("⬇️ Descargar etiqueta PNG", data=label_bytes, file_name=f"et_{cod}.png", mime="image/png")

# Consultar Stock

def section_consultar_stock():
    st.subheader("📦 Stock Actual")
    st.dataframe(inv_df)
    st.download_button("⬇️ Descargar Stock Excel", data=to_excel_bytes(inv_df), file_name="stock_actual.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Inventario completo

def section_inventario():
    st.subheader("📊 Inventario Completo")
    st.dataframe(inv_df)
    st.download_button("⬇️ Descargar Inventario Excel", data=to_excel_bytes(inv_df), file_name="inventario_completo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Historial

def section_historial():
    st.subheader("📚 Historial")
    if inv_df.empty:
        st.info("No hay registros.")
    else:
        df = inv_df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        dmin, dmax = df['Fecha'].dt.date.min(), df['Fecha'].dt.date.max()
        start = st.date_input("Desde", value=dmin)
        end = st.date_input("Hasta", value=dmax)
        filt = df[(df['Fecha'].dt.date >= start) & (df['Fecha'].dt.date <= end)]
        st.dataframe(filt)
        st.download_button("⬇️ Descargar Historial Excel", data=to_excel_bytes(filt), file_name="historial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Soluciones Stock

def section_soluciones_stock():
    st.subheader("🧪 Registro de soluciones stock")
    fdate = st.date_input("Fecha preparación", value=date.today())
    qty = st.text_input("Cantidad (g/mL)")
    code_s = st.text_input("Código solución")
    who = st.text_input("Responsable")
    regulador = st.text_input("Regulador crecimiento")
    obs2 = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fdate.isoformat(), qty, code_s, who, regulador, obs2]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        info2 = [
            f"Código: {code_s}", f"Fecha: {fdate.isoformat()}",
            f"Cantidad: {qty}", f"Responsable: {who}", f"Regulador: {regulador}", f"Obs: {obs2}"
        ]
        qr2 = make_qr("\n".join(info2))
        label2 = make_label(info2, qr2)
        st.image(label2, width=300)
        st.download_button("⬇️ Descargar etiqueta PNG", data=label2, file_name=f"sol_{code_s}.png", mime="image/png")
    st.markdown("---")
    st.subheader("📋 Lista de soluciones stock")
    st.dataframe(sol_df)
    st.download_button("⬇️ Descargar Soluciones Excel", data=to_excel_bytes(sol_df), file_name="soluciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Recetas

def section_recetas():
    st.subheader("📖 Recetas de Medios")
    if not recipes:
        st.info("No se encontró archivo de recetas.")
    else:
        sel = st.selectbox("Selecciona medio:", list(recipes.keys()))
        dfm = recipes[sel]
        st.dataframe(dfm)
        buf = BytesIO()
        dfm.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ Descargar Receta Excel", data=buf.getvalue(), file_name=f"receta_{sel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Bajas Inventario

def section_bajas():
    st.subheader("⚠️ Dar de baja Inventarios")
    tipo = st.radio("Tipo de baja:", ["Medios","Soluciones"])
    if tipo == "Medios":
        lote = st.selectbox("Lote:", inv_df['Código'].tolist())
        baja_ct = st.number_input("Frascos a dar de baja:", min_value=1)
        mot = st.text_input("Motivo consum
