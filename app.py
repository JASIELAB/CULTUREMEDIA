import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import base64
import os

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
primary_color = "#007ACC"
accent_color = "#2ECC71"
bg_color = "#F5F9FC"
text_color = "#1C2833"

st.markdown(f"""
<style>
  .stApp {{background-color: {bg_color}; color: {text_color};}}
  div.stButton>button {{background-color: {primary_color}; color: white;}}
  div.stDownloadButton>button {{background-color: {accent_color}; color: white;}}
</style>
""", unsafe_allow_html=True)

# --- Rutas de archivos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
RECETAS_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Carga o inicialización de DataFrames ---
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE, parse_dates=["Fecha"] if "Fecha" in pd.read_csv(INV_FILE, nrows=0).columns else [])
else:
    inv_df = pd.DataFrame(columns=["Código","Año","Receta","Solución","Semana","Día","Preparación","Fecha"])

if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE, parse_dates=["Fecha"] if "Fecha" in pd.read_csv(SOL_FILE, nrows=0).columns else [])
else:
    sol_df = pd.DataFrame(columns=["Fecha","Cantidad","Código_Solución","Responsable","Observaciones"])

# --- Carga de recetas desde Excel ---
recipes = {}
if os.path.exists(RECETAS_FILE):
    xls = pd.ExcelFile(RECETAS_FILE)
    for sheet in xls.sheet_names:
        df_raw = xls.parse(sheet)
        if df_raw.shape[0] > 9:
            df2 = df_raw.iloc[9:,[0,1,2]].dropna(how='all')
            df2.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = df2

# --- Funciones auxiliares ---

def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def download_excel(df, filename):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return buf.getvalue()

# --- Sidebar de navegación ---
with st.sidebar:
    st.title("🗭 Menú")
    section = st.radio("Selecciona una sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario",
        "Historial",
        "Soluciones Stock",
        "Recetas"
    ])

# --- Encabezado ---
col1, col2, col3 = st.columns([1,6,1])
with col1:
    st.image("logo_blackberry.png", width=60)
with col2:
    st.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
with col3:
    st.empty()

st.markdown("---")

# --- Sección Registrar Lote ---
if section == "Registrar Lote":
    st.subheader("📋 Registrar Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].dropna().tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Preparación")
    frascos = st.number_input("Cantidad de etiquetas", min_value=1, value=1)
    if st.button("Registrar lote"):
        codigo = f"{año}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(' ','')
        fecha = datetime.now().strftime("%Y-%m-%d")
        inv_df.loc[len(inv_df)] = [codigo,año,receta,solucion,semana,dia,prep,fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado exitosamente.")
        info_lines = [f"Año: {año}", f"Semana: {semana}", f"Día: {dia}", f"Receta: {receta}", f"Solución: {solucion}", f"Preparación: {prep}"]
        qr_data = make_qr("\n".join(info_lines))
        st.image(qr_data, width=200)
        st.download_button("⬇️ Descargar etiqueta PNG", data=qr_data, file_name=f"etiqueta_{codigo}.png", mime="image/png")

# --- Sección Consultar Stock ---
elif section == "Consultar Stock":
    st.subheader("📦 Stock Actual")
    st.dataframe(inv_df)
    excel_data = download_excel(inv_df, 'stock.xlsx')
    st.download_button("⬇️ Descargar Stock Excel", data=excel_data, file_name="stock.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Inventario ---
elif section == "Inventario":
    st.subheader("📊 Inventario Completo")
    st.dataframe(inv_df)
    excel_data = download_excel(inv_df, 'inventario.xlsx')
    st.download_button("⬇️ Descargar Inventario", data=excel_data, file_name="inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Historial ---
elif section == "Historial":
    st.subheader("📚 Historial")
    if inv_df.empty:
        st.info("No hay registros.")
    else:
        df = inv_df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        min_date = df['Fecha'].min().date()
        max_date = df['Fecha'].max().date()
        start = st.date_input("Desde", min_value=min_date, max_value=max_date, value=min_date)
        end = st.date_input("Hasta", min_value=min_date, max_value=max_date, value=max_date)
        mask = (df['Fecha'].dt.date >= start) & (df['Fecha'].dt.date <= end)
        df_f = df.loc[mask]
        st.dataframe(df_f)
        excel_data = download_excel(df_f, 'historial.xlsx')
        st.download_button("⬇️ Descargar Historial", data=excel_data, file_name="historial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Soluciones Stock ---
elif section == "Soluciones Stock":
    st.subheader("🧪 Soluciones Stock")
    f = st.date_input("Fecha de preparación", value=datetime.today())
    cant = st.text_input("Cantidad (g/mL)")
    cods = st.text_input("Código de solución")
    resp = st.text_input("Responsable")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [f.strftime("%Y-%m-%d"), cant, cods, resp, obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        qr_data = make_qr(f"Código: {cods}\nFecha: {f}\nCant: {cant}\nResp: {resp}")
        st.image(qr_data, width=200)
        st.download_button("⬇️ Descargar etiqueta PNG", data=qr_data, file_name=f"sol_{cods}.png", mime="image/png")
    st.markdown("---")
    st.dataframe(sol_df)
    excel_data = download_excel(sol_df, 'soluciones.xlsx')
    st.download_button("⬇️ Descargar Soluciones", data=excel_data, file_name="soluciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Recetas ---
elif section == "Recetas":
    st.subheader("📖 Recetas de Medios")
    if not recipes:
        st.info("No se encontró el archivo de recetas.")
    else:
        sel = st.selectbox("Selecciona medio", list(recipes.keys()))
        dfm = recipes.get(sel, pd.DataFrame())
        st.dataframe(dfm)
        if not dfm.empty:
            buf = BytesIO(); dfm.to_excel(buf, index=False); buf.seek(0)
            st.download_button("⬇️ Descargar receta Excel", data=buf.getvalue(), file_name=f"receta_{sel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
