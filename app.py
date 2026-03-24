import streamlit as st
import pandas as pd
import qrcode
import os
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Medios Cultivo InVitRo", layout="wide")

# --- FUNCIONES DE SEGURIDAD (Previenen errores de conversión) ---
def safe_int(val, default=0):
    try:
        if pd.isna(val) or str(val).strip() == "": return default
        return int(float(val))
    except:
        return default

def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or str(val).strip() == "": return default
        return float(val)
    except:
        return default

# --- HELPERS DE QR Y ETIQUETAS ---
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
        font = ImageFont.try_load("DejaVuSans-Bold.ttf") or ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    y = 5
    for line in info_lines:
        draw.text((5, y), line, fill="black", font=font)
        y += 15
    
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- PERSISTENCIA DE DATOS ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = [
    "Código", "Año", "Receta", "Solución", "Equipo", "Semana", "Día", "Preparación",
    "frascos", "pH_Ajustado", "pH_Final", "CE_Final", "Litros_preparar", "Dosificar_por_frasco", "Fecha"
]
sol_cols = ["Fecha", "Cantidad", "Código_Solución", "Responsable", "Regulador", "Observaciones"]
hist_cols = ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"]

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df[cols]
    return pd.DataFrame(columns=cols)

def save_df(path, df):
    df.to_csv(path, index=False)

# Carga inicial
inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

# --- CARGA DE RECETAS ---
recipes = {}
if os.path.exists(REC_FILE):
    try:
        xls0 = pd.ExcelFile(REC_FILE)
        for sheet in xls0.sheet_names:
            df0 = xls0.parse(sheet)
            if not df0.empty:
                sub0 = df0.iloc[:, :3].dropna(how='all').copy()
                sub0.columns = ["Componente","Fórmula","Concentración"]
                recipes[sheet] = sub0
    except:
        recipes = {"Genérica": pd.DataFrame()}

# --- INTERFAZ ---
st.title("🧪 Control de Medios de Cultivo")

menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Baja Inventario","⚠️"),
    ("Retorno Medio","🔄"), ("Soluciones Stock","🧪"), ("Recetas","📖"), 
    ("Etiquetas","🖨"), ("Planning","📅")
]

if 'choice' not in st.session_state: st.session_state.choice = menu[0][0]

# Botones de navegación
cols_menu = st.columns(len(menu))
for i, (lbl, icn) in enumerate(menu):
    if cols_menu[i].button(f"{icn}\n{lbl}"):
        st.session_state.choice = lbl

st.divider()
choice = st.session_state.choice

# --- LÓGICA DE SECCIONES ---

if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("registro_form"):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("Año", 2000, 2100, value=date.today().year)
        receta = c2.selectbox("Receta", list(recipes.keys()))
        solucion = c3.text_input("Solución stock")
        
        c4, c5, c6 = st.columns(3)
        equipo = c4.selectbox("Equipo", ["Preparadora Alpha", "Preparadora Beta"])
        semana = c5.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
        dia = c6.number_input("Día", 1, 7, value=datetime.today().isoweekday())
        
        c7, c8, c9 = st.columns(3)
        prep = c7.number_input("Preparación #", 1, 100)
        frascos = c8.number_input("Frascos", 0, 999, value=1) # Mínimo 0 por seguridad
        litros = c9.number_input("Litros a preparar", 0.0, 100.0, value=1.0)
        
        submit = st.form_submit_button("Registrar lote")
        if submit:
            code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
            new_row = [code, year, receta, solucion, equipo, semana, dia, prep, frascos, 0.0, 0.0, 0.0, litros, 0.0, date.today().isoformat()]
            inv_df.loc[len(inv_df)] = new_row
            save_df(INV_FILE, inv_df)
            st.success(f"Lote {code} guardado.")

elif choice == "Consultar Stock":
    st.header("📦 Inventario Actual")
    st.dataframe(inv_df, use_container_width=True)
    
    st.subheader("✏️ Editar Lote Existente")
    sel = st.selectbox("Selecciona lote", [""] + list(inv_df['Código'].unique()))
    
    if sel != "":
        idx = inv_df[inv_df['Código'] == sel].index[0]
        
        with st.expander(f"Editando Lote: {sel}", expanded=True):
            col1, col2 = st.columns(2)
            # AQUÍ ESTÁ LA CORRECCIÓN DEL ERROR: Usamos safe_int y min_value=0
            e_fras = col1.number_input("Frascos", 0, 999, value=safe_int(inv_df.at[idx, 'frascos']))
            e_phaj = col2.number_input("pH Ajustado", 0.0, 14.0, value=safe_float(inv_df.at[idx, 'pH_Ajustado']))
            e_phfin = col1.number_input("pH Final", 0.0, 14.0, value=safe_float(inv_df.at[idx, 'pH_Final']))
            e_ce = col2.number_input("CE Final", 0.0, 20.0, value=safe_float(inv_df.at[idx, 'CE_Final']))
            
            if st.button("Actualizar Datos"):
                inv_df.at[idx, 'frascos'] = e_fras
                inv_df.at[idx, 'pH_Ajustado'] = e_phaj
                inv_df.at[idx, 'pH_Final'] = e_phfin
                inv_df.at[idx, 'CE_Final'] = e_ce
                save_df(INV_FILE, inv_df)
                st.success("Cambios aplicados.")
                st.rerun()

elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    sel = st.selectbox("Lote a descontar", inv_df['Código'])
    cant = st.number_input("Cantidad a quitar", 1, 500)
    motivo = st.selectbox("Motivo", ["Consumo", "Contaminación", "Merma"])
    
    if st.button("Procesar Baja"):
        idx = inv_df[inv_df['Código'] == sel].index[0]
        actual = safe_int(inv_df.at[idx, 'frascos'])
        if actual >= cant:
            inv_df.at[idx, 'frascos'] = actual - cant
            save_df(INV_FILE, inv_df)
            mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Baja", sel, cant, motivo]
            save_df(HIST_FILE, mov_df)
            st.warning(f"Se descontaron {cant} unidades de {sel}.")
        else:
            st.error("No hay suficiente stock.")

elif choice == "Retorno Medio":
    st.header("🔄 Retorno de Frascos")
    sel = st.selectbox("Lote", inv_df['Código'])
    cant = st.number_input("Cantidad a retornar", 1, 500)
    if st.button("Sumar al Stock"):
        idx = inv_df[inv_df['Código'] == sel].index[0]
        inv_df.at[idx, 'frascos'] = safe_int(inv_df.at[idx, 'frascos']) + cant
        save_df(INV_FILE, inv_df)
        st.success("Stock actualizado.")

elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    with st.form("sol_form"):
        c1, c2 = st.columns(2)
        f_sol = c1.date_input("Fecha", date.today())
        cod_sol = c2.text_input("Código Solución")
        cant_sol = c1.number_input("Litros/Cantidad", 0.0, 50.0)
        resp = c2.text_input("Responsable")
        if st.form_submit_button("Guardar Solución"):
            sol_df.loc[len(sol_df)] = [f_sol.isoformat(), cant_sol, cod_sol, resp, "", ""]
            save_df(SOL_FILE, sol_df)
            st.success("Solución registrada.")
    st.dataframe(sol_df)

elif choice == "Recetas":
    st.header("📖 Consulta de Recetas")
    if recipes:
        sel_r = st.selectbox("Selecciona Receta", list(recipes.keys()))
        st.table(recipes[sel_r])
    else:
        st.info("Sube el archivo Excel de recetas para visualizarlas.")

elif choice == "Etiquetas":
    st.header("🖨 Generador de Etiquetas")
    sel_e = st.selectbox("Lote para etiqueta", inv_df['Código'])
    if st.button("Generar"):
        row = inv_df[inv_df['Código'] == sel_e].iloc[0]
        info = [f"ID: {row['Código']}", f"Receta: {row['Receta']}", f"Fecha: {row['Fecha']}"]
        qr = make_qr(sel_e)
        img = make_label(info, qr)
        st.image(img, width=300)
        
        # Descarga
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.download_button("Descargar Etiqueta", buf.getvalue(), f"Etiqueta_{sel_e}.png", "image/png")

elif choice == "Planning":
    st.header("📅 Gestión de Planning")
    uploaded = st.file_uploader("Subir Excel de Planning", type="xlsx")
    if uploaded:
        dfp = pd.read_excel(uploaded)
        st.dataframe(dfp)
        st.info("Funcionalidad de procesamiento de planning lista para configurar.")
