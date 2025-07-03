import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
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
    .stButton>button, .stDownloadButton>button {{ background-color: {PRIMARY_COLOR}; color: {ACCENT_COLOR}; }}
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
    width, height = 600, 200
    label = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    x_text, y_text = 20, 20
    line_h = 24
    for line in info:
        draw.text((x_text, y_text), line, fill="black", font=font)
        y_text += line_h
    qr_img = Image.open(BytesIO(qr_bytes)).resize((120, 120))
    qr_x = width - qr_img.width - 20
    qr_y = (height - qr_img.height) // 2
    label.paste(qr_img, (qr_x, qr_y))
    return label

# --- Menú lateral ---
st.sidebar.title("💬 Menú")
choice = st.sidebar.radio("Selecciona sección:", [
    "Registrar Lote", "Consultar Stock", "Inventario Completo", 
    "Incubación", "Soluciones Stock", "Recetas de Medios", 
    "Bajas Inventario","Imprimir Etiquetas"
])

st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.subheader("📋 Registrar nuevo lote")
    año = st.number_input("Año (ej. 2025)", min_value=2000, max_value=2100, value=date.today().year)
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    semana = st.number_input("Semana", min_value=1, max_value=52, value=date.today().isocalendar()[1])
    dia = st.number_input("Día", min_value=1, max_value=7, value=date.today().weekday()+1)
    prep = st.number_input("Preparación N°", min_value=1, max_value=100)
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, value=1)
    ph_aj = st.number_input("pH ajustado", min_value=0.0, max_value=14.0, step=0.1)
    ph_fin = st.number_input("pH final", min_value=0.0, max_value=14.0, step=0.1)
    ce = st.number_input("CE final (mS/cm)", min_value=0.0, step=0.01)
    if st.button("Registrar lote"):
        code = f"{str(año)[-2:]}{receta}{solucion}{semana}{dia}{prep}"
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [code,año,receta,solucion,semana,dia,prep,frascos,ph_aj,ph_fin,ce,fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("✅ Lote registrado")

# --- Consultar Stock (últimos lotes) ---
elif choice == "Consultar Stock":
    st.subheader("📦 Stock reciente")
    st.table(inv_df.tail(5))

# --- Inventario Completo ---
elif choice == "Inventario Completo":
    st.subheader("📊 Inventario completo")
    st.dataframe(inv_df)

# --- Incubación con colores ---
elif choice == "Incubación":
    st.subheader("⏱️ Estado de incubación")
    df2 = inv_df.copy()
    df2['Fecha_reg'] = pd.to_datetime(df2['Fecha'])
    df2['Días'] = (pd.Timestamp.today() - df2['Fecha_reg']).dt.days
    def color_row(days):
        if days>30: return 'background-color: #FFCDD2'
        if days<7: return 'background-color: #C8E6C9'
        return 'background-color: #FFF9C4'
    styled = df2.style.apply(lambda row: [color_row(row['Días']) for _ in row], axis=1)
    st.dataframe(styled)

# --- Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.subheader("🔬 Registro de soluciones stock")
    fecha_s = st.date_input("Fecha", value=date.today())
    cantidad = st.text_input("Cantidad (ej. 1 g)")
    resp = st.text_input("Responsable")
    regul = st.text_input("Regulador de crecimiento")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        code_s = f"Z{len(sol_df)+1}"
        sol_df.loc[len(sol_df)] = [fecha_s.isoformat(), cantidad, code_s, resp, regul, obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
    st.table(sol_df)

# --- Bajas Inventario ---
elif choice == "Bajas Inventario":
    st.subheader("⚠️ Bajas de inventario")
    type_ = st.radio("Tipo de baja:", ["Frascos Consumo/Merma", "Eliminar Lote"])
    if type_ == "Frascos Consumo/Merma":
        lote_sel = st.selectbox("Seleccionar lote:", inv_df['Código'])
        num = st.number_input("# Frascos a dar de baja", min_value=1, max_value=inv_df.loc[inv_df['Código']==lote_sel,'Frascos'].iloc[0])
        motivo = st.text_area("Motivo consumo/merma")
        if st.button("Aplicar baja medios"):
            idx = inv_df[inv_df['Código']==lote_sel].index[0]
            inv_df.at[idx,'Frascos'] -= num
            inv_df.to_csv(INV_FILE, index=False)
            st.success("Frascos descontados.")
    else:
        lote_del = st.multiselect("Eliminar lote(s):", inv_df['Código'])
        if st.button("Eliminar lote(s)"):
            inv_df.drop(inv_df[inv_df['Código'].isin(lote_del)].index, inplace=True)
            inv_df.to_csv(INV_FILE, index=False)
            st.success("Lote(s) eliminado(s)")

# --- Recetas de Medios ---
elif choice == "Recetas de Medios":
    st.subheader("📖 Recetas de medios")
    sel = st.selectbox("Selecciona receta:", list(recipes.keys()))
    if sel:
        st.dataframe(recipes[sel])

# --- Imprimir Etiquetas ---
elif choice == "Imprimir Etiquetas":
    st.subheader("🖨️ Imprimir Etiquetas")
    codes = st.multiselect("Selecciona lote(s) para etiqueta:", inv_df['Código'])
    labels = []
    for c in codes:
        row = inv_df[inv_df['Código']==c].iloc[0]
        info = [
            f"Código: {row['Código']}", f"Año: {row['Año']}", f"Receta: {row['Receta']}",
            f"Solución: {row['Solución']}", f"Semana: {row['Semana']}",
            f"Día: {row['Día']} Prep {row['Preparación']}", f"Frascos: {row['Frascos']}",
            f"pH aj: {row['pH_Ajustado']}", f"pH fin: {row['pH_Final']}", f"CE: {row['CE_Final']}"
        ]
        qr = make_qr(row['Código'])
        img = make_label(info, qr)
        labels.append(img)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), use_container_width=True)
    if labels:
        if st.button("Generar PDF etiquetas"):
            pdf_buf = BytesIO()
            labels[0].save(pdf_buf, "PDF", save_all=True, append_images=labels[1:])
            pdf_buf.seek(0)
            st.download_button("⬇️ Descargar PDF etiquetas", pdf_buf, file_name="etiquetas_lotes.pdf", mime="application/pdf")
