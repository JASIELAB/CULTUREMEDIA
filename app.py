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

# --- Carga inicial de datos ---
inv_df = load_df(INV_FILE, inv_cols)
mov_df = load_df(MOV_FILE, mov_cols)
sol_df = load_df(SOL_FILE, sol_cols)

# --- Diccionario de recetas embebido en el código ---
recipes = {
    "MS": pd.DataFrame([
        {"Componente": "Agar",     "Fórmula": "C14H24O9",  "Concentración": "0.8%"},
        {"Componente": "Sacarosa","Fórmula": "C12H22O11", "Concentración": "3%"},
        {"Componente": "Ca(NO3)2","Fórmula": "Ca(NO3)2",   "Concentración": "100 mg/L"},
    ]),
    "AR2": pd.DataFrame([
        {"Componente": "Agar",    "Fórmula": "C14H24O9",  "Concentración": "0.7%"},
        {"Componente": "Maltosa", "Fórmula": "C12H22O11", "Concentración": "2%"},
        {"Componente": "KNO3",    "Fórmula": "KNO3",      "Concentración": "80 mg/L"},
    ]),
    "AR6": pd.DataFrame([
        {"Componente": "Agar",     "Fórmula": "C14H24O9", "Concentración": "0.9%"},
        {"Componente": "Glucosa",  "Fórmula": "C6H12O6",  "Concentración": "3.5%"},
        {"Componente": "NH4NO3",   "Fórmula": "NH4NO3",   "Concentración": "90 mg/L"},
    ]),
    "AR5": pd.DataFrame([
        {"Componente": "Agar",       "Fórmula": "C14H24O9", "Concentración": "1.0%"},
        {"Componente": "Sacárido X", "Fórmula": "C6H12O6",  "Concentración": "2.5%"},
        {"Componente": "MgSO4",      "Fórmula": "MgSO4",    "Concentración": "50 mg/L"},
    ]),
    "ZR-1": pd.DataFrame([
        {"Componente": "Agar",       "Fórmula": "C14H24O9", "Concentración": "0.85%"},
        {"Componente": "Dextrosa",   "Fórmula": "C6H12O6",  "Concentración": "3.2%"},
        {"Componente": "FeSO4",      "Fórmula": "FeSO4",    "Concentración": "20 mg/L"},
    ]),
}

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

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

# --- Menú en grid de 3 columnas por fila ---
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

for row in [menu_items[i:i+3] for i in range(0, len(menu_items), 3)]:
    cols = st.columns(3)
    for col, (label, icon) in zip(cols, row):
        if col.button(f"{icon}  {label}", key=label):
            st.session_state.choice = label

st.markdown("---")
choice = st.session_state.choice

# --- Secciones originales, sin modificar la lógica inicial ---

if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año      = st.number_input("Año", 2000,2100,value=date.today().year)
    receta   = st.text_input("Receta")
    solucion = st.text_input("Solución stock")
    equipo   = st.selectbox("Equipo", ["Alpha","Beta"])
    semana   = st.number_input("Semana",1,52,value=int(datetime.today().strftime("%U")))
    día      = st.number_input("Día",1,7,value=datetime.today().isoweekday())
    prep     = st.number_input("Preparación #",1,100)
    frascos  = st.number_input("frascos",1,999,value=1)
    ph_aj    = st.number_input("pH Ajustado",0.0,14.0,format="%.1f")
    ph_fin   = st.number_input("pH Final",0.0,14.0,format="%.1f")
    ce       = st.number_input("CE Final",0.0,20.0,format="%.2f")
    litros   = st.number_input("Litros a preparar",0.0,100.0,value=1.0,format="%.2f")
    dosif    = st.number_input("Dosificar por frasco",0.0,10.0,format="%.2f")
    if st.button("Registrar lote"):
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
    st.dataframe(inv_df, use_container_width=True)
    st.download_button(
        "Descargar Inventario (CSV)",
        inv_df.to_csv(index=False).encode("utf-8"),
        file_name="inventario_medios.csv"
    )

elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)

elif choice == "Incubación":
    st.header("⏱ Incubación")
    df = inv_df.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Días incubación"] = (pd.to_datetime(date.today()) - df["Fecha"]).dt.days
    def hl(r):
        d = r["Días incubación"]
        if d < 6:     return ["background-color: yellow"]*len(r)
        elif d <= 28: return ["background-color: lightgreen"]*len(r)
        else:         return ["background-color: red"]*len(r)
    st.dataframe(df.style.apply(hl, axis=1).format({"Días incubación":"{:.0f}"}), use_container_width=True)

elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo", ["Consumo","Merma"])
    sel    = st.selectbox("Selecciona código", inv_df["Código"])
    cantidad = st.number_input("Cantidad de frascos",1,999,value=1)
    if motivo == "Merma":
        tipo = st.selectbox("Tipo de Merma", ["Contaminación","Ruptura","Evaporación","Otro"])
    if st.button("Aplicar baja"):
        det = f"Cantidad frascos: {cantidad}" + (f"; Merma: {tipo}" if motivo=="Merma" else "")
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), f"Baja {motivo}", sel, cantidad, det]
        save_df(MOV_FILE, mov_df)
        idx = inv_df[inv_df["Código"]==sel].index[0]
        inv_df.at[idx,"frascos"] = max(0, int(inv_df.at[idx,"frascos"]) - cantidad)
        save_df(INV_FILE, inv_df)
        st.success(f"{motivo} aplicado a {sel}.")

elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel      = st.selectbox("Selecciona lote", inv_df["Código"])
    cant_ret = st.number_input("Cantidad de frascos a retornar",1,999,value=1)
    if st.button("Aplicar retorno"):
        idx = inv_df[inv_df["Código"]==sel].index[0]
        inv_df.at[idx,"frascos"] = int(inv_df.at[idx,"frascos"]) + cant_ret
        save_df(INV_FILE, inv_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Retorno",sel,cant_ret,""]
        save_df(MOV_FILE, mov_df)
        st.success(f"Retorno de {cant_ret} frascos para {sel} aplicado.")

elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    f2   = st.date_input("Fecha", date.today())
    c2   = st.number_input("Cantidad",0.0,format="%.2f")
    code2= st.text_input("Código Solución")
    resp = st.text_input("Responsable")
    reg  = st.text_input("Regulador")
    obs  = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [f2.isoformat(), c2, code2, resp, reg, obs]
        save_df(SOL_FILE, sol_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Stock Solución",code2,c2,f"Resp:{resp}"]
        save_df(MOV_FILE, mov_df)
        st.success(f"Solución {code2} registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)

elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    receta_sel = st.selectbox("Elige una receta", list(recipes.keys()))
    df_rec = recipes[receta_sel]
    st.dataframe(df_rec, use_container_width=True)
    st.download_button(
        "Descargar receta (CSV)",
        df_rec.to_csv(index=False).encode("utf-8"),
        file_name=f"receta_{receta_sel}.csv",
        mime="text/csv"
    )

elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    sel = st.selectbox("Selecciona lote", inv_df["Código"])
    if st.button("Generar etiqueta"):
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
        pdf = BytesIO()
        lbl.convert("RGB").save(pdf, format="PDF")
        pdf.seek(0)
        st.download_button(
            "Descargar etiqueta (PDF)",
            pdf,
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
            rec_map = {"manila":"AR2","madeira":"AR6","maldiva":"AR5","zarzamora":"ZR-1"}
            dfp["receta"] = dfp["variedad"].str.lower().map(rec_map)
            dfp["frascos"] = (dfp["plantas"]/40).apply(lambda x: int(x) if x==int(x) else int(x)+1)
            st.dataframe(dfp, use_container_width=True)
            st.download_button(
                "Descargar Planning (CSV)",
                dfp.to_csv(index=False).encode("utf-8"),
                file_name="planning.csv"
            )
        else:
            st.error("Faltan columnas 'Variedad' o 'Plantas'.")
