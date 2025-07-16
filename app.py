import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN GOOGLE SHEETS ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
SERVICE_ACCOUNT_FILE = "credentials.json"  # <–– Cambia esto por el nombre de tu JSON
SHEET_INVENTARIO   = "INVENTARIO_MEDIOS"
SHEET_SOLUCIONES   = "SOLUCIONES_STOCK"
SHEET_MOVIMIENTOS  = "MOVIMIENTOS"
# Si quisieras recetas en Sheets, define otro nombre:
# SHEET_RECETAS = "RECETAS"

# --- AUTENTICACIÓN ---
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPE
)
gc = gspread.authorize(creds)

def get_ws(sheet_name: str):
    return gc.open(sheet_name).sheet1

def leer_df(sheet_name: str, cols: list):
    try:
        data = get_ws(sheet_name).get_all_records()
        df = pd.DataFrame(data)
    except Exception:
        df = pd.DataFrame()
    # asegurar columnas
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def guardar_df(sheet_name: str, df: pd.DataFrame):
    ws = get_ws(sheet_name)
    ws.clear()
    if not df.empty:
        ws.update([df.columns.tolist()] + df.values.tolist())

# --- Columnas estándar ---
inv_cols = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

# --- Carga inicial desde Sheets ---
inv_df = leer_df(SHEET_INVENTARIO, inv_cols)
sol_df = leer_df(SHEET_SOLUCIONES, sol_cols)
mov_df = leer_df(SHEET_MOVIMIENTOS, hist_cols)

# --- Helpers etiquetas QR ---
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

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Inventario Completo","🔍"),
    ("Incubación","⏱"), ("Baja Inventario","⚠️"), ("Retorno Medio Nutritivo","🔄"),
    ("Soluciones Stock","🧪"), ("Stock Reactivos","🔬"), ("Recetas de Medios","📖"),
    ("Imprimir Etiquetas","🖨"), ("Planning","📅")
]
cols = st.columns(4)
if 'choice' not in st.session_state:
    st.session_state.choice = menu[0][0]
for i, (lbl, icn) in enumerate(menu):
    if cols[i % 4].button(f"{icn}  {lbl}", key=lbl):
        st.session_state.choice = lbl
choice = st.session_state.choice
st.markdown("---")

# --- Sección: Registrar Lote ---
if choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    year    = st.number_input("Año", 2000, 2100, value=date.today().year)
    receta  = st.text_input("Receta")
    solucion= st.text_input("Solución stock")
    equipo  = st.selectbox("Equipo", ["Preparadora Alpha","Preparadora Beta"])
    semana  = st.number_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
    dia     = st.number_input("Día", 1, 7, value=datetime.today().isoweekday())
    prep    = st.number_input("Preparación #", 1, 100)
    frascos = st.number_input("Cantidad de frascos", 1, 999, value=1)
    ph_aj   = st.number_input("pH ajustado", 0.0, 14.0, format="%.1f")
    ph_fin  = st.number_input("pH final", 0.0, 14.0, format="%.1f")
    ce      = st.number_input("CE final", 0.0, 20.0, format="%.2f")
    litros  = st.number_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
    dosif   = st.number_input("Dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{str(year)[2:]}{receta[:2]}Z{semana:02d}{dia}-{prep}"
        inv_df.loc[len(inv_df)] = [
            code, year, receta, solucion, equipo, semana, dia, prep,
            frascos, ph_aj, ph_fin, ce, litros, dosif, date.today().isoformat()
        ]
        guardar_df(SHEET_INVENTARIO, inv_df)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(), "Entrada", code, frascos, f"Equipo: {equipo}"
        ]
        guardar_df(SHEET_MOVIMIENTOS, mov_df)
        st.success(f"Lote {code} registrado.")

# --- Sección: Consultar Stock ---
elif choice == "Consultar Stock":
    st.header("📦 Consultar Stock")
    st.dataframe(inv_df, use_container_width=True)
    st.download_button(
        "Descargar Inventario (CSV)",
        inv_df.to_csv(index=False).encode("utf-8"),
        file_name="inventario_medios.csv"
    )

    st.markdown("### Editar o borrar lote")
    if not inv_df.empty:
        cod_edit = st.selectbox("Selecciona el lote", inv_df["Código"])
        idx = inv_df[inv_df["Código"] == cod_edit].index[0]
        with st.form("Editar lote"):
            c1, c2 = st.columns(2)
            with c1:
                anio    = st.text_input("Año", inv_df.at[idx,"Año"])
                receta_ = st.text_input("Receta", inv_df.at[idx,"Receta"])
                sol_    = st.text_input("Solución", inv_df.at[idx,"Solución"])
                equipo_ = st.text_input("Equipo", inv_df.at[idx,"Equipo"])
                sem_    = st.text_input("Semana", inv_df.at[idx,"Semana"])
                dia_    = st.text_input("Día", inv_df.at[idx,"Día"])
                prep_   = st.text_input("Preparación", inv_df.at[idx,"Preparación"])
                fras_   = st.text_input("frascos", inv_df.at[idx,"frascos"])
            with c2:
                phaj_   = st.text_input("pH_Ajustado", inv_df.at[idx,"pH_Ajustado"])
                phfin_  = st.text_input("pH_Final", inv_df.at[idx,"pH_Final"])
                ce_     = st.text_input("CE_Final", inv_df.at[idx,"CE_Final"])
                lts_    = st.text_input("Litros_preparar", inv_df.at[idx,"Litros_preparar"])
                dos_    = st.text_input("Dosificar_por_frasco", inv_df.at[idx,"Dosificar_por_frasco"])
                fch_    = st.text_input("Fecha", inv_df.at[idx,"Fecha"])
            btn_edit  = st.form_submit_button("Guardar cambios")
            btn_del   = st.form_submit_button("Borrar lote", type="secondary")
        if btn_edit:
            inv_df.at[idx,"Año"]                  = anio
            inv_df.at[idx,"Receta"]               = receta_
            inv_df.at[idx,"Solución"]             = sol_
            inv_df.at[idx,"Equipo"]               = equipo_
            inv_df.at[idx,"Semana"]               = sem_
            inv_df.at[idx,"Día"]                  = dia_
            inv_df.at[idx,"Preparación"]          = prep_
            inv_df.at[idx,"frascos"]              = fras_
            inv_df.at[idx,"pH_Ajustado"]          = phaj_
            inv_df.at[idx,"pH_Final"]             = phfin_
            inv_df.at[idx,"CE_Final"]             = ce_
            inv_df.at[idx,"Litros_preparar"]      = lts_
            inv_df.at[idx,"Dosificar_por_frasco"] = dos_
            inv_df.at[idx,"Fecha"]                = fch_
            guardar_df(SHEET_INVENTARIO, inv_df)
            st.success("Lote editado correctamente.")
        if btn_del:
            inv_df.drop(index=idx, inplace=True)
            inv_df.reset_index(drop=True, inplace=True)
            guardar_df(SHEET_INVENTARIO, inv_df)
            st.success("Lote borrado correctamente.")

# --- Sección: Inventario Completo ---
elif choice == "Inventario Completo":
    st.header("🔍 Inventario Completo")
    st.dataframe(inv_df, use_container_width=True)
    st.markdown("---")
    st.subheader("📜 Histórico de Movimientos")
    st.dataframe(mov_df, use_container_width=True)

# --- Sección: Incubación ---
elif choice == "Incubación":
    st.header("⏱ Incubación")
    df_inc = inv_df.copy()
    df_inc["Fecha"]             = pd.to_datetime(df_inc["Fecha"])
    df_inc["Días incubación"]   = (pd.to_datetime(date.today()) - df_inc["Fecha"]).dt.days
    def hl(r):
        d = r["Días incubación"]
        if d < 6:    return ["background-color: yellow"] * len(r)
        if d <= 28:  return ["background-color: lightgreen"] * len(r)
        return ["background-color: red"] * len(r)
    st.dataframe(df_inc.style.apply(hl, axis=1).format({"Días incubación":"{:.0f}"}), use_container_width=True)

# --- Sección: Baja Inventario ---
elif choice == "Baja Inventario":
    st.header("⚠️ Baja de Inventario")
    motivo    = st.radio("Motivo", ["Consumo", "Merma"])
    codigos   = list(inv_df["Código"]) + list(sol_df.get("Código_Solución",[]))
    sel       = st.selectbox("Selecciona código", codigos)
    cantidad  = st.number_input("Cantidad de frascos", 1, 999, value=1)
    fecha_sal = st.date_input("Fecha de salida", value=date.today())
    tipo_m    = st.selectbox(
        "Tipo de Merma",
        ["", "Contaminación","Ruptura","Evaporación","Falla eléctrica","Interrupción suministro agua","Otro"]
    ) if motivo=="Merma" else ""
    if st.button("Aplicar baja"):
        detalle = f"Cantidad frascos: {cantidad}; Fecha salida: {fecha_sal}"
        if motivo=="Merma": detalle += f"; Merma: {tipo_m}"
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),
            f"Baja {motivo}",
            sel, cantidad,
            detalle
        ]
        guardar_df(SHEET_MOVIMIENTOS, mov_df)
        if sel in inv_df["Código"].values:
            idx0 = inv_df[inv_df["Código"]==sel].index[0]
            inv_df.at[idx0,"frascos"] = max(0, int(inv_df.at[idx0,"frascos"]) - cantidad)
            guardar_df(SHEET_INVENTARIO, inv_df)
        else:
            idx1 = sol_df[sol_df["Código_Solución"]==sel].index[0]
            sol_df.at[idx1,"Cantidad"] = max(0, float(sol_df.at[idx1,"Cantidad"]) - cantidad)
            guardar_df(SHEET_SOLUCIONES, sol_df)
        st.success(f"{motivo} aplicado a {sel}.")

# --- Sección: Retorno Medio Nutritivo ---
elif choice == "Retorno Medio Nutritivo":
    st.header("🔄 Retorno Medio Nutritivo")
    sel      = st.selectbox("Selecciona lote", inv_df["Código"])
    cant_ret = st.number_input("Cantidad de frascos a retornar", 1, 999, value=1)
    if st.button("Aplicar retorno"):
        idx2 = inv_df[inv_df["Código"]==sel].index[0]
        inv_df.at[idx2,"frascos"] = int(inv_df.at[idx2,"frascos"]) + cant_ret
        guardar_df(SHEET_INVENTARIO, inv_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Retorno",sel,cant_ret,""]
        guardar_df(SHEET_MOVIMIENTOS, mov_df)
        st.success(f"Retorno de {cant_ret} frascos para {sel} aplicado.")

# --- Sección: Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.header("🧪 Gestionar Soluciones Stock")
    c1, c2 = st.columns(2)
    with c1:
        fsol = st.date_input("Fecha", date.today())
        csol = st.number_input("Cantidad (L)", 0.0, format="%.2f")
        cods = st.text_input("Código Solución")
    with c2:
        resp = st.text_input("Responsable")
        reg  = st.text_input("Regulador")
        obs  = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fsol.isoformat(), csol, cods, resp, reg, obs]
        guardar_df(SHEET_SOLUCIONES, sol_df)
        mov_df.loc[len(mov_df)] = [datetime.now().isoformat(),"Stock Solución",cods,csol,f"Resp:{resp}"]
        guardar_df(SHEET_MOVIMIENTOS, mov_df)
        st.success(f"Solución {cods} registrada.")
    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)
    st.download_button(
        "Descargar Soluciones (CSV)",
        sol_df.to_csv(index=False).encode("utf-8"),
        file_name="soluciones_stock.csv"
    )

# --- Sección: Stock Reactivos ---
elif choice == "Stock Reactivos":
    st.header("🔬 Stock de Reactivos")
    st.info("Sube tu archivo Excel (.xlsx) de inventario de reactivos.")
    uploaded = st.file_uploader("Selecciona archivo", type=["xlsx"])
    if uploaded:
        try:
            df_r = pd.read_excel(uploaded)
            st.dataframe(df_r, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar: {e}")

# --- Sección: Recetas de Medios ---
elif choice == "Recetas de Medios":
    st.header("📖 Recetas de Medios")
    st.info("Sube tu archivo Excel de recetas (si no usas Sheets).")
    uploaded = st.file_uploader("Selecciona archivo", type=["xlsx"])
    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)
            for sheet in xls.sheet_names:
                df0 = xls.parse(sheet)
                if df0.shape[0] > 9:
                    sub = df0.iloc[9:,:3].dropna(how="all")
                    sub.columns = ["Componente","Fórmula","Concentración"]
                    st.subheader(sheet)
                    st.dataframe(sub, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar: {e}")

# --- Sección: Imprimir Etiquetas ---
elif choice == "Imprimir Etiquetas":
    st.header("🖨 Imprimir Etiquetas")
    if inv_df.empty:
        st.info("No hay lotes registrados.")
    else:
        cod_imp = st.selectbox("Selecciona lote", inv_df["Código"])
        if st.button("Generar etiqueta"):
            row = inv_df[inv_df["Código"]==cod_imp].iloc[0]
            info = [
                f"Código: {row['Código']}",
                f"Receta: {row['Receta']}",
                f"Solución: {row['Solución']}",
                f"Fecha: {row['Fecha']}"
            ]
            buf = make_qr(cod_imp)
            lbl = make_label(info, buf)
            st.image(lbl)
            pdf = BytesIO()
            lbl.convert("RGB").save(pdf, format="PDF")
            pdf.seek(0)
            st.download_button(
                "Descargar etiqueta (PDF)",
                pdf,
                file_name=f"etiqueta_{cod_imp}.pdf",
                mime="application/pdf"
            )

# --- Sección: Planning ---
elif choice == "Planning":
    st.header("📅 Planning de Propagación")
    st.info("Sube tu Excel con columnas 'Variedad' y 'Plantas'.")
    up = st.file_uploader("Selecciona planning", type=["xlsx"])
    receta_por_variedad = {
        "manila":   "AR2",
        "madeira":  "AR6",
        "maldiva":  "AR5",
        "zarzamora":"ZR-1"
    }
    if up:
        try:
            dfp = pd.read_excel(up)
            dfp.columns = [c.strip().lower() for c in dfp.columns]
            if "variedad" in dfp and "plantas" in dfp:
                dfp["receta"] = dfp["variedad"].str.lower().map(receta_por_variedad)
                dfp["frascos necesarios"] = (dfp["plantas"]/40).apply(lambda x: int(x) if x==int(x) else int(x)+1)
                st.success("Planeación cargada.")
                st.dataframe(dfp[["variedad","plantas","receta","frascos necesarios"]], use_container_width=True)
                st.download_button(
                    "Descargar Planning (CSV)",
                    dfp.to_csv(index=False).encode("utf-8"),
                    file_name="planning_con_recetas.csv"
                )
            else:
                st.error("Faltan columnas 'Variedad' o 'Plantas'.")
        except Exception as e:
            st.error(f"Error al procesar: {e}")
