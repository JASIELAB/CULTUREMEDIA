import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
# Colores de interfaz
PRIMARY_COLOR = "#D32F2F"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    div.stButton>button, div.stDownloadButton>button {{ background-color: {PRIMARY_COLOR}; color: white; }}
    .dataframe {{ background-color: white; }}
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

# Diseño de etiqueta inspirado en ejemplo de laboratorio
LABEL_W, LABEL_H = 400, 200  # px
QR_SIZE = 80

def make_label(info: dict, qr_bytes: bytes) -> Image.Image:
    label = Image.new("RGB", (LABEL_W, LABEL_H), "white")
    draw = ImageDraw.Draw(label)
    # Fuentes
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    # Título central (código)
    code = info.get("Código", "")
    w, h = draw.textsize(code, font=font_title)
    draw.text(((LABEL_W - w)//2, 10), code, fill="black", font=font_title)
    # Línea separadora
    draw.line([(10, 40), (LABEL_W - 10, 40)], fill="black", width=1)
    # Detalles a la izquierda
    y = 50
    for key in ["Año","Receta","Solución","Semana","Día","Preparación"]:
        val = info.get(key, "")
        text = f"{key}: {val}"
        draw.text((10, y), text, fill="black", font=font_text)
        y += 20
    # QR a la derecha
    qr_img = Image.open(BytesIO(qr_bytes)).resize((QR_SIZE, QR_SIZE))
    label.paste(qr_img, (LABEL_W - QR_SIZE - 10, LABEL_H - QR_SIZE - 10))
    return label

# Excel
from io import BytesIO

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Menú lateral ---
with st.sidebar:
    st.title("🗂 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote","Consultar Stock","Inventario Completo","Historial",
        "Soluciones Stock","Recetas de Medios","Bajas Inventario","Imprimir Etiquetas"
    ])

# --- Cabecera ---
col1, col2 = st.columns([1,6])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones ---
def section_registrar_lote():
    st.subheader("📋 Registrar Nuevo Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].fillna('').tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Preparación #")
    frascos = st.number_input("Cantidad frascos", min_value=1, max_value=999, value=1)
    ph_aj = st.number_input("pH ajustado", value=5.8, format="%.2f")
    ph_fin = st.number_input("pH final", value=5.8, format="%.2f")
    ce = st.number_input("CE final (mS/cm)", value=1.0, format="%.2f")
    if st.button("Registrar lote"):
        cod = f"{str(año)[-2:]}{receta[:2]}{solucion}{semana}{dia}{prep}"
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [cod,año,receta,solucion,semana,dia,prep,frascos,ph_aj,ph_fin,ce,fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado.")

def section_consultar_stock():
    st.subheader("📦 Stock Actual")
    st.dataframe(inv_df.style.set_properties(**{'background-color':'white'}))
    st.download_button("⬇️ Descargar Stock Excel", data=to_excel_bytes(inv_df), file_name="stock_actual.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def section_inventario():
    st.subheader("📊 Inventario Completo")
    st.dataframe(inv_df)
    st.download_button("⬇️ Descargar Inventario", data=to_excel_bytes(inv_df), file_name="inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def section_historial():
    st.subheader("📚 Historial")
    if inv_df.empty:
        st.info("Sin registros.")
        return
    df = inv_df.copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    start = st.date_input("Desde", df['Fecha'].dt.date.min())
    end = st.date_input("Hasta", df['Fecha'].dt.date.max())
    filt = df[(df['Fecha'].dt.date>=start)&(df['Fecha'].dt.date<=end)]
    st.dataframe(filt)
    st.download_button("⬇️ Descargar Historial", data=to_excel_bytes(filt), file_name="historial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def section_soluciones():
    st.subheader("🧪 Soluciones Stock")
    fdate = st.date_input("Fecha preparación", date.today())
    qty = st.text_input("Cantidad (g)")
    code_s = st.text_input("Código Solución")
    who = st.text_input("Responsable")
    reg = st.text_input("Regulador crecimiento")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fdate.isoformat(),qty,code_s,who,reg,obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario Soluciones")
    st.dataframe(sol_df)
    st.download_button("⬇️ Descargar Soluciones", data=to_excel_bytes(sol_df), file_name="soluciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def section_recetas():
    st.subheader("📖 Recetas de Medios")
    if not recipes: st.info("No hay archivo."); return
    sel = st.selectbox("Selecciona medio", list(recipes.keys()))
    st.dataframe(recipes[sel])

def section_bajas():
    st.subheader("⚠️ Baja de Inventario")
    tipo = st.radio("Tipo:", ["Consumo/Merma","Eliminar Lote"])
    if tipo=="Consumo/Merma":
        lote = st.selectbox("Lote", inv_df['Código'].tolist())
        n = st.number_input("# Frascos",1,inv_df['Frascos'].max())
        mot = st.text_input("Motivo")
        if st.button("Aplicar baja medios"):
            idx = inv_df.index[inv_df['Código']==lote][0]
            inv_df.at[idx,'Frascos'] -= n; inv_df.to_csv(INV_FILE,index=False)
            st.success("Merma registrada.")
    else:
        lote = st.selectbox("Lote a eliminar", inv_df['Código'].tolist())
        if st.button("Eliminar lote"):
            inv_df.drop(inv_df[inv_df['Código']==lote].index, inplace=True)
            inv_df.to_csv(INV_FILE,index=False)
            st.success("Lote eliminado.")

def section_imprimir():
    st.subheader("🖨️ Imprimir Etiquetas")
    sel = st.multiselect("Selecciona lote(s) para etiqueta", inv_df['Código'].tolist())
    if not sel: return
    if st.button("Generar PDF etiquetas"):
        buf_pdf = BytesIO()
        imgs = []
        for code in sel:
            row = inv_df[inv_df['Código']==code].iloc[0]
            info = {k:row[k] for k in ['Código','Año','Receta','Solución','Semana','Día','Preparación']}
            qr = make_qr(code)
            imgs.append(make_label(info,qr))
        imgs[0].save(buf_pdf, format='PDF', save_all=True, append_images=imgs[1:])
        buf_pdf.seek(0)
        st.download_button("⬇️ Descargar PDF", data=buf_pdf, file_name="etiquetas.pdf", mime="application/pdf")

sections = {
    "Registrar Lote": section_registrar_lote,
    "Consultar Stock": section_consultar_stock,
    "Inventario Completo": section_inventario,
    "Historial": section_historial,
    "Soluciones Stock": section_soluciones,
    "Recetas de Medios": section_recetas,
    "Bajas Inventario": section_bajas,
    "Imprimir Etiquetas": section_imprimir
}

sections[choice]()
