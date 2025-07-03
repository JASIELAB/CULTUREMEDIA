import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return buf.getvalue()
def make_label_text(info, qr_bytes, size=(300,100)):
    from PIL import Image, ImageDraw, ImageFont
    w,h=size; img=Image.new("RGB",(w,h),"white"); d=ImageDraw.Draw(img)
    try: f=ImageFont.truetype("arial.ttf",12)
    except: f=ImageFont.load_default()
    y=5
    for line in info: d.text((5,y),line,fill="black",font=f); y+=14
    qr=Image.open(BytesIO(qr_bytes)).resize((60,60)); img.paste(qr,(w-70,(h-60)//2))
    return img

def df_to_excel_bytes(df):
    buf=BytesIO(); df.to_excel(buf,index=False); return buf.getvalue()

# Config
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
# Load data
INV_FILE, SOL_FILE, REC_FILE = "inventario_medios.csv", "soluciones_stock.csv", "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
inv_cols=["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
sol_cols=["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
import os
inv_df=pd.read_csv(INV_FILE) if os.path.exists(INV_FILE) else pd.DataFrame(columns=inv_cols)
sol_df=pd.read_csv(SOL_FILE) if os.path.exists(SOL_FILE) else pd.DataFrame(columns=sol_cols)
# Load recipes
recipes={}
if os.path.exists(REC_FILE):
    xls=pd.ExcelFile(REC_FILE)
    for sh in xls.sheet_names:
        df=xls.parse(sh)
        if df.shape[0]>9:
            sub=df.iloc[9:,:3].dropna(how='all').copy()
            sub.columns=["Componente","Fórmula","Concentración"]
            recipes[sh]=sub
# Menu
sections=["Registrar Lote","Consultar Stock","Inventario Completo","Incubación","Baja Inventario","Soluciones Stock","Recetas de Medios","Imprimir Etiquetas"]
choice=st.sidebar.radio("Selecciona sección:", sections)
st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")
# Registrar Lote
if choice=="Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año=st.number_input("Año",2000,2100,value=date.today().year)
    receta=st.selectbox("Receta",list(recipes.keys()))
    solucion=st.text_input("Solución stock")
    semana=st.number_input("Semana",1,52,value=int(date.today().strftime("%U")))
    día=st.number_input("Día",1,7,value=date.today().isoweekday())
    prep=st.number_input("Preparación #",1,100)
    frascos=st.number_input("Cantidad de frascos",1,999,value=1)
    ph_aj=st.number_input("pH ajustado",0.0,14.0,format="%.1f")
    ph_fin=st.number_input("pH final",0.0,14.0,format="%.1f")
    ce=st.number_input("CE final",0.0,20.0,format="%.2f")
    if st.button("Registrar lote"):
        code=f"{str(año)[2:]}{receta[:2]}Z{semana:02d}{día}-{prep}"
        inv_df.loc[len(inv_df)]=[code,año,receta,solucion,semana,día,prep,frascos,ph_aj,ph_fin,ce,date.today().isoformat()]
        inv_df.to_csv(INV_FILE,index=False)
        st.success(f"Lote {code} registrado.")
# Consultar Stock
elif choice=="Consultar Stock":
    st.header("📦 Inventario Medio")
    st.dataframe(inv_df.style.set_properties(**{"background-color":"white"}),use_container_width=True)
    st.download_button("⬇️ Inventario Excel",df_to_excel_bytes(inv_df),"inventario_medios.xlsx")
# Inventario Completo
elif choice=="Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df,use_container_width=True)
# Incubación
elif choice=="Incubación":
    st.header("⏱ Estado de incubación")
    df2=inv_df.copy()
    df2['Días']=(pd.to_datetime(date.today().isoformat())-pd.to_datetime(df2['Fecha'])).dt.days
    def clr(d): return '#ffcdd2' if d>28 else '#c8e6c9' if d>7 else '#fff9c4'
    styled=df2.style.apply(lambda r: [f"background-color:{clr(r['Días'])}"]*len(r),axis=1)
    st.dataframe(styled,use_container_width=True)
# Baja Inventario
elif choice=="Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    act=st.radio("Motivo baja:",["Consumo","Merma"])
    códigos=inv_df['Código'].tolist()+sol_df['Código_Solución'].tolist()
    sel=st.selectbox("Selecciona código",códigos)
    fecha=st.date_input("Fecha de salida")
    variedad=st.text_input("Variedad")
    if st.button("Aplicar baja"):
        if sel in inv_df['Código'].values:
            inv_df=inv_df[inv_df['Código']!=sel]
            inv_df.to_csv(INV_FILE,index=False)
        else:
            sol_df=sol_df[sol_df['Código_Solución']!=sel]
            sol_df.to_csv(SOL_FILE,index=False)
        st.success("Registro dado de baja.")
# Soluciones Stock
elif choice=="Soluciones Stock":
    st.header("🧪 Registro de soluciones stock")
    fecha=st.date_input("Fecha")
    cantidad=st.text_input("Cantidad")
    code_s=st.text_input("Código sol.")
    resp=st.text_input("Responsable")
    reg=st.text_input("Regulador")
    obs=st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)]=[fecha.isoformat(),cantidad,code_s,resp,reg,obs]
        sol_df.to_csv(SOL_FILE,index=False)
        st.success("Solución registrada.")
# Recetas de Medios
elif choice=="Recetas de Medios":
    st.header("📖 Recetas")
    sel=st.selectbox("Receta",list(recipes.keys()))
    st.dataframe(recipes[sel],use_container_width=True)
# Imprimir Etiquetas
elif choice=="Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    opts=inv_df['Código'].tolist()
    sel=st.multiselect("Selecciona lote(s)",opts)
    if st.button("Generar etiquetas") and sel:
        for code in sel:
            r=inv_df[inv_df['Código']==code].iloc[0]
            info=[f"Código: {code}",f"Año: {r['Año']}",f"Receta: {r['Receta']}",f"Sol: {r['Solución']}",f"Sem: {r['Semana']}",f"Día: {r['Día']}",f"Prep: {r['Preparación']}",f"Frascos: {r['Frascos']}"]
            img=make_label_text(info,make_qr(code),size=(300,100))
            st.image(img)
        st.info("Imprima con clic derecho o pida PDF.")
