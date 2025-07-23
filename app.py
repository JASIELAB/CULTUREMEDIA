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

# --- Columnas ---
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

# --- Carga inicial de datos ---
inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

# --- Cargar recetas embebidas ---
recipes = {}
if os.path.exists(REC_FILE):
    try:
        xls0 = pd.ExcelFile(REC_FILE)
        for sheet in xls0.sheet_names:
            df0 = xls0.parse(sheet)
            if not df0.empty:
                sub0 = df0.iloc[:, :3].dropna(how='all').copy()
                if sub0.shape[1] >= 3:
                    sub0.columns = ["Componente","Fórmula","Concentración"]
                    recipes[sheet] = sub0
    except Exception:
        recipes = {}

# --- UI Principal ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

# --- Menú ---
menu = [
    ("Registrar Lote","📋"),("Consultar Stock","📦"),("Inventario Completo","🔍"),
    ("Incubación","⏱"),("Baja Inventario","⚠️"),("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"),("Recetas de Medios","📖"),("Imprimir Etiquetas","🖨"),
    ("Planning","📅"),("Stock Reactivos","🔬")
]
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
cols = st.columns(4)
for i,(lbl,icn) in enumerate(menu):
    if cols[i%4].button(f"{icn}  {lbl}",key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year = st.number_input("Año",2000,2100,value=date.today().year)
    receta = st.selectbox("Receta",list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo",["Preparadora Alpha","Preparadora Beta"])
    semana = st.number_input("Semana",1,52,value=int(datetime.today().strftime('%U')))
    dia = st.number_input("Día",1,7,value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #",1,100)
    frascos = st.number_input("Frascos",1,999,value=1)
    ph_aj = st.number_input("pH ajustado",0.0,14.0,format="%.1f")
    ph_fin = st.number_input("pH final",0.0,14.0,format="%.1f")
    ce = st.number_input("CE final",0.0,20.0,format="%.2f")
    litros = st.number_input("Litros a preparar",0.0,100.0,value=1.0,format="%.2f")
    dosif = st.number_input("Dosificar por frasco",0.0,10.0,value=0.0,format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [code,year,receta,solucion,equipo,semana,dia,prep,frascos,ph_aj,ph_fin,ce,litros,dosif,date.today().isoformat()]
        save_df(INV_FILE,inv_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Entrada",code,frascos,f"Equipo: {equipo}"]
        save_df(HIST_FILE,mov_df)
        st.success(f"Lote {code} registrado.")

# --- Consultar y Editar Stock ---
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df,use_container_width=True)
    st.download_button("Descargar Inventario (CSV)",inv_df.to_csv(index=False).encode('utf-8'),file_name="inventario_medios.csv")
    st.markdown("---")
    st.subheader("✏️ Editar Lote")
    sel = st.selectbox("Selecciona lote a editar",inv_df['Código'])
    if sel:
        idx=inv_df[inv_df['Código']==sel].index[0]
        e_year=st.number_input("Año",2000,2100,value=int(inv_df.at[idx,'Año']))
        e_rec=st.selectbox("Receta",list(recipes.keys()),index=list(recipes.keys()).index(inv_df.at[idx,'Receta']))
        e_sol=st.text_input("Solución stock",value=inv_df.at[idx,'Solución'])
        e_equ=st.selectbox("Equipo",["Preparadora Alpha","Preparadora Beta"],index=["Preparadora Alpha","Preparadora Beta"].index(inv_df.at[idx,'Equipo']))
        e_sem=st.number_input("Semana",1,52,value=int(inv_df.at[idx,'Semana']))
        e_dia=st.number_input("Día",1,7,value=int(inv_df.at[idx,'Día']))
        e_prep=st.number_input("Preparación #",1,100,value=int(inv_df.at[idx,'Preparación']))
        e_fras=st.number_input("Frascos",1,999,value=int(inv_df.at[idx,'frascos']))
        e_phaj=st.number_input("pH Ajustado",0.0,14.0,format="%.1f",value=float(inv_df.at[idx,'pH_Ajustado']))
        e_phfin=st.number_input("pH Final",0.0,14.0,format="%.1f",value=float(inv_df.at[idx,'pH_Final']))
        e_ce=st.number_input("CE Final",0.0,20.0,format="%.2f",value=float(inv_df.at[idx,'CE_Final']))
        e_lit=st.number_input("Litros a preparar",0.0,100.0,format="%.2f",value=float(inv_df.at[idx,'Litros_preparar']))
        e_dos=st.number_input("Dosificar por frasco",0.0,10.0,format="%.2f",value=float(inv_df.at[idx,'Dosificar_por_frasco']))
        e_fecha=st.date_input("Fecha",value=pd.to_datetime(inv_df.at[idx,'Fecha']).date())
        if st.button("Guardar cambios"):
            inv_df.at[idx,'Año']=e_year
            inv_df.at[idx,'Receta']=e_rec
            inv_df.at[idx,'Solución']=e_sol
            inv_df.at[idx,'Equipo']=e_equ
            inv_df.at[idx,'Semana']=e_sem
            inv_df.at[idx,'Día']=e_dia
            inv_df.at[idx,'Preparación']=e_prep
            inv_df.at[idx,'frascos']=e_fras
            inv_df.at[idx,'pH_Ajustado']=e_phaj
            inv_df.at[idx,'pH_Final']=e_phfin
            inv_df.at[idx,'CE_Final']=e_ce
            inv_df.at[idx,'Litros_preparar']=e_lit
            inv_df.at[idx,'Dosificar_por_frasco']=e_dos
            inv_df.at[idx,'Fecha']=e_fecha.isoformat()
            save_df(INV_FILE,inv_df)
            st.success("Lote actualizado correctamente.")

# --- Inventario Completo ---
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df,use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df,use_container_width=True)

# --- Incubación ---
elif choice == "Incubación":
    st.header("⏱ Incubación")
    df_inc=inv_df.copy()
    df_inc['Fecha']=pd.to_datetime(df_inc['Fecha'])
    df_inc['Días incubación']=(pd.Timestamp(date.today())-df_inc['Fecha']).dt.days
    def color_days(r):
        d=r['Días incubación']
        return ['background-color: yellow']*len(r) if d<6 else (['background-color: lightgreen']*len(r) if d<=28 else ['background-color: red']*len(r))
    st.dataframe(df_inc.style.apply(color_days,axis=1),use_container_width=True)

# --- Baja Inventario ---
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo=st.radio("Motivo",["Consumo","Merma"])
    sel=st.selectbox("Selecciona código",inv_df['Código'])
    cantidad=st.number_input("Cantidad de frascos a dar de baja",1,999,value=1)
    tipo=st.selectbox("Tipo de Merma",["Contaminación","Ruptura","Evaporación","Otro"]) if motivo=="Merma" else None
    if st.button("Aplicar baja"):
        det=f"Cantidad: {cantidad} frascos"+(f"; Merma: {tipo}" if motivo=="Merma" else "")
        mov_df.loc[len(mov_df)]=[datetime.now().isoformat(),f"Baja {motivo}",sel,cantidad,det]
        save_df(HIST_FILE,mov_df)
        idx0=inv_df[inv_df['Código']==sel].index[0]
        inv_df.at[idx0,'frascos']=max(0,int(inv_df.at[idx0,'frascos'])-cantidad)
        save_df(INV_FILE,inv_df)
        st.success(f"Baja por {motivo} aplicada a {sel}.")

# --- Retorno Medio Nutritivo ---
elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel=st.selectbox("Selecciona lote",inv_df['Código'])
    cant_ret=st.number_input("Cantidad de frascos a retornar",1,999,value=1)
    if st.button("Aplicar retorno"):
        idx1=inv_df[inv_df['Código']==sel].index[0]
        inv_df.at[idx1,'frascos']=int(inv_df.at[idx1,'frascos'])+cant_ret
        save_df(INV_FILE,inv_df)
        mov_df.loc[len(mov_df)]=[datetime.now().isoformat(),"Retorno",sel,cant_ret,""]
        save_df(HIST_FILE,mov_df)
        st.success(f"Retorno de {cant_ret} frascos aplicado a {sel}.")

# --- Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    f2=st.date_input("Fecha",date.today())
    c2=st.number_input("Cantidad",0.0,format="%.2f")
    code2=st.text_input("Código Solución")
    resp=st.text_input("Responsable")
    reg=st.text_input("Regulador")
    obs=st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)]=[f2.isoformat(),c2,code2,resp,reg,obs]
        save_df(SOL_FILE,sol_df)
        mov_df.loc[len(mov_df)]=[datetime.now().isoformat(),"Stock Solución",code2,c2,f"Resp: {resp}"]
        save_df(HIST_FILE,mov_df)
        st.success(f"Solución {code2} registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df,use_container_width=True)

# --- Recetas de Medios ---
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    # Carga de recetas embebidas (archivo en carpeta)
    global_recipes = recipes.copy()
    # Subida dinámica para sobreescribir
    upload_rec = st.file_uploader("(Opcional) Sube tu archivo Excel de recetas", type=["xls","xlsx"], key="recetas_uploader")
    local_recipes = {}
    if upload_rec:
        try:
            xls_rec = pd.ExcelFile(upload_rec)
            for sheet in xls_rec.sheet_names:
                df_sh = xls_rec.parse(sheet)
                if not df_sh.empty:
                    sub = df_sh.iloc[:, :3].dropna(how='all').copy()
                    if sub.shape[1]>=3:
                        sub.columns=["Componente","Fórmula","Concentración"]
                        local_recipes[sheet]=sub
        except Exception as e:
            st.error(f"Error al leer recetas subidas: {e}")
    display = local_recipes if local_recipes else global_recipes
    if display:
        sel=st.selectbox("Elige receta",list(display.keys()),key="sel_receta")
        st.dataframe(display[sel],use_container_width=True)
        csv_r=display[sel].to_csv(index=False).encode('utf-8')
        st.download_button("Descargar receta",csv_r,file_name=f"receta_{sel}.csv")
    else:
        st.info("No hay recetas. Sube un Excel o verifica que exista el archivo en carpeta.")

# --- Imprimir Etiquetas ---
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    sel2=st.selectbox("Selecciona lote",inv_df['Código'],key="etq")
    if st.button("Generar etiqueta"):
        row=inv_df[inv_df['Código']==sel2].iloc[0]
        info=[
            f"Código: {row['Código']}",
            f"Receta: {row['Receta']}",
            f"Solución: {row['Solución']}",
            f"Fecha: {row['Fecha']}"
        ]
        buf=make_qr(sel2)
        lbl=make_label(info,buf)
        st.image(lbl)
        pdf=BytesIO()
        lbl.convert("RGB").save(pdf,format="PDF")
        pdf.seek(0)
        st.download_button("Descargar PDF",pdf,file_name=f"etiqueta_{sel2}.pdf",mime="application/pdf")

# --- Planning ---
elif choice == "Planning":
    st.header("📅 Planning")
    up = st.file_uploader("Sube tu Excel de planning",type="xlsx")
    if up:
        dfp=pd.read_excel(up)
        if {'variedad','plantas'}.issubset({c.lower() for c in dfp.columns}):
            dfp.columns=[c.lower() for c in dfp.columns]
            m={'manila':'AR2','madeira':'AR6','maldiva':'AR5','zarzamora':'ZR-1'}
            dfp['receta']=dfp['variedad'].str.lower().map(m)
            dfp['frascos']=(dfp['plantas']/40).apply(lambda x:int(x) if x==int(x) else int(x)+1)
            st.dataframe(dfp,use_container_width=True)
            st.download_button("Descargar Planning",dfp.to_csv(index=False).encode('utf-8'),file_name="planning.csv")
        else:
            st.error("Faltan columnas 'Variedad' o 'Plantas'.")

# --- Stock Reactivos ---
elif choice == "Stock Reactivos":
    st.header("🔬 Stock de Reactivos")
    up2=st.file_uploader("Sube tu Excel de reactivos",type="xlsx",key="reactivos_upl")
    if up2:
        try:
            df_r=pd.read_excel(up2)
            st.dataframe(df_r,use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar reactivos: {e}")
