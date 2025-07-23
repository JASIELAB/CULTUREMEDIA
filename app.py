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
    from PIL import Image as PILImage
    try:
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
            th = draw.textsize(line, font=font)[1]
        y += th + 2
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Archivos de datos ---
INV_FILE    = "inventario_medios.csv"
SOL_FILE    = "soluciones_stock.csv"
HIST_FILE   = "movimientos.csv"
REC_FILE    = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols  = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascros","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols  = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

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
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- UI ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

# menú en grid 3x4
menu = [
    ("Registrar Lote","📋"),("Consultar Stock","📦"),("Inventario Completo","🔍"),("Incubación","⏱"),
    ("Baja Inventario","⚠️"),("Retorno Medio Nutritivo","🔄"),("Soluciones Stock","🧪"),("Recetas de Medios","📖"),
    ("Imprimir Etiquetas","🖨"),("Planning","📅"),("Stock Reactivos","🔬")
]
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
cols = st.columns(4)
for i, (lbl, icn) in enumerate(menu):
    if cols[i%4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# --- Secciones ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year    = st.number_input("Año", 2000,2100,value=date.today().year)
    receta  = st.selectbox("Receta", list(recipes.keys()))
    solucion= st.text_input("Solución stock")
    equipo  = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"])
    semana  = st.number_input("Semana",1,52,value=int(datetime.today().strftime('%U')))
    dia     = st.number_input("Día",1,7,value=datetime.today().isoweekday())
    prep    = st.number_input("Preparación #",1,100)
    frascros= st.number_input("frascros",1,999,value=1)
    ph_aj   = st.number_input("pH ajustado",0.0,14.0,format="%.1f")
    ph_fin  = st.number_input("pH final",0.0,14.0,format="%.1f")
    ce      = st.number_input("CE final",0.0,20.0,format="%.2f")
    litros  = st.number_input("Litros a preparar",0.0,100.0,value=1.0,format="%.2f")
    dosif   = st.number_input("Dosificar por frasco",0.0,10.0,value=0.0,format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [code,year,receta,solucion,equipo,semana,dia,prep,frascros,ph_aj,ph_fin,ce,litros,dosif,date.today().isoformat()]
        save_df(INV_FILE, inv_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Entrada",code,frascros,f"Equipo: {equipo}"]
        save_df(HIST_FILE, mov_df)
        st.success(f"Lote {code} registrado.")

elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df,use_container_width=True)
    st.download_button(
        "Descargar Inventario (CSV)",
        inv_df.to_csv(index=False).encode('utf-8'),
        file_name="inventario_medios.csv"
    )
    st.markdown("---")
    st.subheader("✏️ Editar Lote")
    sel = st.selectbox("Selecciona lote a editar", inv_df['Código'])
    if sel:
        idx = inv_df[inv_df['Código']==sel].index[0]
        e_year   = st.number_input("Año",2000,2100,value=int(inv_df.at[idx,'Año']))
        e_receta = st.selectbox("Receta", list(recipes.keys()), index=list(recipes.keys()).index(inv_df.at[idx,'Receta']))
        e_sol    = st.text_input("Solución stock", value=inv_df.at[idx,'Solución'])
        e_equip  = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"], index=["Preparadora Alpha","Preparadora Beta"].index(inv_df.at[idx,'Equipo']))
        e_sem    = st.number_input("Semana",1,52,value=int(inv_df.at[idx,'Semana']))
        e_dia    = st.number_input("Día",1,7,value=int(inv_df.at[idx,'Día']))
        e_prep   = st.number_input("Preparación #",1,100,value=int(inv_df.at[idx,'Preparación']))
        e_fras   = st.number_input("frascros",1,999,value=int(inv_df.at[idx,'frascros']))
        e_phaj   = st.number_input("pH Ajustado",0.0,14.0,format="%.1f",value=float(inv_df.at[idx,'pH_Ajustado']))
        e_phfin  = st.number_input("pH Final",0.0,14.0,format="%.1f",value=float(inv_df.at[idx,'pH_Final']))
        e_ce     = st.number_input("CE Final",0.0,20.0,format="%.2f",value=float(inv_df.at[idx,'CE_Final']))
        e_lit    = st.number_input("Litros a preparar",0.0,100.0,format="%.2f",value=float(inv_df.at[idx,'Litros_preparar']))
        e_dos    = st.number_input("Dosificar por frasco",0.0,10.0,format="%.2f",value=float(inv_df.at[idx,'Dosificar_por_frasco']))
        if st.button("Guardar cambios"):
            inv_df.at[idx,'Año']                 = e_year
            inv_df.at[idx,'Receta']              = e_receta
            inv_df.at[idx,'Solución']            = e_sol
            inv_df.at[idx,'Equipo']              = e_equip
            inv_df.at[idx,'Semana']              = e_sem
            inv_df.at[idx,'Día']                 = e_dia
            inv_df.at[idx,'Preparación']         = e_prep
            inv_df.at[idx,'frascros']            = e_fras
            inv_df.at[idx,'pH_Ajustado']         = e_phaj
            inv_df.at[idx,'pH_Final']            = e_phfin
            inv_df.at[idx,'CE_Final']            = e_ce
            inv_df.at[idx,'Litros_preparar']     = e_lit
            inv_df.at[idx,'Dosificar_por_frasco']= e_dos
            save_df(INV_FILE, inv_df)
            st.success("Lote actualizado correctamente.")

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
    sel    = st.selectbox("Selecciona código", inv_df['Código'])
    cantidad = st.number_input("Cantidad de frascros a dar de baja",1,999,value=1)
    tipo_merma = st.selectbox("Tipo de Merma", ["Contaminación","Ruptura","Evaporación","Otro"]) if motivo=="Merma" else ""
    if st.button("Aplicar baja"):
        det = f"Cantidad frascros: {cantidad}" + (f"; Merma: {tipo_merma}" if motivo=="Merma" else "")
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), f"Baja {motivo}", sel, cantidad, det]
        save_df(HIST_FILE, mov_df)
        idx = inv_df[inv_df['Código']==sel].index[0]
        inv_df.at[idx,'frascros'] = max(0, int(inv_df.at[idx,'frascros']) - cantidad)
        save_df(INV_FILE, inv_df)
        st.success(f"{motivo} aplicado a {sel}.")

elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel      = st.selectbox("Selecciona lote", inv_df['Código'])
    cant_ret = st.number_input("Cantidad de frascros a retornar",1,999,value=1)
    if st.button("Aplicar retorno"):
        idx = inv_df[inv_df['Código']==sel].index[0]
        inv_df.at[idx,'frascros'] = int(inv_df.at[idx,'frascros']) + cant_ret
        save_df(INV_FILE, inv_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Retorno", sel, cant_ret, ""]
        save_df(HIST_FILE, mov_df)
        st.success(f"Retorno de {cant_ret} frascros para {sel} aplicado.")

elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    f2   = st.date_input("Fecha", date.today())
    c2   = st.number_input("Cantidad", 0.0, format="%.2f")
    code2= st.text_input("Código Solución")
    resp = st.text_input("Responsable")
    reg  = st.text_input("Regulador")
    obs  = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [f2.isoformat(), c2, code2, resp, reg, obs]
        save_df(SOL_FILE, sol_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Stock Solución", code2, c2, f"Resp:{resp}"]
        save_df(HIST_FILE, mov_df)
        st.success(f"Solución {code2} registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)

elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    if recipes:
        rec_sel = st.selectbox("Elige receta", list(recipes.keys()))
        df_rec = recipes[rec_sel]
        st.dataframe(df_rec, use_container_width=True)
        csv = df_rec.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar receta (CSV)", csv, file_name=f"receta_{rec_sel}.csv")
    else:
        st.error(f"No encontré el archivo {REC_FILE}.")

elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    sel = st.selectbox("Selecciona lote", inv_df['Código'])
    if st.button("Generar etiqueta"):
        row = inv_df[inv_df['Código']==sel].iloc[0]
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
        st.download_button("Descargar etiqueta (PDF)", pdf, file_name=f"etiqueta_{sel}.pdf", mime="application/pdf")

elif choice == "Planning":
    st.header("📅 Planning")
    up = st.file_uploader("Sube tu Excel de Planning", type="xlsx")
    if up:
        dfp = pd.read_excel(up)
        dfp.columns = [c.lower() for c in dfp.columns]
        if {"variedad","plantas"} <= set(dfp.columns):
            rec_map = {"manila":"AR2","madeira":"AR6","maldiva":"AR5","zarzamora":"ZR-1"}
            dfp["receta"] = dfp["variedad"].str.lower().map(rec_map)
            dfp["frascros"] = (dfp["plantas"]/40).apply(lambda x: int(x) if x==int(x) else int(x)+1)
            st.dataframe(dfp, use_container_width=True)
            st.download_button("Descargar Planning (CSV)", dfp.to_csv(index=False).encode("utf-8"), file_name="planning.csv")
        else:
            st.error("Faltan columnas 'Variedad' o 'Plantas'.")

elif choice == "Stock Reactivos":
    st.header("🔬 Stock de Reactivos")
    st.info("Sube tu Excel (.xlsx) de inventario de reactivos.")
    up = st.file_uploader("Selecciona archivo", type=["xlsx"])
    if up:
        try:
            df_r = pd.read_excel(up)
            st.dataframe(df_r, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar: {e}")
