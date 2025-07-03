import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, date
from PIL import Image
import os

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
primary_color = "#007ACC"
accent_color = "#2ECC71"
bg_color = "#F5F9FC"
text_color = "#1C2833"
st.markdown(f"""
<style>
  .stApp {{ background-color: {bg_color}; color: {text_color}; }}
  div.stButton>button {{ background-color: {primary_color}; color: white; }}
  div.stDownloadButton>button {{ background-color: {accent_color}; color: white; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos CSV/Excel ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Inicializar o cargar DataFrames ---
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)
    if 'Fecha_Registro' in inv_df.columns:
        inv_df.rename(columns={'Fecha_Registro':'Fecha'}, inplace=True)
    # Asegurar columnas correctas
    inv_df = inv_df.reindex(columns=inv_cols)
else:
    inv_df = pd.DataFrame(columns=inv_cols)
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Cargar recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:,[0,1,2]].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Funciones auxiliares ---
def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def to_excel_bytes(df):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Sidebar ---
with st.sidebar:
    st.title("🗭 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario",
        "Historial",
        "Soluciones Stock",
        "Recetas",
        "Bajas Inventario"
    ])

# --- Encabezado ---
cols = st.columns([1,6,1])
cols[0].image("logo_blackberry.png", width=60)
cols[1].markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
cols[2].image("logo_plantainvitro.png", width=80)
st.markdown("---")("---")

# --- Sección Registrar Lote ---
if choice == "Registrar Lote":
    st.subheader("📋 Registrar Nuevo Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].dropna().tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, value=1)
    ph_aj = st.number_input("pH ajustado", value=5.8, format="%.2f")
    ph_fin = st.number_input("pH final", value=5.8, format="%.2f")
    ce = st.number_input("CE final (mS/cm)", value=1.0, format="%.2f")
    if st.button("Registrar lote"):
        cod = f"{año}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(' ','')
        fecha = date.today().strftime("%Y-%m-%d")
        inv_df.loc[len(inv_df)] = [cod,año,receta,solucion,semana,dia,prep,frascos,ph_aj,ph_fin,ce,fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado exitosamente.")
        info = [
            f"Código: {cod}", f"Año: {año}", f"Receta: {receta}", f"Sol: {solucion}",
            f"Frascos: {frascos}", f"pH ajustado: {ph_aj}", f"pH final: {ph_fin}", f"CE final: {ce}"
        ]
        qr = make_qr("\n".join(info))
        st.image(qr, width=200)
        st.download_button("⬇️ Descargar etiqueta PNG", data=qr, file_name=f"etiqueta_{cod}.png", mime="image/png")

# --- Sección Consultar Stock ---
elif choice == "Consultar Stock":
    st.subheader("📦 Stock Actual")
    # Mostrar inventario actual sin ajustes
    st.dataframe(inv_df)
    # Descarga del inventario actual
    st.download_button(
        "⬇️ Descargar Stock Excel", 
        data=to_excel_bytes(inv_df), 
        file_name="stock_actual.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif choice == "Inventario":
    st.subheader("📊 Inventario Completo")
    st.dataframe(inv_df)
    st.download_button("⬇️ Descargar Inventario Excel", data=to_excel_bytes(inv_df), file_name="inventario.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Historial ---
elif choice == "Historial":
    st.subheader("📚 Historial")
    if inv_df.empty:
        st.info("No hay registros.")
    else:
        df = inv_df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        min_d, max_d = df['Fecha'].dt.date.min(), df['Fecha'].dt.date.max()
        start = st.date_input("Desde", value=min_d, min_value=min_d, max_value=max_d)
        end = st.date_input("Hasta", value=max_d, min_value=min_d, max_value=max_d)
        filt = df[(df['Fecha'].dt.date >= start) & (df['Fecha'].dt.date <= end)]
        st.dataframe(filt)
        st.download_button("⬇️ Descargar Historial Excel", data=to_excel_bytes(filt), file_name="historial.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.subheader("🧪 Soluciones Stock")
    fdate = st.date_input("Fecha preparación", value=date.today())
    qty = st.text_input("Cantidad (g/mL)")
    code_s = st.text_input("Código solución")
    who = st.text_input("Responsable")
    regulador = st.text_input("Tipo de regulador de crecimiento")
    obs2 = st.text_area("Observaciones")
    if st.button("Registrar solución", key='reg_sol'):
        sol_df.loc[len(sol_df)] = [fdate.strftime("%Y-%m-%d"), qty, code_s, who, regulador, obs2]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        info2 = [
            f"Código: {code_s}",
            f"Fecha: {fdate.strftime('%Y-%m-%d')}",
            f"Cantidad: {qty}",
            f"Responsable: {who}",
            f"Regulador: {regulador}"
        ]
        qr2 = make_qr("
".join(info2))
        st.image(qr2, width=200)
        st.download_button("⬇️ Descargar etiqueta PNG", data=qr2, file_name=f"sol_{code_s}.png", mime="image/png")
    st.markdown("---")
    st.subheader("📋 Registro de soluciones stock")("🧪 Soluciones Stock")
    fdate = st.date_input("Fecha preparación", value=date.today())
    qty = st.text_input("Cantidad (g/mL)")
    code_s = st.text_input("Código solución")
    who = st.text_input("Responsable")
    obs2 = st.text_area("Observaciones")
    if st.button("Registrar solución", key='reg_sol'):
        sol_df.loc[len(sol_df)] = [fdate.strftime("%Y-%m-%d"), qty, code_s, who, obs2]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        info2 = [
            f"Código: {code_s}",
            f"Fecha: {fdate.strftime('%Y-%m-%d')}",
            f"Cantidad: {qty}",
            f"Responsable: {who}"
        ]
        qr2 = make_qr("\n".join(info2))
        st.image(qr2, width=200)
        st.download_button("⬇️ Descargar etiqueta PNG", data=qr2, file_name=f"sol_{code_s}.png", mime="image/png")
    st.markdown("---")
    st.subheader("📋 Registro de soluciones stock")
    del_sol = st.multiselect("Selecciona solución(es) a eliminar:", sol_df['Código_Solución'].dropna().tolist())
    if del_sol and st.button("🗑️ Eliminar solución(es)", key='del_sol'):
        sol_df = sol_df[~sol_df['Código_Solución'].isin(del_sol)]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Soluciones eliminadas.")
    st.dataframe(sol_df)
    st.download_button("⬇️ Descargar Soluciones Excel", data=to_excel_bytes(sol_df), file_name="soluciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Recetas de Medios ---
elif choice == "Recetas":
    st.subheader("📖 Recetas de Medios")
    if not recipes:
        st.info("No se encontró archivo de recetas.")
    else:
        sel = st.selectbox("Selecciona medio:", list(recipes.keys()))
        dfm = recipes.get(sel, pd.DataFrame())
        st.dataframe(dfm)
        if not dfm.empty:
            buf = BytesIO()
            dfm.to_excel(buf, index=False)
            buf.seek(0)
            st.download_button("⬇️ Descargar Receta Excel", data=buf.getvalue(), file_name=f"receta_{sel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Sección Bajas Inventario ---
elif choice == "Bajas Inventario":
    st.subheader("⚠️ Dar de baja Inventarios")
    tipo_baja = st.radio("Tipo de baja:", ["Medios de Cultivo","Soluciones Stock"])
    if tipo_baja == "Medios de Cultivo":
        lote = st.selectbox("Lote:", inv_df['Código'].tolist(), key='baja_med')
        baja_ct = st.number_input("Frascos a dar de baja:", min_value=1, step=1, key='baja_ct')
        motivo = st.text_input("Motivo:", key='baja_mot')
        if st.button("Aplicar baja medios", key='btn_baja_med'):
            idx = inv_df.index[inv_df['Código']==lote]
            if not idx.empty:
                i = idx[0]
                if baja_ct <= inv_df.at[i,'Frascos']:
                    inv_df.at[i,'Frascos'] -= baja_ct
                    inv_df.to_csv(INV_FILE, index=False)
                    st.success(f"Baja de {baja_ct} frascos en {lote}.")
                else:
                    st.error("Cantidad excede stock.")
    else:
        sol = st.selectbox("Código solución:", sol_df['Código_Solución'].dropna().tolist(), key='baja_sol')
        if st.button("Eliminar solución stock", key='btn_baja_sol'):
            sol_df = sol_df[sol_df['Código_Solución'] != sol]
            sol_df.to_csv(SOL_FILE, index=False)
            st.success("Solución eliminada del inventario.")
