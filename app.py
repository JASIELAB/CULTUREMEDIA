import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
# Paleta rojo y blanco
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

# --- Menú lateral ---
with st.sidebar:
    st.title("🗭 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote","Consultar Stock","Inventario","Historial",
        "Soluciones Stock","Recetas","Baja de Inventario","Imprimir Etiquetas"
    ])

# --- Cabecera ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones ---

def section_registrar_lote():
    st.subheader("📋 Registrar Nuevo Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].fillna("").tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, value=1)
    ph_aj = st.number_input("pH ajustado", value=5.8, format="%.2f")
    ph_fin = st.number_input("pH final", value=5.8, format="%.2f")
    ce = st.number_input("CE final (mS/cm)", value=1.0, format="%.2f")
    if st.button("Registrar lote"):
        cod_base = f"{año}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(' ','')
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [cod_base, año, receta, solucion, semana, dia, prep, frascos, ph_aj, ph_fin, ce, fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado exitosamente.")


def section_consultar_stock():
    st.subheader("📦 Stock Actual")
    st.dataframe(inv_df)
    st.write("---")
    st.subheader("🔬 Inventario Soluciones Stock")
    st.dataframe(sol_df)
    st.download_button("⬇️ Descargar Stock Excel", data=to_excel_bytes(inv_df), file_name="stock_actual.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def section_inventario():
    st.subheader("📊 Inventario Completo")
    st.dataframe(inv_df)
    st.download_button("⬇️ Descargar Inventario Excel", data=to_excel_bytes(inv_df), file_name="inventario_completo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def section_historial():
    st.subheader("📚 Historial")
    if inv_df.empty:
        st.info("No hay registros.")
        return
    df = inv_df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    start = st.date_input("Desde", value=df['Fecha'].dt.date.min())
    end = st.date_input("Hasta", value=df['Fecha'].dt.date.max())
    filt = df[(df['Fecha'].dt.date >= start) & (df['Fecha'].dt.date <= end)]
    st.dataframe(filt)
    st.download_button("⬇️ Descargar Historial Excel", data=to_excel_bytes(filt), file_name="historial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


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


def section_recetas():
    st.subheader("📖 Recetas de Medios")
    if not recipes:
        st.info("No se encontró archivo de recetas.")
        return
    sel = st.selectbox("Selecciona medio:", list(recipes.keys()))
    st.dataframe(recipes[sel])


def section_baja_inventario():
    st.subheader("⚠️ Baja de Inventario")
    opt = st.radio("Ruta de baja:", ["Consumo","Merma"])
    lote = st.selectbox("Lote:", inv_df['Código'].tolist())
    fecha_salida = st.date_input("Fecha de salida")
    variedad = st.text_input("Variedad")
    cantidad = st.number_input("Cantidad de frascos", min_value=1, max_value=inv_df.loc[inv_df['Código']==lote,'Frascos'].iloc[0])
    if st.button("Aplicar baja"):
        idx = inv_df.index[inv_df['Código']==lote][0]
        inv_df.at[idx,'Frascos'] -= cantidad
        inv_df.to_csv(INV_FILE, index=False)
        st.success(f"Baja aplicada por {opt}: {cantidad} frascos de {variedad}.")


def section_imprimir_etiquetas():
    st.subheader("🖨️ Imprimir Etiquetas")
    if inv_df.empty:
        st.info("No hay lotes registrados.")
        return
    cod_base = st.selectbox("Selecciona lote:", inv_df['Código'].tolist())
    copies = st.number_input("Número de etiquetas a generar", min_value=1, value=1)
    if st.button("Generar PDF de etiquetas"):
        row = inv_df.loc[inv_df['Código']==cod_base].iloc[0]
        images = []
        for i in range(1, copies+1):
            cod_i = f"{cod_base}-{i}"
            info = [
                f"Código: {cod_i}",
                f"Año: {row['Año']}",
                f"Receta: {row['Receta']}",
                f"Frascos: {row['Frascos']}",
                f"pH ajustado: {row['pH_Ajustado']}",
                f"pH final: {row['pH_Final']}",
                f"CE: {row['CE_Final']}"
            ]
            qr_bytes = make_qr("\n".join(info))
            label_img = make_label(info, qr_bytes)
            images.append(label_img)
        pdf_buf = BytesIO()
        images[0].save(pdf_buf, format='PDF', save_all=True, append_images=images[1:])
        pdf_buf.seek(0)
        st.download_button("⬇️ Descargar etiquetas PDF", data=pdf_buf, file_name=f"etiquetas_{cod_base}.pdf", mime="application/pdf")

# --- Dispatcher ---
sections = {
    "Registrar Lote": section_registrar_lote,
    "Consultar Stock": section_consultar_stock,
    "Inventario": section_inventario,
    "Historial": section_historial,
    "Soluciones Stock": section_soluciones_stock,
    "Recetas": section_recetas,
    "Baja de Inventario": section_baja_inventario,
    "Imprimir Etiquetas": section_imprimir_etiquetas
}
sections.get(choice, lambda: None)()
