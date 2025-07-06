import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

st.set_page_config(page_title="Medios Cultivo", layout="wide")

# --- Logo en esquina ---
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar logo: {e}")
else:
    st.warning(f"Logo '{logo_path}' no encontrado.")

# --- Helpers ---
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

# --- Columnas estándar ---
inv_cols = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]

inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

def save_inventory(): inv_df.to_csv(INV_FILE, index=False)
def save_solutions(): sol_df.to_csv(SOL_FILE, index=False)
def save_history(): mov_df.to_csv(HIST_FILE, index=False)

# --- Botón para descargar inventario_medios.csv vacío ---
st.sidebar.markdown("### Utilidades")
df_vacio = pd.DataFrame(columns=inv_cols)
st.sidebar.download_button(
    "Descargar inventario_medios.csv vacío",
    df_vacio.to_csv(index=False).encode('utf-8'),
    file_name="inventario_medios.csv"
)

# --- Recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Interfaz ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")
menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Inventario Completo","🔍"),
    ("Incubación","⏱"), ("Baja Inventario","⚠️"), ("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"), ("Stock Reactivos","🔬"), ("Recetas de Medios","📖"), ("Imprimir Etiquetas","🖨")
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for i, (lbl, icn) in enumerate(menu):
    if cols[i % 4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"])
    semana = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    dia = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #", 1, 100)
    frascos = st.number_input("Cantidad de frascos", 1, 999, value=1)
    ph_aj = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros = st.number_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
    dosif = st.number_input("Dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [code, year, receta, solucion, equipo, semana, dia, prep,
                                   frascos, ph_aj, ph_fin, ce, litros, dosif, date.today().isoformat()]
        save_inventory()
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Entrada", code, frascos, f"Equipo: {equipo}"]
        save_history()
        st.success(f"Lote {code} registrado.")

elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button("Descargar Inventario (CSV)", inv_df.to_csv(index=False).encode("utf-8"), file_name="inventario_medios.csv")

    st.markdown("### Editar o borrar lote")
    if not inv_df.empty:
        cod_edit = st.selectbox("Selecciona el lote a editar o borrar", inv_df["Código"])
        row_idx = inv_df[inv_df["Código"] == cod_edit].index[0]
        # Mostrar formulario de edición
        with st.form("Editar lote"):
            col1, col2 = st.columns(2)
            with col1:
                anio = st.text_input("Año", inv_df.at[row_idx, "Año"])
                receta = st.text_input("Receta", inv_df.at[row_idx, "Receta"])
                solucion = st.text_input("Solución", inv_df.at[row_idx, "Solución"])
                equipo = st.text_input("Equipo", inv_df.at[row_idx, "Equipo"])
                semana = st.text_input("Semana", inv_df.at[row_idx, "Semana"])
                dia = st.text_input("Día", inv_df.at[row_idx, "Día"])
                prep = st.text_input("Preparación", inv_df.at[row_idx, "Preparación"])
                frascos = st.text_input("frascos", inv_df.at[row_idx, "frascos"])
            with col2:
                ph_aj = st.text_input("pH_Ajustado", inv_df.at[row_idx, "pH_Ajustado"])
                ph_fin = st.text_input("pH_Final", inv_df.at[row_idx, "pH_Final"])
                ce = st.text_input("CE_Final", inv_df.at[row_idx, "CE_Final"])
                litros = st.text_input("Litros_preparar", inv_df.at[row_idx, "Litros_preparar"])
                dosif = st.text_input("Dosificar_por_frasco", inv_df.at[row_idx, "Dosificar_por_frasco"])
                fecha = st.text_input("Fecha", inv_df.at[row_idx, "Fecha"])
            editar = st.form_submit_button("Guardar cambios")
            borrar = st.form_submit_button("Borrar lote", type="secondary")

        if editar:
            inv_df.at[row_idx, "Año"] = anio
            inv_df.at[row_idx, "Receta"] = receta
            inv_df.at[row_idx, "Solución"] = solucion
            inv_df.at[row_idx, "Equipo"] = equipo
            inv_df.at[row_idx, "Semana"] = semana
            inv_df.at[row_idx, "Día"] = dia
            inv_df.at[row_idx, "Preparación"] = prep
            inv_df.at[row_idx, "frascos"] = frascos
            inv_df.at[row_idx, "pH_Ajustado"] = ph_aj
            inv_df.at[row_idx, "pH_Final"] = ph_fin
            inv_df.at[row_idx, "CE_Final"] = ce
            inv_df.at[row_idx, "Litros_preparar"] = litros
            inv_df.at[row_idx, "Dosificar_por_frasco"] = dosif
            inv_df.at[row_idx, "Fecha"] = fecha
            save_inventory()
            st.success("Lote editado correctamente. Refresca o cambia de sección para ver los cambios.")
        if borrar:
            inv_df.drop(index=row_idx, inplace=True)
            inv_df.reset_index(drop=True, inplace=True)
            save_inventory()
            st.success("Lote borrado correctamente. Refresca o cambia de sección para ver los cambios.")

elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)

elif choice == "Incubación":
    st.header("⏱ Incubación")
    df_inc = inv_df.copy()
    df_inc["Fecha"] = pd.to_datetime(df_inc["Fecha"])
    df_inc["Días incubación"] = (pd.to_datetime(date.today()) - df_inc["Fecha"]).dt.days
    def hl(r): d=r["Días incubación"]; return (["background-color: yellow"]*len(r) if d<6 else ["background-color: lightgreen"]*len(r) if d<=28 else ["background-color: red"]*len(r))
    st.dataframe(df_inc.style.apply(hl, axis=1).format({"Días incubación":"{:.0f}"}), use_container_width=True)

elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo", ["Consumo", "Merma"])
    codigos = inv_df['Código'].tolist() + sol_df['Código_Solución'].tolist()
    sel = st.selectbox("Selecciona código", codigos)
    cantidad = st.number_input("Cantidad de frascos a dar de baja", 1, 999, value=1)
    tipo_merma = st.selectbox("Tipo de Merma", ["", "Contaminación", "Ruptura", "Evaporación", "Falla eléctrica", "Interrupción suministro agua", "Otro"]) if motivo == "Merma" else ""
    if st.button("Aplicar baja"):
        det = f"Cantidad frascos: {cantidad}" + (f"; Merma: {tipo_merma}" if motivo == "Merma" else "")
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), f"Baja {motivo}", sel, cantidad, det]
        save_history()
        if sel in inv_df['Código'].values:
            idx = inv_df[inv_df['Código'] == sel].index[0]
            inv_df.at[idx, 'frascos'] = max(0, int(inv_df.at[idx, 'frascos']) - cantidad)
            save_inventory()
        else:
            idx = sol_df[sol_df['Código_Solución'] == sel].index[0]
            sol_df.at[idx, 'Cantidad'] = max(0, float(sol_df.at[idx, 'Cantidad']) - cantidad)
            save_solutions()
        st.success(f"{motivo} aplicado a {sel}.")

elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel = st.selectbox("Selecciona lote", inv_df['Código'])
    cant_retor = st.number_input("Cantidad de frascos a retornar", 1, 999, value=1)
    if st.button("Aplicar retorno"):
        idx = inv_df[inv_df['Código'] == sel].index[0]
        inv_df.at[idx, 'frascos'] = int(inv_df.at[idx, 'frascos']) + cant_retor
        save_inventory()
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Retorno", sel, cant_retor, ""]
        save_history()
        st.success(f"Retorno de {cant_retor} frascos para {sel} aplicado.")

elif choice == "Soluciones Stock":
    st.header("🧪 Gestionar Soluciones Stock")
    c1, c2 = st.columns(2)
    with c1:
        fsol = st.date_input("Fecha", date.today())
        csol = st.number_input("Cantidad (L)", 0.0, format="%.2f")
        cods = st.text_input("Código Solución")
    with c2:
        resp = st.text_input("Responsable")
        reg = st.text_input("Regulador")
        obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fsol.isoformat(), csol, cods, resp, reg, obs]
        save_solutions()
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Stock Solución", cods, csol, f"Resp:{resp}"]
        save_history()
        st.success(f"Solución {cods} registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)
    st.download_button("Descargar Soluciones (CSV)", sol_df.to_csv(index=False).encode("utf-8"), file_name="soluciones_stock.csv")

elif choice == "Stock Reactivos":
    st.header("🔬 Stock de Reactivos")
    st.info("Sube tu archivo Excel (.xlsx) de inventario de reactivos. Se mostrará la tabla completa en pantalla.")
    uploaded_file = st.file_uploader("Selecciona el archivo Excel", type=["xlsx"])
    if uploaded_file:
        try:
            df_reactivos = pd.read_excel(uploaded_file)
            st.dataframe(df_reactivos, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")

elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    if recipes:
        for name, df in recipes.items():
            st.subheader(name)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontró el archivo de recetas.")

elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    if inv_df.empty:
        st.info("No hay lotes registrados aún.")
    else:
        cod_imp = st.selectbox("Selecciona lote", inv_df['Código'])
        if st.button("Generar etiqueta"):
            row = inv_df[inv_df['Código']==cod_imp].iloc[0]
            info=[f"Código: {row['Código']}",f"Receta: {row['Receta']}",f"Solución: {row['Solución']}",f"Fecha: {row['Fecha']}"]
            buf=make_qr(cod_imp); lbl=make_label(info,buf)
            st.image(lbl)
            pdf_buf=BytesIO(); lbl.convert("RGB").save(pdf_buf,format="PDF"); pdf_buf.seek(0)
            st.download_button("Descargar etiqueta (PDF)",pdf_buf,file_name=f"etiqueta_{cod_imp}.pdf",mime="application/pdf")
