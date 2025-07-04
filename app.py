import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de página ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")

# --- Logo en esquina ---
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar logo: {e}")
else:
    st.warning(f"Logo '{logo_path}' no encontrado.")

# --- Helpers ---
def make_qr(text: str) -> BytesIO:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def make_label(info_lines, qr_buf, size=(250, 120)):
    w, h = size
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
    except IOError:
        font = ImageFont.load_default()
    y = 5
    for line in info_lines:
        draw.text((5, y), line, fill="black", font=font)
        try:
            bbox = draw.textbbox((5, y), line, font=font)
            th = bbox[3] - bbox[1]
        except AttributeError:
            th = draw.textsize(line, font=font)[1]
        y += th + 2
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Archivos y columnas ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

# Carga o inicializa DataFrames
def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]

inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

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

# --- Interfaz ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

menu = [
    ("Registrar Lote","📋"),("Consultar Stock","📦"),("Inventario Completo","🔍"),
    ("Incubación","⏱"),("Baja Inventario","⚠️"),("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"),("Stock Reactivos","🔬"),("Recetas de Medios","📖"),("Imprimir Etiquetas","🖨")
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for i, (lbl, icn) in enumerate(menu):
    if cols[i % 4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"])
    semana = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    dia = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #", 1, 100)
    frascos = st.number_input("Cantidad de frascos", 1, 999, value=1)
    ph_aj = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros = st.number_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
    dosif = st.number_input("Dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [code, year, receta, solucion, equipo, semana, dia, prep, frascos, ph_aj, ph_fin, ce, litros, dosif, date.today().isoformat()]
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Entrada", code, frascos, f"Equipo: {equipo}"]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Lote {code} registrado.")

# --- Consultar Stock ---
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button("Descargar Inventario (CSV)", inv_df.to_csv(index=False).encode("utf-8"), file_name="inventario_medios.csv")

# --- Inventario Completo ---
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)

# --- Incubación ---
elif choice == "Incubación":
    st.header("⏱ Incubación")
    df_inc = inv_df.copy()
    df_inc["Fecha"] = pd.to_datetime(df_inc["Fecha"])
    df_inc["Días incubación"] = (pd.to_datetime(date.today()) - df_inc["Fecha"]).dt.days
    def highlight_row(row):
        days = row["Días incubación"]
        if days < 6:
            return ["background-color: yellow"] * len(row)
        elif days <= 28:
            return ["background-color: lightgreen"] * len(row)
        else:
            return ["background-color: red"] * len(row)
    st.dataframe(df_inc.style.apply(highlight_row, axis=1).format({"Días incubación": "{:.0f}"}), use_container_width=True)

