import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de archivos CSV ---
INV_FILE  = "inventario_medios.csv"
MOV_FILE  = "movimientos.csv"
SOL_FILE  = "soluciones_stock.csv"

inv_cols  = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final","Litros_preparar",
    "Dosificar_por_frasco","Fecha"
]
mov_cols  = ["Timestamp","Tipo","Código","Cantidad","Detalles"]
sol_cols  = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def save_df(path, df):
    df.to_csv(path, index=False)

# --- Carga inicial ---
inv_df = load_df(INV_FILE, inv_cols)
mov_df = load_df(MOV_FILE, mov_cols)
sol_df = load_df(SOL_FILE, sol_cols)

# --- Helpers QR y etiquetas ---
def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf

def make_label(lines, qr_buf, size=(250,120)):
    w,h = size
    img = Image.new("RGB", (w,h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
    except IOError:
        font = ImageFont.load_default()
    y = 5
    for L in lines:
        draw.text((5,y), L, fill="black", font=font)
        _, th = draw.textsize(L, font=font)
        y += th + 2
    qr = Image.open(qr_buf).resize((80,80))
    img.paste(qr, (w-qr.width-5, (h-qr.height)//2))
    return img

# --- Interfaz ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

# --- Nuevo menú en grid ---
menu_items = [
    ("Registrar Lote","📋"),
    ("Consultar Stock","📦"),
    ("Inventario Completo","🔍"),
    ("Incubación","⏱"),
    ("Baja Inventario","⚠️"),
    ("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"),
    ("Recetas de Medios","📖"),
    ("Imprimir Etiquetas","🖨"),
    ("Planning","📅"),
]
if "choice" not in st.session_state:
    st.session_state.choice = menu_items[0][0]

# dibujar en filas de 3 columnas
for row in [menu_items[i:i+3] for i in range(0, len(menu_items), 3)]:
    cols = st.columns(3)
    for col, (lbl, icn) in zip(cols, row):
        if col.button(f"{icn}  {lbl}", key=lbl):
            st.session_state.choice = lbl
st.markdown("---")

# recoge la elección
choice = st.session_state.choice

# --- Lógica de cada sección (idéntica a la versión CSV) ---

if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año      = st.number_input("Año", 2000,2100,value=date.today().year)
    receta   = st.text_input("Receta")
    solucion = st.text_input("Solución stock")
    equipo   = st.selectbox("Equipo", ["Alpha","Beta"])
    semana   = st.number_input("Semana",1,52,value=int(datetime.today().strftime("%U")))
    día      = st.number_input("Día",1,7,value=datetime.today().isoweekday())
    prep     = st.number_input("Preparación #",1,100)
    frascos  = st.number_input("Frascos",1,999,value=1)
    ph_aj    = st.number_input("pH Ajustado",0.0,14.0,format="%.1f")
    ph_fin   = st.number_input("pH Final",0.0,14.0,format="%.1f")
    ce       = st.number_input("CE Final",0.0,20.0,format="%.2f")
    litros   = st.number_input("Litros a preparar",0.0,100.0,value=1.0,format="%.2f")
    dosif    = st.number_input("Dosificar por frasco",0.0,10.0,format="%.2f")
    if st.button("Registrar"):
        code = f"{str(año)[2:]}{receta[:2]}Z{semana:02d}{día}-{prep}"
        inv_df.loc[len(inv_df)] = [
            code,año,receta,solucion,equipo,semana,día,prep,
            frascos,ph_aj,ph_fin,ce,litros,dosif,date.today().isoformat()
        ]
        save_df(INV_FILE, inv_df)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),"Entrada",code,frascos,f"Equipo:{equipo}"
        ]
        save_df(MOV_FILE, mov_df)
        st.success(f"Lote {code} registrado.")

elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df,use_container_width=True)
    st.download_button("Descargar Inventario (CSV)",
                       inv_df.to_csv(index=False).encode(),
                       file_name="inventario_medios.csv")

elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df,use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df,use_container_width=True)

elif choice == "Incubación":
    st.header("⏱ Incubación")
    df = inv_df.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Días"] = (pd.to_datetime(date.today()) - df["Fecha"]).dt.days
    def color(r):
        d = r["Días"]
        if d<6:     c="background-color:yellow"
        elif d<=28: c="background-color:lightgreen"
        else:       c="background-color:red"
        return [c]*len(r)
    st.dataframe(df.style.apply(color,axis=1).format({"Días":"{:.0f}"}),
                 use_container_width=True)

elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo",["Consumo","Merma"])
    sel    = st.selectbox("Código",inv_df["Código"])
    cant   = st.number_input("Cantidad",1,999,value=1)
    if motivo=="Merma":
        tipo = st.selectbox("Tipo de Merma",
                            ["Contaminación","Ruptura","Evaporación","Otro"])
    if st.button("Aplicar Baja"):
        det = f"{motivo}({cant})" + (f" Merma:{tipo}" if motivo=="Merma" else "")
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),f"Baja {motivo}",sel,cant,det
        ]
        save_df(MOV_FILE,mov_df)
        idx = inv_df[inv_df["Código"]==sel].index[0]
        inv_df.at[idx,"frascos"] = max(0,int(inv_df.at[idx,"frascos"])-cant)
        save_df(INV_FILE,inv_df)
        st.success("Baja aplicada.")

elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel  = st.selectbox("Código",inv_df["Código"])
    cant = st.number_input("Cantidad",1,999,value=1)
    if st.button("Aplicar Retorno"):
        idx = inv_df[inv_df["Código"]==sel].index[0]
        inv_df.at[idx,"frascos"] = int(inv_df.at[idx,"frascos"])+cant
        save_df(INV_FILE,inv_df)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),"Retorno",sel,cant,""
        ]
        save_df(MOV_FILE,mov_df)
        st.success("Retorno aplicado.")

elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    f2   = st.date_input("Fecha",date.today())
    c2   = st.number_input("Cantidad",0.0,format="%.2f")
    csol = st.text_input("Código Solución")
    resp = st.text_input("Responsable")
    reg  = st.text_input("Regulador")
    obs  = st.text_area("Observaciones")
    if st.button("Registrar Solución"):
        sol_df.loc[len(sol_df)] = [
            f2.isoformat(),c2,csol,resp,reg,obs
        ]
        save_df(SOL_FILE,sol_df)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),"Solución",csol,c2,f"Resp:{resp}"
        ]
        save_df(MOV_FILE,mov_df)
        st.success("Solución registrada.")
    st.markdown("---")
    st.dataframe(sol_df,use_container_width=True)

elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    up = st.file_uploader("Sube tu Excel de recetas", type="xlsx")
    if up:
        xls = pd.ExcelFile(up)
        for s in xls.sheet_names:
            df0 = xls.parse(s)
            if df0.shape[0] > 9:
                sub = df0.iloc[9:,:3].dropna(how="all").copy()
                sub.columns = ["Componente","Fórmula","Concentración"]
                st.subheader(s)
                st.dataframe(sub,use_container_width=True)

elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    sel = st.selectbox("Código",inv_df["Código"])
    if st.button("Generar"):
        row = inv_df[inv_df["Código"]==sel].iloc[0]
        info = [
            f"Código: {row['Código']}",
            f"Receta: {row['Receta']}",
            f"Solución: {row['Solución']}",
            f"Fecha: {row['Fecha']}"
        ]
        buf = make_qr(sel)
        lbl = make_label(info, buf)
        st.image(lbl)
        pdf=BytesIO()
        lbl.convert("RGB").save(pdf,format="PDF")
        pdf.seek(0)
        st.download_button(
            "Descargar PDF", pdf,
            file_name=f"etiqueta_{sel}.pdf",
            mime="application/pdf"
        )

elif choice == "Planning":
    st.header("📅 Planning")
    up = st.file_uploader("Sube tu Excel de Planning", type="xlsx")
    if up:
        dfp = pd.read_excel(up)
        dfp.columns = [c.lower() for c in dfp.columns]
        if {"variedad","plantas"} <= set(dfp.columns):
            rec_map={"manila":"AR2","madeira":"AR6","maldiva":"AR5","zarzamora":"ZR-1"}
            dfp["receta"] = dfp["variedad"].str.lower().map(rec_map)
            dfp["frascos"] = (dfp["plantas"]/40).apply(lambda x:int(x) if x==int(x) else int(x)+1)
            st.dataframe(dfp,use_container_width=True)
            st.download_button(
                "Descargar CSV",
                dfp.to_csv(index=False).encode(),
                file_name="planning.csv"
            )
        else:
            st.error("Faltan columnas 'Variedad' o 'Plantas'.")
