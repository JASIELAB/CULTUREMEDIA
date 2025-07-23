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
        from PIL import Image as PILImage
        logo = PILImage.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar logo: {e}")
else:
    st.warning(f"Logo '{logo_path}' no encontrado.")

# --- Helpers de QR y Etiquetas ---
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
            th = font.getsize(line)[1]
        y += th + 2
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Archivos de datos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = [
    "Código", "Año", "Receta", "Solución", "Equipo", "Semana", "Día", "Preparación",
    "frascos", "pH_Ajustado", "pH_Final", "CE_Final",
    "Litros_preparar", "Dosificar_por_frasco", "Fecha"
]
sol_cols = ["Fecha", "Cantidad", "Código_Solución", "Responsable", "Regulador", "Observaciones"]
hist_cols = ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"]

# --- Funciones de carga / guardado ---
def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]


def save_df(path, df):
    df.to_csv(path, index=False)

# --- Carga inicial ---
inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

# --- Cargar recetas desde Excel ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if not df.empty:
            sub = df.iloc[:, :3].dropna(how='all').copy()
            sub.columns = ["Componente", "Fórmula", "Concentración"]
            recipes[sheet] = sub

# --- UI principal ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

menu = [
    ("Registrar Lote", "📋"), ("Consultar Stock", "📦"), ("Inventario Completo", "🔍"),
    ("Incubación", "⏱"), ("Baja Inventario", "⚠️"), ("Retorno Medio Nutritivo", "🔄"),
    ("Soluciones Stock", "🧪"), ("Recetas de Medios", "📖"), ("Imprimir Etiquetas", "🖨"),
    ("Planning", "📅"), ("Stock Reactivos", "🔬")
]
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
cols = st.columns(4)
for i, (lbl, icn) in enumerate(menu):
    if cols[i % 4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# ---------------------------
# Sección: Registrar Lote
# ---------------------------
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo", ["Preparadora Alpha", "Preparadora Beta"])
    semana = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    dia = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #", 1, 100)
    frascos = st.number_input("Frascos", 1, 999, value=1)
    ph_aj = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros = st.number_input(
        "Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f"
    )
    dosif = st.number_input(
        "Dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f"
    )
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [
            code, year, receta, solucion, equipo, semana, dia, prep,
            frascos, ph_aj, ph_fin, ce, litros, dosif,
            date.today().isoformat()
        ]
        save_df(INV_FILE, inv_df)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(), "Entrada", code,
            frascos, f"Equipo: {equipo}"
        ]
        save_df(HIST_FILE, mov_df)
        st.success(f"Lote {code} registrado.")

# ---------------------------
# Sección: Consultar Stock / Editar
# ---------------------------
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button(
        "Descargar Inventario (CSV)",
        inv_df.to_csv(index=False).encode('utf-8'),
        file_name="inventario_medios.csv"
    )
    st.markdown("---")
    st.subheader("✏️ Editar Lote")
    sel = st.selectbox("Selecciona lote a editar", inv_df['Código'])
    if sel:
        idx = inv_df[inv_df['Código'] == sel].index[0]
        e_year = st.number_input("Año", 2000, 2100, value=int(inv_df.at[idx, 'Año']))
        e_receta = st.selectbox(
            "Receta", list(recipes.keys()),
            index=list(recipes.keys()).index(inv_df.at[idx, 'Receta'])
        )
        e_sol = st.text_input("Solución stock", value=inv_df.at[idx, 'Solución'])
        e_equip = st.selectbox(
            "Equipo", ["Preparadora Alpha","Preparadora Beta"],
            index=["Preparadora Alpha","Preparadora Beta"].index(inv_df.at[idx, 'Equipo'])
        )
        e_sem = st.number_input("Semana", 1, 52, value=int(inv_df.at[idx, 'Semana']))
        e_dia = st.number_input("Día", 1, 7, value=int(inv_df.at[idx, 'Día']))
        e_prep = st.number_input(
            "Preparación #", 1, 100, value=int(inv_df.at[idx, 'Preparación'])
        )
        e_frascos = st.number_input(
            "Frascos", 1, 999, value=int(inv_df.at[idx, 'frascos'])
        )
        e_phaj = st.number_input(
            "pH Ajustado", 0.0, 14.0, format="%.1f",
            value=float(inv_df.at[idx, 'pH_Ajustado'])
        )
        e_phfin = st.number_input(
            "pH Final", 0.0, 14.0, format="%.1f",
            value=float(inv_df.at[idx, 'pH_Final'])
        )
        e_ce = st.number_input(
            "CE Final", 0.0, 20.0, format="%.2f",
            value=float(inv_df.at[idx, 'CE_Final'])
        )
        e_lit = st.number_input(
            "Litros a preparar", 0.0, 100.0, format="%.2f",
            value=float(inv_df.at[idx, 'Litros_preparar'])
        )
        e_dos = st.number_input(
            "Dosificar por frasco", 0.0, 10.0, format="%.2f",
            value=float(inv_df.at[idx, 'Dosificar_por_frasco'])
        )
        e_fecha = st.date_input(
            "Fecha",
            value=pd.to_datetime(inv_df.at[idx, 'Fecha']).date()
        )
        if st.button("Guardar cambios"):
            inv_df.at[idx, 'Año'] = e_year
            inv_df.at[idx, 'Receta'] = e_receta
            inv_df.at[idx, 'Solución'] = e_sol
            inv_df.at[idx, 'Equipo'] = e_equip
            inv_df.at[idx, 'Semana'] = e_sem
            inv_df.at[idx, 'Día'] = e_dia
            inv_df.at[idx, 'Preparación'] = e_prep
            inv_df.at[idx, 'frascos'] = e_frascos
            inv_df.at[idx, 'pH_Ajustado'] = e_phaj
            inv_df.at[idx, 'pH_Final'] = e_phfin
            inv_df.at[idx, 'CE_Final'] = e_ce
            inv_df.at[idx, 'Litros_preparar'] = e_lit
            inv_df.at[idx, 'Dosificar_por_frasco'] = e_dos
            inv_df.at[idx, 'Fecha'] = e_fecha.isoformat()
            save_df(INV_FILE, inv_df)
            st.success("Lote actualizado correctamente.")
