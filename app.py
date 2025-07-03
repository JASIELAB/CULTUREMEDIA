import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from streamlit_option_menu import option_menu

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#D32F2F"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    .option-menu {{ padding: 0; }}
    .nav-link {{ font-size: 14px; }}
    .reportview-container .main .block-container{{padding-top:1rem;}}
</style>
""", unsafe_allow_html=True)

# --- Archivos y DataFrames ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]

if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)[inv_cols]
else:
    inv_df = pd.DataFrame(columns=inv_cols)

if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)[sol_cols]
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Recetas de medios ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Funciones Auxiliares ---

def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def make_label_lines_medios(row: pd.Series) -> list:
    return [
        f"Código: {row['Código']}",
        f"Año: {row['Año']}",
        f"Receta: {row['Receta']}",
        f"Solución: {row['Solución']}",
        f"Semana: {row['Semana']}",
        f"Día: {row['Día']}  Prep: {row['Preparación']}",
        f"Frascos: {row['Frascos']}",
        f"pH ajustado: {row['pH_Ajustado']}",
        f"pH final: {row['pH_Final']}",
        f"CE final: {row['CE_Final']}"
    ]

def make_label_lines_stock(row: pd.Series) -> list:
    return [
        f"Código: {row['Código_Solución']}",
        f"Fecha: {row['Fecha']}",
        f"Cant: {row['Cantidad']}",
        f"Resp: {row['Responsable']}",
        f"Regul: {row['Regulador']}",
        f"Obs: {row['Observaciones']}"
    ]

def make_label_image(lines: list, qr_bytes: bytes, size=(300,100)) -> Image.Image:
    w,h = size
    label = Image.new("RGB", (w,h), "white")
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("arial.ttf",12)
    except:
        font = ImageFont.load_default()
    y = 5
    for line in lines:
        draw.text((5,y), line, fill="black", font=font)
        y += 12
    qr = Image.open(BytesIO(qr_bytes)).resize((80,80))
    label.paste(qr,(w-90,(h-80)//2))
    return label

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# --- Menú principal estilo grid ---
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=[
            "Stock Control","Entry Registration","Production","Culture Testing","Harvesting Bag","Activities",
            "Register Breaktimes","Planning","Sales","Media Production",
            "Production Control","Evaluations","Deliveries","Losses",
            "Basic Data","Media Management","Breeding"
        ],
        icons=[
            "clipboard-check","clipboard-plus","factory","microscope","truck-loading","list-task",
            "clock-history","calendar","bar-chart-line","beaker","bag-heart","people-fill",
            "box-seam","exclamation-triangle",
            "file-earmark-text","book","seedling"
        ],
        menu_icon="app-indicator",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding":"0!important","background-color":"#FFFFFF"},
            "icon": {"color":"#4CAF50","font-size":"16px"},
            "nav-link": {"font-size":"14px","text-align":"left","margin":"0px","--hover-color":"#E8F5E9"},
            "nav-link-selected": {"background-color":"#C8E6C9"}
        }
    )

st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")

# --- Secciones ---

if selected == "Stock Control":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df.style.set_properties(**{"background-color":"white"}), use_container_width=True)
    st.sidebar.download_button("⬇️ Descargar Inventario Excel", df_to_excel_bytes(inv_df), "inventario_medios.xlsx")

elif selected == "Entry Registration":
    st.header("📋 Registrar Lote")
    col1, col2, col3 = st.columns(3)
    with col1:
        año = st.number_input("Año (ej. 2025)", min_value=2000, max_value=2100, value=date.today().year)
        receta = st.selectbox("Receta", ["Selecciona"]+list(recipes.keys()))
        solucion = st.text_input("Solución stock")
    with col2:
        semana = st.number_input("Semana", min_value=1, max_value=52, value=int(date.today().isocalendar()[1]))
        dia = st.number_input("Día", min_value=1, max_value=7, value=date.today().isocalendar()[2])
        prep = st.number_input("Preparación", min_value=1, max_value=99, value=1)
    with col3:
        frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, value=1)
        ph_aj = st.number_input("pH ajustado", min_value=0.0, max_value=14.0, step=0.1, value=5.5)
        ph_fin = st.number_input("pH final", min_value=0.0, max_value=14.0, step=0.1, value=5.3)
        ce = st.number_input("CE final", min_value=0.0, max_value=20.0, step=0.1, value=4.0)
    if st.button("Registrar"):
        code = f"{str(año)[-2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        today = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [code,año,receta,solucion,semana,dia,prep,frascos,ph_aj,ph_fin,ce,today]
        inv_df.to_csv(INV_FILE,index=False)
        st.success("Lote registrado.")
        # Mostrar etiqueta
        qr = make_qr(code)
        label = make_label_image(make_label_lines_medios(inv_df.iloc[-1]), qr)
        st.image(label)
        # PDF para descargar
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawInlineImage(label, 50, 650, width=300, height=100)
        c.showPage(); c.save(); buf.seek(0)
        st.download_button("⬇️ Descargar Etiqueta PDF", buf, f"etq_{code}.pdf")

elif selected == "Production":
    st.header("🧑‍🔬 Producción (pendiente)")

elif selected == "Culture Testing":
    st.header("🔬 Test de Cultivo (pendiente)")

elif selected == "Harvesting Bag":
    st.header("📦 Harvesting Bag (pendiente)")

elif selected == "Activities":
    st.header("📋 Activities (pendiente)")

elif selected == "Register Breaktimes":
    st.header("⏱ Register Breaktimes (pendiente)")

elif selected == "Planning":
    st.header("📅 Planning (pendiente)")

elif selected == "Sales":
    st.header("💲 Sales (pendiente)")

elif selected == "Media Production":
    st.header("🥼 Media Production (pendiente)")

elif selected == "Production Control":
    st.header("📊 Production Control (pendiente)")

elif selected == "Evaluations":
    st.header("✅ Evaluations (pendiente)")

elif selected == "Deliveries":
    st.header("🚚 Deliveries (pendiente)")

elif selected == "Losses":
    st.header("❌ Losses (pendiente)")

elif selected == "Basic Data":
    st.header("📁 Basic Data (pendiente)")

elif selected == "Media Management":
    st.header("🌱 Media Management (pendiente)")

elif selected == "Breeding":
    st.header("🌳 Breeding (pendiente)")

elif selected == "Entry Registration":
    pass  # ya manejado arriba

elif selected == "Stock Control":
    pass

elif selected == "Culture Testing":
    pass

elif selected == "Production":
    pass

elif selected == "Harvesting Bag":
    pass

# Sección de Incubación
elif selected == "Evaluations":  # usando este slot para incubación
    st.header("⏳ Estado de incubación")
    if not inv_df.empty:
        df2 = inv_df.copy()
        df2["Días"] = (pd.to_datetime(date.today()) - pd.to_datetime(df2["Fecha"])).dt.days
        def color_row(d):
            if d > 28: return ['background-color: #FFCDD2']*len(df2.columns)  # rojo
            if d > 7:  return ['background-color: #C8E6C9']*len(df2.columns)  # verde
            return ['background-color: #FFF9C4']*len(df2.columns)               # amarillo
        st.dataframe(df2.style.apply(lambda x: color_row(x["Días"]), axis=1), use_container_width=True)
    else:
        st.info("No hay lotes registrados.")

# Soluciones Stock
elif selected == "Deliveries":  # usando Deliveries para soluciones stock
    st.header("🧪 Registro de Soluciones Stock")
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha = st.date_input("Fecha", value=date.today())
        cantidad = st.text_input("Cantidad (ej. 1 g)")
    with col2:
        cod_s = st.text_input("Código Solución")
        responsable = st.text_input("Responsable")
    with col3:
        regulador = st.text_input("Regulador de crecimiento")
        observ = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fecha.isoformat(),cantidad,cod_s,responsable,regulador,observ]
        sol_df.to_csv(SOL_FILE,index=False)
        st.success("Solución registrada.")
        qr2 = make_qr(cod_s)
        lbl2 = make_label_image(make_label_lines_stock(sol_df.iloc[-1]), qr2, size=(300,100))
        st.image(lbl2)
        buf2 = BytesIO()
        c2 = canvas.Canvas(buf2, pagesize=letter)
        c2.drawInlineImage(lbl2,50,650,width=300,height=100)
        c2.showPage(); c2.save(); buf2.seek(0)
        st.download_button("⬇️ Descargar Etiqueta Solución PDF", buf2, f"etq_sol_{cod_s}.pdf")
    st.subheader("Inventario Soluciones Stock")
    st.dataframe(sol_df, use_container_width=True)
    st.sidebar.download_button("⬇️ Descargar Soluciones Excel", df_to_excel_bytes(sol_df), "soluciones_stock.xlsx")

# Recetas de Medios
elif selected == "Media Management":
    st.header("📖 Recetas de Medios de Cultivo")
    if recipes:
        opt = st.selectbox("Selecciona receta", list(recipes.keys()))
        st.dataframe(recipes[opt], use_container_width=True)
    else:
        st.info("No se encontró el archivo de recetas.")

# Imprimir Etiquetas (PDF múltiple)
elif selected == "Production Control":
    st.header("🖨️ Imprimir Etiquetas Múltiples")
    if inv_df.empty:
        st.warning("No hay lotes para imprimir.")
    else:
        picks = st.multiselect("Selecciona lote(s) para etiqueta", inv_df["Código"].tolist())
        if st.button("Generar PDF etiquetas"):
            bufp = BytesIO()
            c3 = canvas.Canvas(bufp, pagesize=letter)
            y0 = 700
            for code in picks:
                row = inv_df[inv_df["Código"]==code].iloc[0]
                lines = make_label_lines_medios(row)
                qr = make_qr(code)
                lbl = make_label_image(lines, qr, size=(250,80))
                # Save PIL to temp buffer
                tmp = BytesIO()
                lbl.save(tmp, format="PNG"); tmp.seek(0)
                c3.drawInlineImage(tmp,50,y0,width=250,height=80)
                y0 -= 120
                if y0 < 100:
                    c3.showPage(); y0 = 700
            c3.save(); bufp.seek(0)
            st.download_button("⬇️ Descargar PDF etiquetas", bufp, "etiquetas_lotes.pdf")

else:
    st.info("Selección pendiente de implementar.")
