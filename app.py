import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")

# Paleta rojo-blanco
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"
ACCENT_COLOR = "#D32F2F"

st.markdown(f"""
<style>
  .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
  .sidebar .sidebar-content {{ background-color: #FFFFFF; }}
  .stDownloadButton>button {{ background-color: {ACCENT_COLOR}; color: white; }}
  .stButton>button {{ background-color: {ACCENT_COLOR}; color: white; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos de datos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# Columnas
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]

# Carga inventario medios
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)
else:
    inv_df = pd.DataFrame(columns=inv_cols)

# Carga soluciones stock
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# Carga recetas
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


def make_label_text(info: list, qr_bytes: bytes, size=(300,100)) -> Image.Image:
    w,h = size
    img = Image.new("RGB", (w,h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
    y = 5
    for line in info:
        draw.text((5,y), line, fill="black", font=font)
        y += 14
    qr = Image.open(BytesIO(qr_bytes)).resize((60,60))
    img.paste(qr, (w-70, (h-60)//2))
    return img


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# --- Menú lateral ---
sections = [
    "Registrar Lote","Consultar Stock","Inventario Completo",
    "Incubación","Soluciones Stock","Recetas de Medios","Imprimir Etiquetas"
]
choice = st.sidebar.radio("Selecciona sección:", sections)

st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")

# Registrar Lote
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año = st.number_input("Año (ej. 2025)", min_value=2000, max_value=2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    semana = st.number_input("Semana", min_value=1, max_value=52, value=int(date.today().strftime("%U")))
    día = st.number_input("Día", min_value=1, max_value=7, value=date.today().isoweekday())
    prep = st.number_input("Preparación #", min_value=1, max_value=100)
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, value=1)
    ph_aj = st.number_input("pH ajustado", min_value=0.0, max_value=14.0, format="%.1f")
    ph_fin = st.number_input("pH final", min_value=0.0, max_value=14.0, format="%.1f")
    ce = st.number_input("CE final", min_value=0.0, max_value=20.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(año)[2:]}{receta[:2]}Z{str(semana).zfill(2)}{día}-{prep}"
        new = {"Código":code,"Año":año,"Receta":receta,"Solución":solucion,
               "Semana":semana,"Día":día,"Preparación":prep,"Frascos":frascos,
               "pH_Ajustado":ph_aj,"pH_Final":ph_fin,"CE_Final":ce,"Fecha":date.today().isoformat()}
        inv_df.loc[len(inv_df)] = new
        inv_df.to_csv(INV_FILE, index=False)
        st.success(f"Lote {code} registrado.")

# Consultar Stock
elif choice == "Consultar Stock":
    st.header("📦 Inventario Medio de Cultivo")
    st.dataframe(inv_df.style.set_properties(**{"background-color":"white"}), use_container_width=True)
    st.download_button("⬇️ Descargar Inventario Excel", df_to_excel_bytes(inv_df), "inventario_medios.xlsx")

# Inventario Completo
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)

# Incubación
elif choice == "Incubación":
    st.header("⏱ Estado de incubación")
    df2 = inv_df.copy()
    df2["Días"] = (pd.to_datetime(date.today().isoformat()) - pd.to_datetime(df2["Fecha"]))\
.dt.days
    def get_row_color(d):
        if d > 28:
            return "#ffcdd2"
        elif d > 7:
            return "#c8e6c9"
        else:
            return "#fff9c4"
    styled = df2.style.apply(lambda row: [f"background-color: {get_row_color(row['Días'])}"]*len(row), axis=1)
    st.dataframe(styled, use_container_width=True)

# Soluciones Stock
elif choice == "Soluciones Stock":
    st.header("🧪 Registro de soluciones stock")
    fecha = st.date_input("Fecha")
    cantidad = st.text_input("Cantidad (ej. 1 g)")
    code_s = st.text_input("Código solución stock")
    responsable = st.text_input("Responsable")
    regulador = st.text_input("Regulador de crecimiento")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        new2 = {"Fecha":fecha.isoformat(),"Cantidad":cantidad,"Código_Solución":code_s,
                "Responsable":responsable,"Regulador":regulador,"Observaciones":obs}
        sol_df.loc[len(sol_df)] = new2
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        qr_bytes = make_qr(code_s)
        info = [f"Código: {code_s}", f"Fecha: {fecha.isoformat()}", f"Cantidad: {cantidad}",
                f"Responsable: {responsable}", f"Regulador: {regulador}", f"Obs: {obs}"]
        lbl = make_label_text(info, qr_bytes, size=(300,100))
        st.image(lbl)

# Recetas de Medios
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios de Cultivo")
    sel = st.selectbox("Selecciona receta", list(recipes.keys()))
    st.dataframe(recipes[sel], use_container_width=True)

# Imprimir Etiquetas
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    options = inv_df["Código"].tolist()
    sel_codes = st.multiselect("Selecciona lote(s) para etiqueta", options)
    if st.button("Generar etiquetas") and sel_codes:
        imgs = []
        for code in sel_codes:
            row = inv_df[inv_df["Código"]==code].iloc[0]
            qr_b = make_qr(code)
            info = [f"Código: {code}", f"Año: {row['Año']}", f"Receta: {row['Receta']}",
                    f"Sol: {row['Solución']}", f"Sem: {row['Semana']}", f"Día: {row['Día']} Prep{row['Preparación']}",
                    f"Frascos: {row['Frascos']}", f"pH Aj: {row['pH_Ajustado']}", f"pH Fin: {row['pH_Final']}", f"CE: {row['CE_Final']}"]
            imgs.append(make_label_text(info, qr_b, size=(300,100)))
        for im in imgs:
            st.image(im)
        st.info("Descarga cada imagen con clic derecho o solicita PDF por implementar.")
