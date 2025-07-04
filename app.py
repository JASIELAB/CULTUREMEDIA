import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Page Config ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")

# --- Logo en esquina superior izquierda ---
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar el logo: {e}")
else:
    st.warning(f"Logo '{logo_path}' no encontrado en el directorio de la aplicación.")

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
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            _, text_height = font.getsize(line)
        y += text_height + 2
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Files and Columns ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
inv_cols = [
    "Código", "Año", "Receta", "Solución", "Equipo", "Semana", "Día", "Preparación",
    "Frascros", "pH_Ajustado", "pH_Final", "CE_Final",
    "Litros_preparar", "Dosificar_por_frasco", "Fecha"
]
sol_cols = ["Fecha", "Cantidad", "Código_Solución", "Responsable", "Regulador", "Observaciones"]
hist_cols = ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"]

# --- Load Data ---
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

# --- Load Recipes ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente", "Fórmula", "Concentración"]
            recipes[sheet] = sub

# --- UI ---
st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")
menu = [
    ("Registrar Lote", "📋"), ("Consultar Stock", "📦"), ("Inventario Completo", "🔍"),
    ("Incubación", "⏱"), ("Baja Inventario", "⚠️"), ("Retorno Medio Nutritivo", "🔄"),
    ("Soluciones Stock", "🧪"), ("Recetas de Medios", "📖"), ("Imprimir Etiquetas", "🖨"),
    ("Control del Sistema", "⚙️")
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for idx, (label, icon) in enumerate(menu):
    if cols[idx % 4].button(f"{icon}  {label}", key=label):
        st.session_state.choice = label
choice = st.session_state.choice
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo", ["Preparadora Alpha", "Preparadora Beta"])
    semana = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    día = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #", 1, 100)
    frascros = st.number_input("Cantidad de frascros", 1, 999, value=1)
    ph_aj = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros = st.number_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
    dosificar = st.number_input("Cantidad a dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(año)[2:]}{receta[:2]}Z{semana:02d}{día}-{prep}"
        inv_df.loc[len(inv_df)] = [code, año, receta, solucion, equipo, semana, día, prep,
                                    frascros, ph_aj, ph_fin, ce, litros, dosificar, date.today().isoformat()]
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Entrada", code, frascros, f"Equipo: {equipo}"]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Lote {code} registrado.")

# --- Baja Inventario ---
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo", ["Consumo", "Merma"] )
    códigos = inv_df['Código'].tolist() + sol_df['Código_Solución'].tolist()
    sel = st.selectbox("Selecciona código", códigos)
    fecha = st.date_input("Fecha de salida")
    variedad = st.text_input("Variedad")
    cantidad = st.number_input("Cantidad de frascros a dar de baja", min_value=1, value=1)
    if motivo == "Merma":
        tipo = st.selectbox("Tipo de Merma", ["Contaminación", "Ruptura", "Evaporación", "Falla eléctrica", "Interrupción del suministro de agua", "Otro"] )
    if st.button("Aplicar baja"):
        if sel in inv_df['Código'].tolist():
            inv_df.loc[inv_df['Código']==sel, 'Frascros'] -= cantidad
            if inv_df.loc[inv_df['Código']==sel, 'Frascros'].values[0] <= 0:
                inv_df.drop(inv_df[inv_df['Código']==sel].index, inplace=True)
            inv_df.to_csv(INV_FILE, index=False)
        else:
            sol_df['Cantidad'] = sol_df['Cantidad'].astype(int)
            sol_df.loc[sol_df['Código_Solución']==sel, 'Cantidad'] -= cantidad
            if sol_df.loc[sol_df['Código_Solución']==sel, 'Cantidad'].values[0] <= 0:
                sol_df.drop(sol_df[sol_df['Código_Solución']==sel].index, inplace=True)
            sol_df.to_csv(SOL_FILE, index=False)
        det = motivo + (f" ({tipo})" if motivo=="Merma" else "")
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Salida", sel, cantidad, det]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"{cantidad} frascros dados de baja por {det}.")

# --- remaining sections unchanged ---
