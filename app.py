import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
import os
from PIL import Image, ImageDraw, ImageFont

# --- Page Config ---
st.set_page_config("Medios Cultivo", layout="wide")

# --- Logo ---
logo_path = "plablue.png"
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.image(logo, width=120)
else:
    st.warning(f"Logo '{logo_path}' no encontrado.")

# --- Helpers ---
def make_qr(text: str) -> BytesIO:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

 def make_label(info_lines, qr_buf, size=(250,120)):
    w,h = size
    img = Image.new("RGB", (w,h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
    # draw text
    y = 5
    for line in info_lines:
        draw.text((5, y), line, fill="black", font=font)
        y += 14
    # paste QR
    qr_img = Image.open(qr_buf).resize((80,80))
    img.paste(qr_img, (w-85, (h-80)//2))
    return img

# --- Load / Persist Data ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]

inv_df = pd.read_csv(INV_FILE) if os.path.exists(INV_FILE) else pd.DataFrame(columns=inv_cols)
sol_df = pd.read_csv(SOL_FILE) if os.path.exists(SOL_FILE) else pd.DataFrame(columns=sol_cols)

# Load recipes
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:,:3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Grid Menu in Main Page ---
st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")
# define menu items as (label, icon, color)
menu = [
    ("Registrar Lote", "📋", "#AED581"),
    ("Consultar Stock", "📦", "#81D4FA"),
    ("Inventario Completo", "🔍", "#90CAF9"),
    ("Incubación", "⏱", "#FFF176"),
    ("Baja Inventario", "⚠️", "#FF8A65"),
    ("Soluciones Stock", "🧪", "#BA68C8"),
    ("Recetas de Medios", "📖", "#FFB74D"),
    ("Imprimir Etiquetas", "🖨", "#4DB6AC"),
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for idx, (label, icon, color) in enumerate(menu):
    c = cols[idx % 4]
    if c.button(f"{icon}  {label}", key=label, help=label):
        st.session_state.choice = label
choice = st.session_state.choice
st.markdown("---")

# --- Sections ---
# Registrar Lote
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año = st.number_input("Año",2000,2100,value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    semana = st.number_input("Semana",1,52,value=int(datetime.today().strftime('%U')))
    día = st.number_input("Día",1,7,value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #",1,100)
    frascos = st.number_input("Cantidad de frascos",1,999,value=1)
    ph_aj = st.number_input("pH ajustado",0.0,14.0,format="%.1f")
    ph_fin = st.number_input("pH final",0.0,14.0,format="%.1f")
    ce = st.number_input("CE final",0.0,20.0,format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(año)[2:]}{receta[:2]}Z{semana:02d}{día}-{prep}"
        inv_df.loc[len(inv_df)] = [code,año,receta,solucion,semana,día,prep,frascos,ph_aj,ph_fin,ce,date.today().isoformat()]
        inv_df.to_csv(INV_FILE,index=False)
        st.success(f"Lote {code} registrado.")
# Consultar Stock
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df.style.set_properties(**{"background-color":"white"}), use_container_width=True)
# Inventario Completo
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
# Incubación
elif choice == "Incubación":
    st.header("⏱ Estado de incubación")
    df2 = inv_df.copy()
    df2['Días'] = (pd.to_datetime(date.today()) - pd.to_datetime(df2['Fecha'])).dt.days
    def color_row(days): return 'background-color:#FFCDD2' if days>28 else 'background-color:#C8E6C9' if days>7 else 'background-color:#FFF9C4'
    st.dataframe(df2.style.apply(lambda r: [color_row(r['Días'])]*len(r), axis=1), use_container_width=True)
# Baja Inventario
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo:",["Consumo","Merma"])
    códigos = inv_df['Código'].tolist() + sol_df['Código_Solución'].tolist()
    sel = st.selectbox("Selecciona código", códigos)
    fecha = st.date_input("Fecha de salida")
    variedad = st.text_input("Variedad")
    if st.button("Aplicar baja"):
        if sel in inv_df['Código'].values:
            inv_df.drop(inv_df[inv_df['Código']==sel].index, inplace=True)
            inv_df.to_csv(INV_FILE,index=False)
        else:
            sol_df.drop(sol_df[sol_df['Código_Solución']==sel].index, inplace=True)
            sol_df.to_csv(SOL_FILE,index=False)
        st.success("Registro dado de baja.")
# Soluciones Stock
elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    f2 = st.date_input("Fecha")
    cant2 = st.text_input("Cantidad")
    code_s = st.text_input("Código Solución")
    resp = st.text_input("Responsable")
    reg = st.text_input("Regulador")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [f2.isoformat(),cant2,code_s,resp,reg,obs]
        sol_df.to_csv(SOL_FILE,index=False)
        st.success("Solución registrada.")
# Recetas de Medios
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    selr = st.selectbox("Receta", list(recipes.keys()))
    st.dataframe(recipes[selr], use_container_width=True)
# Imprimir Etiquetas
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    opts = inv_df['Código'].tolist()
    sels = st.multiselect("Selecciona lote(s)", opts)
    if st.button("Generar etiquetas") and sels:
        for code in sels:
            r = inv_df[inv_df['Código']==code].iloc[0]
            info = [f"Código: {code}", f"Año: {r['Año']}", f"Receta: {r['Receta']}", f"Sol.: {r['Solución']}", f"Sem: {r['Semana']}", f"Día: {r['Día']}", f"Prep: {r['Preparación']}", f"Frascos: {r['Frascos']}]
            buf = make_qr(code)
            lbl = make_label(info, buf)
            st.image(lbl)
        st.info("Usa clic derecho para guardar o imprimir PDF.")
