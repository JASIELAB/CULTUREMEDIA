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

# --- Archivos y columnas ---
INV_FILE  = "inventario_medios.csv"
SOL_FILE  = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE  = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols  = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "Frascros","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols  = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

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
    ("Registrar Lote","📋"),("Consultar Stock","📦"),("Inventario Completo","🔍"),
    ("Incubación","⏱"),("Baja Inventario","⚠️"),("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"),("Recetas de Medios","📖"),("Imprimir Etiquetas","🖨"),
    ("Control del Sistema","⚙️")
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for i, (lbl, icn) in enumerate(menu):
    if cols[i%4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# --- Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year     = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta   = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    equipo   = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"])
    semana   = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    dia      = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep     = st.number_input("Preparación #", 1, 100)
    frascros = st.number_input("Cantidad de frascros", 1, 999, value=1)
    ph_aj    = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin   = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce       = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros   = st.number_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
    dosif    = st.number_input("Dosificar por frascro", 0.0, 10.0, value=0.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [
            code, year, receta, solucion, equipo, semana, dia, prep,
            frascros, ph_aj, ph_fin, ce, litros, dosif, date.today().isoformat()
        ]
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(), "Entrada", code, frascros, f"Equipo: {equipo}"
        ]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Lote {code} registrado.")

# --- Consultar Stock ---
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button(
        "Descargar Inventario (CSV)",
        inv_df.to_csv(index=False).encode("utf-8"),
        file_name="inventario_medios.csv"
    )

# --- Inventario Completo ---
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)

# --- Incubación ---
elif choice == "Incubación":
    st.header("⏱ Incubación")
    df = inv_df.copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Días incubación"] = (pd.to_datetime(date.today()) - df["Fecha"]).dt.days

    def highlight_row(row):
        days = row["Días incubación"]
        if days < 6:
            color = "background-color: yellow"
        elif days <= 28:
            color = "background-color: lightgreen"
        else:
            color = "background-color: red"
        return [color] * len(row)

    st.dataframe(
        df.style.apply(highlight_row, axis=1)
               .format({"Días incubación": "{:.0f}"}),
        use_container_width=True
    )

# --- Baja Inventario (modificado) ---
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo   = st.radio("Motivo", ["Consumo","Merma"])
    codigos  = inv_df['Código'].tolist() + sol_df['Código_Solución'].tolist()
    sel      = st.selectbox("Selecciona código", codigos)
    cantidad = st.number_input("Cantidad de frascros a dar de baja", 1, 999, value=1)

    if motivo == "Merma":
        tipo_merma = st.selectbox(
            "Tipo de Merma",
            ["Contaminación","Ruptura","Evaporación",
             "Falla eléctrica","Interrupción del suministro de agua","Otro"]
        )
    else:
        tipo_merma = None

    if st.button("Aplicar baja"):
        detalles = f"Cantidad de frascros: {cantidad}"
        if motivo == "Merma":
            detalles += f"; Tipo de merma: {tipo_merma}"

        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),
            f"Baja {motivo}",
            sel,
            cantidad,
            detalles
        ]
        mov_df.to_csv(HIST_FILE, index=False)

        if sel in inv_df['Código'].values:
            idx = inv_df[inv_df['Código'] == sel].index[0]
            cur = int(inv_df.at[idx, "Frascros"])
            inv_df.at[idx, "Frascros"] = max(0, cur - cantidad)
            inv_df.to_csv(INV_FILE, index=False)
        else:
            idx = sol_df[sol_df['Código_Solución'] == sel].index[0]
            cur = float(sol_df.at[idx, "Cantidad"])
            sol_df.at[idx, "Cantidad"] = max(0, cur - cantidad)
            sol_df.to_csv(SOL_FILE, index=False)

        st.success(f"{motivo} aplicado a {sel}.")

# --- Retorno de Medio Nutritivo ---
elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel        = st.selectbox("Selecciona lote", inv_df['Código'].tolist())
    cant_retor = st.number_input("Cantidad de frascros a retornar", 1, 999, value=1)
    if st.button("Aplicar retorno"):
        idx = inv_df[inv_df['Código'] == sel].index[0]
        cur = int(inv_df.at[idx, "Frascros"])
        inv_df.at[idx, "Frascros"] = cur + cant_retor
        inv_df.to_csv(INV_FILE, index=False)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(), "Retorno", sel, cant_retor, ""
        ]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Retorno de {cant_retor} frascros para {sel} aplicado.")

# --- Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.header("🧪 Gestionar Soluciones Stock")
    col1, col2 = st.columns(2)
    with col1:
        fecha_sol    = st.date_input("Fecha", value=date.today())
        cantidad_sol = st.number_input("Cantidad (L)", min_value=0.0, format="%.2f")
        codigo_sol   = st.text_input("Código Solución")
    with col2:
        responsable   = st.text_input("Responsable")
        regulador     = st.text_input("Regulador")
        observaciones = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [
            fecha_sol.isoformat(), cantidad_sol, codigo_sol,
            responsable, regulador, observaciones
        ]
        sol_df.to_csv(SOL_FILE, index=False)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(), "Stock Solución",
            codigo_sol, cantidad_sol, f"Resp: {responsable}"
        ]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Solución {codigo_sol} registrada.")

    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)
    st.download_button(
        "Descargar Soluciones (CSV)",
        sol_df.to_csv(index=False).encode("utf-8"),
        file_name="soluciones_stock.csv"
    )

# --- Recetas de Medios ---
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    if recipes:
        for name, df in recipes.items():
            st.subheader(name)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No se encontró el archivo de recetas.")

# --- Imprimir Etiquetas ---
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    if not inv_df.empty:
        cod_imp = st.selectbox("Selecciona lote", inv_df["Código"].tolist())
        if st.button("Generar etiqueta"):
            row = inv_df[inv_df["Código"] == cod_imp].iloc[0]
            info = [
                f"Código: {row['Código']}",
                f"Receta: {row['Receta']}",
                f"Solución: {row['Solución']}",
                f"Fecha: {row['Fecha']}"
            ]
            buf   = make_qr(cod_imp)
            label = make_label(info, buf)
            st.image(label)
            bio = BytesIO()
            label.save(bio, format="PNG")
            bio.seek(0)
            st.download_button("Descargar etiqueta", bio,
                               file_name=f"etiqueta_{cod_imp}.png")
    else:
        st.info("No hay lotes registrados aún.")

# --- Control del Sistema ---
elif choice == "Control del Sistema":
    st.header("⚙️ Control del Sistema")

    st.subheader("Editar Inventario de Lotes")
    inv_edit = st.experimental_data_editor(inv_df, num_rows="dynamic")
    if st.button("Guardar cambios inventario"):
        inv_edit.to_csv(INV_FILE, index=False)
        st.success("Inventario actualizado.")

    st.markdown("---")
    st.subheader("Eliminar Lote")
    cod_elim = st.selectbox("Selecciona código de lote", inv_df["Código"].tolist())
    if st.button("Eliminar lote"):
        inv_df.drop(inv_df[inv_df["Código"] == cod_elim].index, inplace=True)
        inv_df.to_csv(INV_FILE, index=False)
        st.success(f"Lote {cod_elim} eliminado.")

    st.markdown("---")
    st.subheader("Editar Soluciones Stock")
    sol_edit = st.experimental_data_editor(sol_df, num_rows="dynamic")
    if st.button("Guardar cambios soluciones"):
        sol_edit.to_csv(SOL_FILE, index=False)
        st.success("Soluciones stock actualizadas.")

    st.markdown("---")
    st.subheader("Eliminar Solución")
    cod_sol_elim = st.selectbox("Código solución", sol_df["Código_Solución"].tolist())
    if st.button("Eliminar solución"):
        sol_df.drop(sol_df[sol_df["Código_Solución"] == cod_sol_elim].index, inplace=True)
        sol_df.to_csv(SOL_FILE, index=False)
        st.success(f"Solución {cod_sol_elim} eliminada.")
