import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from fpdf import FPDF
import base64

# --- Paleta de colores personalizada ---
primary_color = "#007ACC"  # azul
accent_color = "#2ECC71"  # verde
bg_color = "#F5F9FC"
text_color = "#1C2833"

st.markdown(f"""
<style>
    .main {{
        background-color: {bg_color};
    }}
    .stApp {{
        color: {text_color};
    }}
    div.stButton > button:first-child {{
        background-color: {primary_color};
        color: white;
    }}
    div.stDownloadButton > button:first-child {{
        background-color: {accent_color};
        color: white;
    }}
    .stRadio > div {{
        background-color: {bg_color};
        color: {text_color};
    }}
</style>
""", unsafe_allow_html=True)

# --- Configuración de la página ---
st.set_page_config(
    page_title="Medios de Cultivo InVitro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Rutas de datos ---
INVENTARIO_CSV = "inventario_medios.csv"
SOLUCIONES_CSV = "soluciones_stock.csv"

# --- Carga o inicialización de DataFrames ---
if os.path.exists(INVENTARIO_CSV):
    inventario_df = pd.read_csv(INVENTARIO_CSV)
else:
    inventario_df = pd.DataFrame(columns=["Código","Año","Receta","Solución","Semana","Día","Preparación","Fecha_Registro"])

if os.path.exists(SOLUCIONES_CSV):
    soluciones_df = pd.read_csv(SOLUCIONES_CSV)
else:
    soluciones_df = pd.DataFrame(columns=["Fecha","Cantidad_Pesada","Código_Solución","Responsable","Observaciones"])

# --- Sidebar de navegación ---
with st.sidebar:
    st.title("🗭 Menú")
    menu = st.radio("Selecciona una sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario General",
        "Historial",
        "Soluciones Stock",
        "Recetas de medios"
    ])

# --- Encabezado ---
col1, col2, col3 = st.columns([1,6,1])
with col1:
    st.image("logo_blackberry.png", width=60)
with col2:
    st.markdown("<h1 style='text-align: center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
with col3:
    st.empty()
st.markdown("---")

# --- Funciones auxiliares ---
def generar_qr(texto):
    qr = qrcode.make(texto)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf)

def generar_etiqueta(info_lineas, codigo, titulo="🧪 MEDIO DE CULTIVO"):
    etiqueta = Image.new("RGB", (472,283), "white")
    draw = ImageDraw.Draw(etiqueta)
    try:
        font = ImageFont.truetype("arial.ttf",16)
    except:
        font = ImageFont.load_default()
    # logo
    try:
        logo = Image.open("logo_blackberry.png").resize((50,50))
        etiqueta.paste(logo,(400,230))
    except:
        pass
    # título
    draw.text((10,10), titulo, font=font, fill="black")
    # líneas de info
    y=40
    for ln in info_lineas:
        draw.text((10,y), ln, font=font, fill="black")
        y+=28
    # QR
    qr = generar_qr("\\n".join(info_lineas))
    qr=qr.resize((120,120))
    etiqueta.paste(qr,(330,20))
    # código abajo
    draw.text((10,250), f"Código: {codigo}", font=font, fill="black")
    buf=BytesIO()
    etiqueta.save(buf,format="PNG")
    buf.seek(0)
    return buf

def generar_excel(df):
    buf=BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf

# --- Sección: Registrar Lote ---
if menu=="Registrar Lote":
    st.subheader("📋 Registrar nuevo lote")
    anio = st.text_input("Año (ej. 2025)")
    rec_opts = list(recetas.keys()) if 'recetas' in globals() else ["MS","½MS","B5"]
    receta = st.selectbox("Receta", ["Selecciona"]+rec_opts)
    sol_opts = soluciones_df["Código_Solución"].dropna().unique().tolist()
    solucion = st.selectbox("Solución stock usada", ["Selecciona"]+sol_opts)
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de etiquetas", min_value=1, value=1)
    if st.button("Registrar lote"):
        codigo = f"{anio}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(" ","")
        fecha = datetime.today().strftime("%Y-%m-%d")
        nuevo = {"Código":codigo,"Año":anio,"Receta":receta,"Solución":solucion,
                 "Semana":semana,"Día":dia,"Preparación":prep,"Fecha_Registro":fecha}
        inventario_df=pd.concat([inventario_df,pd.DataFrame([nuevo])],ignore_index=True)
        inventario_df.to_csv(INVENTARIO_CSV,index=False)
        st.success("Lote registrado")
        # etiqueta
        info=[f"Año: {anio}",f"Semana: {semana}",f"Día: {dia}",f"Receta: {receta}",f"Solución: {solucion}",f"Prep: {prep}"]
        buf = generar_etiqueta(info,codigo)
        st.image(buf,caption="Etiqueta")
        st.download_button("Descargar PNG",buf,file_name=f"et_{codigo}.png",mime="image/png")

# --- Sección: Consultar Stock ---
elif menu=="Consultar Stock":
    st.subheader("📦 Stock actual")
    st.dataframe(inventario_df)
    st.download_button("Descargar Excel",generar_excel(inventario_df),"stock.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección: Inventario General ---
elif menu=="Inventario General":
    st.subheader("📊 Inventario General")
    st.dataframe(inventario_df)

# --- Sección: Historial ---
elif menu=="Historial":
    st.subheader("📚 Historial")
    df=inventario_df.copy()
    df["Fecha_Registro"]=pd.to_datetime(df["Fecha_Registro"])
    start=st.date_input("Desde",df["Fecha_Registro"].min())
    end=st.date_input("Hasta",df["Fecha_Registro"].max())
    fil=df[(df["Fecha_Registro"]>=pd.to_datetime(start))&(df["Fecha_Registro"]<=pd.to_datetime(end))]
    st.dataframe(fil)
    st.download_button("Descargar Historial",generar_excel(fil),"hist.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección: Soluciones Stock ---
elif menu=="Soluciones Stock":
    st.subheader("🧪 Soluciones Stock")
    fecha=st.date_input("Fecha",datetime.today())
    cant=st.text_input("Cantidad pesada")
    cod_sol=st.text_input("Código")
    resp=st.text_input("Responsable")
    obs=st.text_area("Observaciones")
    if st.button("Registrar Solución"):
        new={"Fecha":fecha.strftime("%Y-%m-%d"),"Cantidad_Pesada":cant,
             "Código_Solución":cod_sol,"Responsable":resp,"Observaciones":obs}
        soluciones_df=pd.concat([soluciones_df,pd.DataFrame([new])],ignore_index=True)
        soluciones_df.to_csv(SOLUCIONES_CSV,index=False)
        st.success("Solución registrada")
        # etiqueta sol
        info2=[f"Fecha: {new['Fecha']}",f"Cant: {cant}",f"Cod: {cod_sol}",f"Resp: {resp}"]
        buf2=generar_etiqueta(info2,cod_sol,"🧪 SOLUCIÓN STOCK")
        st.image(buf2,caption="Etiqueta Solución")
        st.download_button("Descargar PNG",buf2,file_name=f"sol_{cod_sol}.png",mime="image/png")
    st.markdown("---")
    st.dataframe(soluciones_df)
    st.download_button("Descargar Excel",generar_excel(soluciones_df),"sol.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección: Recetas de medios ---
elif menu=="Recetas de medios":
    st.subheader("📖 Recetas de medios")
    excel_file="RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
    wb=pd.ExcelFile(excel_file)
    sheet=st.selectbox("Elige medio",wb.sheet_names)
    dfm=wb.parse(sheet)
    dfm2=dfm.iloc[9:,[0,1,2]].dropna()
    dfm2.columns=["Componente","Fórmula","Conc."]
    st.dataframe(dfm2)
    st.download_button("Descargar Receta",BytesIO(dfm2.to_excel(index=False,engine="openpyxl")),f"receta_{sheet}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
