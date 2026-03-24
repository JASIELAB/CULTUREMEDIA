import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

st.set_page_config(page_title="Medios Cultivo", layout="wide")

# ------------------ FUNCIONES SEGURAS ------------------
def safe_int(value, default=1):
    try:
        if pd.isna(value) or value == '':
            return default
        return max(default, int(float(value)))
    except:
        return default

def safe_float(value, default=0.0):
    try:
        if pd.isna(value) or value == '':
            return default
        return float(value)
    except:
        return default

# ------------------ LOGO ------------------
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        st.image(Image.open(logo_path), width=120)
    except:
        pass

# ------------------ HELPERS ------------------
def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def make_label(info_lines, qr_buf, size=(250,120)):
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    y = 5
    for line in info_lines:
        draw.text((5,y), line, fill="black", font=font)
        y += 15
    qr = Image.open(qr_buf).resize((80,80))
    img.paste(qr,(size[0]-85,20))
    return img

# ------------------ ARCHIVOS ------------------
INV_FILE="inventario_medios.csv"
SOL_FILE="soluciones_stock.csv"
HIST_FILE="movimientos.csv"
REC_FILE="RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols=["Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
"frascos","pH_Ajustado","pH_Final","CE_Final","Litros_preparar","Dosificar_por_frasco","Fecha"]

sol_cols=["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols=["Timestamp","Tipo","Código","Cantidad","Detalles"]

# ------------------ DATA ------------------
def load_df(path,cols):
    if os.path.exists(path):
        df=pd.read_csv(path)
    else:
        df=pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c]=''
    return df[cols]

def save_df(path,df):
    df.to_csv(path,index=False)

inv_df=load_df(INV_FILE,inv_cols)
sol_df=load_df(SOL_FILE,sol_cols)
mov_df=load_df(HIST_FILE,hist_cols)

# ------------------ RECETAS ------------------
recipes={}
if os.path.exists(REC_FILE):
    try:
        xls=pd.ExcelFile(REC_FILE)
        for s in xls.sheet_names:
            df0=xls.parse(s)
            if not df0.empty:
                sub=df0.iloc[:,:3].dropna(how='all')
                if sub.shape[1]>=3:
                    sub.columns=["Componente","Fórmula","Concentración"]
                    recipes[s]=sub
    except:
        pass

# ------------------ UI ------------------
st.title("Control de Medios de Cultivo InVitRo")
menu=["Registrar Lote","Consultar Stock","Inventario Completo","Baja Inventario","Retorno","Soluciones","Recetas","Etiquetas"]

choice=st.selectbox("Menú",menu)

# ------------------ REGISTRAR ------------------
if choice=="Registrar Lote":
    year=st.number_input("Año",2000,2100,value=date.today().year)
    receta=st.selectbox("Receta",list(recipes.keys()) if recipes else ["General"])
    frascos=st.number_input("Frascos",1,999,value=1)

    if st.button("Registrar"):
        code=f"{str(year)[2:]}{receta[:2]}"
        inv_df.loc[len(inv_df)]=[code,year,receta,"","","","",1,frascos,0,0,0,0,0,date.today()]
        save_df(INV_FILE,inv_df)
        st.success("Lote registrado")

# ------------------ CONSULTAR ------------------
elif choice=="Consultar Stock":

    if inv_df.empty:
        st.warning("Sin datos")
        st.stop()

    sel=st.selectbox("Lote",inv_df["Código"])
    idx=inv_df[inv_df["Código"]==sel].index[0]

    e_fras=st.number_input("Frascos",1,999,value=safe_int(inv_df.at[idx,"frascos"],1))

    if st.button("Guardar"):
        inv_df.at[idx,"frascos"]=e_fras
        save_df(INV_FILE,inv_df)
        st.success("Actualizado")

# ------------------ INVENTARIO ------------------
elif choice=="Inventario Completo":
    st.dataframe(inv_df)

# ------------------ BAJA ------------------
elif choice=="Baja Inventario":

    if inv_df.empty:
        st.warning("Sin datos")
        st.stop()

    sel=st.selectbox("Código",inv_df["Código"])
    cant=st.number_input("Cantidad",1,999,value=1)

    if st.button("Aplicar"):
        idx=inv_df[inv_df["Código"]==sel].index[0]
        actual=safe_int(inv_df.at[idx,"frascos"],0)
        inv_df.at[idx,"frascos"]=max(0,actual-cant)
        save_df(INV_FILE,inv_df)
        st.success("Baja aplicada")

# ------------------ RETORNO ------------------
elif choice=="Retorno":

    sel=st.selectbox("Lote",inv_df["Código"])
    cant=st.number_input("Cantidad retorno",1,999,value=1)

    if st.button("Aplicar retorno"):
        idx=inv_df[inv_df["Código"]==sel].index[0]
        actual=safe_int(inv_df.at[idx,"frascos"],0)
        inv_df.at[idx,"frascos"]=actual+cant
        save_df(INV_FILE,inv_df)
        st.success("Retorno aplicado")

# ------------------ SOLUCIONES ------------------
elif choice=="Soluciones":

    f=st.date_input("Fecha")
    c=st.number_input("Cantidad",0.0)
    code=st.text_input("Código")
    resp=st.text_input("Responsable")

    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)]=[f,c,code,resp,"",""]
        save_df(SOL_FILE,sol_df)
        st.success("Registrado")

    st.dataframe(sol_df)

# ------------------ RECETAS ------------------
elif choice=="Recetas":

    if recipes:
        sel=st.selectbox("Receta",list(recipes.keys()))
        st.dataframe(recipes[sel])
    else:
        st.info("No hay recetas")

# ------------------ ETIQUETAS ------------------
elif choice=="Etiquetas":

    sel=st.selectbox("Lote",inv_df["Código"])

    if st.button("Generar"):
        row=inv_df[inv_df["Código"]==sel].iloc[0]
        info=[f"Código: {row['Código']}",f"Receta: {row['Receta']}"]
        qr=make_qr(sel)
        lbl=make_label(info,qr)
        st.image(lbl)
