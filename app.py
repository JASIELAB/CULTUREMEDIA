import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Page Config ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")

# --- Logo en esquina superior izquierda ---
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar el logo: {e}")
else:
    st.warning(f"Logo '{logo_path}' no encontrado en el directorio de la aplicación.")

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
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            _, text_height = font.getsize(line)
        y += text_height + 2
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Data Files ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# Column definitions
inv_cols = ["Código", "Año", "Receta", "Solución", "Equipo", "Semana", "Día", "Preparación", "Frascos", "pH_Ajustado", "pH_Final", "CE_Final", "Fecha"]
sol_cols = ["Fecha", "Cantidad", "Código_Solución", "Responsable", "Regulador", "Observaciones"]
hist_cols = ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"]

# Load data or create empty
def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]

inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

# Cargar recetas desde Excel
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente", "Fórmula", "Concentración"]
            recipes[sheet] = sub

# --- User Interface ---
st.title("Control de Medios de Cultivo InVitro")
st.markdown("---")

menu = [
    ("Registrar Lote", "📋"),
    ("Consultar Stock", "📦"),
    ("Inventario Completo", "🔍"),
    ("Incubación", "⏱"),
    ("Baja Inventario", "⚠️"),
    ("Retorno Medio Nutritivo", "🔄"),
    ("Soluciones Stock", "🧪"),
    ("Recetas de Medios", "📖"),
    ("Imprimir Etiquetas", "🖨"),
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for idx, (label, icon) in enumerate(menu):
    if cols[idx % 4].button(f"{icon}  {label}", key=label):
        st.session_state.choice = label
choice = st.session_state.choice
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    año = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo = st.selectbox("Equipo", ["Preparadora Alpha", "Preparadora Beta"])
    semana = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    día = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep = st.number_input("Preparación #", 1, 100)
    frascros = st.number_input("Cantidad de frascros", 1, 999, value=1)
    ph_aj = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(año)[2:]}{receta[:2]}Z{semana:02d}{día}-{prep}"
        inv_df.loc[len(inv_df)] = [code, año, receta, solucion, equipo, semana, día, prep, frascros, ph_aj, ph_fin, ce, date.today().isoformat()]
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Entrada", code, frascros, f"Equipo: {equipo}"]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Lote {code} registrado.")

# --- Consultar Stock ---
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    csv_inv = inv_df.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Inventario (CSV)", csv_inv, file_name="inventario_medios.csv", mime="text/csv")

# --- Inventario Completo ---
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)
    csv_mov = mov_df.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Histórico (CSV)", csv_mov, file_name="movimientos_stock.csv", mime="text/csv")
    buffer_mov = BytesIO()
    with pd.ExcelWriter(buffer_mov, engine='openpyxl') as writer:
        mov_df.to_excel(writer, index=False, sheet_name='Movimientos')
    buffer_mov.seek(0)
    st.download_button("Descargar Histórico (Excel)", buffer_mov, file_name="movimientos_stock.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Incubación ---
elif choice == "Incubación":
    st.header("⏱ Estado de incubación")
    df2 = inv_df.copy()
    df2['Días'] = (pd.to_datetime(date.today()) - pd.to_datetime(df2['Fecha'])).dt.days
    def color_row(days):
        if days > 28:
            return 'background-color:#FFCDD2'
        elif days > 7:
            return 'background-color:#C8E6C9'
        else:
            return 'background-color:#FFF9C4'
    st.dataframe(df2.style.apply(lambda r: [color_row(r['Días'])]*len(r), axis=1), use_container_width=True)

# --- Baja Inventario ---
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo = st.radio("Motivo:", ["Consumo", "Merma"])
    códigos = inv_df['Código'].tolist() + sol_df['Código_Solución'].tolist()
    sel = st.selectbox("Selecciona código", códigos)
    fecha = st.date_input("Fecha de salida")
    variedad = st.text_input("Variedad")
    cantidad_frasros = st.number_input("Cantidad de frascros a dar de baja", min_value=1, value=1)
    if motivo == "Merma":
        tipo_merma = st.selectbox("Tipo de Merma", ["Contaminación", "Ruptura", "Evaporación", "Falla eléctrica", "Interrupción del suministro de agua", "Otro"])
    if st.button("Aplicar baja"):
        if sel in inv_df['Código'].tolist():
            inv_df.loc[inv_df['Código'] == sel, 'Frascros'] -= cantidad_frasros
            if inv_df.loc[inv_df['Código'] == sel, 'Frascros'].values[0] <= 0:
                inv_df.drop(inv_df[inv_df['Código'] == sel].index, inplace=True)
            inv_df.to_csv(INV_FILE, index=False)
        else:
            sol_df['Cantidad'] = sol_df['Cantidad'].astype(int)
            sol_df.loc[sol_df['Código_Solución'] == sel, 'Cantidad'] -= cantidad_frasros
            if sol_df.loc[sol_df['Código_Solución'] == sel, 'Cantidad'].values[0] <= 0:
                sol_df.drop(sol_df[sol_df['Código_Solución'] == sel].index, inplace=True)
            sol_df.to_csv(SOL_FILE, index=False)
        detalle = f"{motivo}"
        if motivo == "Merma":
            detalle += f" ({tipo_merma})"
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Salida", sel, cantidad_frasros, detalle]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"{cantidad_frasros} frascros dados de baja por {detalle}.")

# --- Retorno Medio Nutritivo ---
elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno de Medio Nutritivo")
    códigos = inv_df['Código'].tolist()
    sel = st.selectbox("Selecciona código", códigos)
    fecha_ret = st.date_input("Fecha de retorno")
    cantidad_retorno = st.number_input("Cantidad de frascros a retornar", min_value=1, value=1)
    if st.button("Aplicar retorno"):
        inv_df.loc[inv_df['Código'] == sel, 'Frascros'] += cantidad_retorno
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(), "Retorno", sel, cantidad_retorno, ""]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"{cantidad_retorno} frascros retornados al inventario.")

# --- Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.header("🧪 Soluciones Stock")
    col1, col2 = st.columns(2)
    with col1:
        f2 = st.date_input("Fecha")
        cant2 = st.text_input("Cantidad")
        code_s = st.text_input("Código Solución")
    with col2:
        resp = st.text_input("Responsable")
        reg = st.text_input("Regulador")
        obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [f2.isoformat(), cant2, code_s, resp, reg, obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
    st.markdown("---")
    st.subheader("📦 Stock de Soluciones Registradas")
    st.dataframe(sol_df, use_container_width=True)
    csv_sol = sol_df.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Soluciones (CSV)", csv_sol, file_name="soluciones_stock.csv", mime="text/csv")
    buffer_sol = BytesIO()
    with pd.ExcelWriter(buffer_sol, engine='openpyxl') as writer:
        sol_df.to_excel(writer, index=False, sheet_name='Soluciones')
    buffer_sol.seek(0)
    st.download_button("Descargar Soluciones (Excel)", buffer_sol, file_name="soluciones_stock.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Recetas de Medios ---
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    selr = st.selectbox("Receta", list(recipes.keys()))
    st.dataframe(recipes[selr], use_container_width=True)

# --- Imprimir Etiquetas ---
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    opts = inv_df['Código'].tolist()
    sels = st.multiselect("Selecciona lote(s)", opts)
    if st.button("Generar etiquetas") and sels:
        for code in sels:
            r = inv_df[inv_df['Código'] == code].iloc[0]
            info = [
                f"Código: {code}",
                f"Año: {r['Año']}",
                f"Receta: {r['Receta']}",
                f"Sol.: {r['Solución']}",
                f"Equipo: {r['Equipo']}",
                f"Sem: {r['Semana']}",
                f"Día: {r['Día']}",
                f"Prep: {r['Preparación']}",
                f"Frascros: {r['Frascros']}" if 'Frascros' in r else f"Frascros: {r['Frascros']}"
            ]
            buf = make_qr(code)
            lbl = make_label(info, buf)
            st.image(lbl)
            pdf_buf = BytesIO()
            lbl_rgb = lbl.convert('RGB')
            lbl_rgb.save(pdf_buf, format='PDF')
            pdf_buf.seek(0)
            st.download_button(f"Descargar PDF {code}", pdf_buf, file_name=f"{code}.pdf", mime='application/pdf')
        st.info("Etiquetas generadas y listas para descargar.")
