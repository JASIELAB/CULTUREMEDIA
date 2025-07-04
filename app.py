import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de página ---

st.set\_page\_config(page\_title="Medios Cultivo", layout="wide")

# --- Logo en esquina ---

logo\_path = "plablue.png"
if os.path.isfile(logo\_path):
try:
logo = Image.open(logo\_path)
st.image(logo, width=120)
except Exception as e:
st.warning(f"Error al cargar logo: {e}")
else:
st.warning(f"Logo '{logo\_path}' no encontrado.")

# --- Helpers ---

def make\_qr(text: str) -> BytesIO:
img = qrcode.make(text)
buf = BytesIO()
img.save(buf, format="PNG")
buf.seek(0)
return buf

def make\_label(info\_lines, qr\_buf, size=(250, 120)):
w, h = size
img = Image.new("RGB", (w, h), "white")
draw = ImageDraw\.Draw(img)
try:
font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
except IOError:
font = ImageFont.load\_default()
y = 5
for line in info\_lines:
draw\.text((5, y), line, fill="black", font=font)
try:
bbox = draw\.textbbox((5, y), line, font=font)
th = bbox\[3] - bbox\[1]
except AttributeError:
th = draw\.textsize(line, font=font)\[1]
y += th + 2
qr\_img = Image.open(qr\_buf).resize((80, 80))
img.paste(qr\_img, (w - qr\_img.width - 5, (h - qr\_img.height) // 2))
return img

# --- Archivos y columnas ---

INV\_FILE  = "inventario\_medios.csv"
SOL\_FILE  = "soluciones\_stock.csv"
HIST\_FILE = "movimientos.csv"
REC\_FILE  = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv\_cols  = \[
"Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
"Frascos","pH\_Ajustado","pH\_Final","CE\_Final",
"Litros\_preparar","Dosificar\_por\_frasco","Fecha"
]
sol\_cols  = \["Fecha","Cantidad","Código\_Solución","Responsable","Regulador","Observaciones"]
hist\_cols = \["Timestamp","Tipo","Código","Cantidad","Detalles"]

def load\_df(path, cols):
if os.path.exists(path):
df = pd.read\_csv(path)
else:
df = pd.DataFrame(columns=cols)
for c in cols:
if c not in df.columns:
df\[c] = ''
return df\[cols]

inv\_df = load\_df(INV\_FILE, inv\_cols)
sol\_df = load\_df(SOL\_FILE, sol\_cols)
mov\_df = load\_df(HIST\_FILE, hist\_cols)

# --- Recetas ---

recipes = {}
if os.path.exists(REC\_FILE):
xls = pd.ExcelFile(REC\_FILE)
for sheet in xls.sheet\_names:
df = xls.parse(sheet)
if df.shape\[0] > 9:
sub = df.iloc\[9:, :3].dropna(how='all').copy()
sub.columns = \["Componente","Fórmula","Concentración"]
recipes\[sheet] = sub

# --- Interfaz ---

st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

menu = \[
("Registrar Lote","📋"),("Consultar Stock","📦"),("Inventario Completo","🔍"),
("Incubación","⏱"),("Baja Inventario","⚠️"),("Retorno Medio Nutritivo","🔄"),
("Soluciones Stock","🧪"),("Recetas de Medios","📖"),("Imprimir Etiquetas","🖨"),
("Control del Sistema","⚙️")
]
cols = st.columns(4)
if 'choice' not in st.session\_state:
st.session\_state.choice = menu\[0]\[0]
for i, (lbl, icn) in enumerate(menu):
if cols\[i%4].button(f"{icn}  {lbl}", key=lbl):
st.session\_state.choice = lbl
choice = st.session\_state.choice
st.markdown("---")

# --- Registrar Lote ---

if choice == "Registrar Lote":
st.header("📋 Registrar nuevo lote")
year     = st.number\_input("Año", 2000, 2100, value=date.today().year)
receta   = st.selectbox("Receta", list(recipes.keys()))
solucion = st.text\_input("Solución stock")
equipo   = st.selectbox("Equipo", \["Preparadora Alpha","Preparadora Beta"])
semana   = st.number\_input("Semana", 1, 52, value=int(datetime.today().strftime('%U')))
dia      = st.number\_input("Día", 1, 7, value=datetime.today().isoweekday())
prep     = st.number\_input("Preparación #", 1, 100)
frascos  = st.number\_input("Cantidad de frascos", 1, 999, value=1)
ph\_aj    = st.number\_input("pH ajustado", 0.0, 14.0, format="%.1f")
ph\_fin   = st.number\_input("pH final", 0.0, 14.0, format="%.1f")
ce       = st.number\_input("CE final", 0.0, 20.0, format="%.2f")
litros   = st.number\_input("Litros a preparar", 0.0, 100.0, value=1.0, format="%.2f")
dosif    = st.number\_input("Dosificar por frasco", 0.0, 10.0, value=0.0, format="%.2f")
if st.button("Registrar lote"):
code = f"{str(year)\[2:]}{receta\[:2]}Z{semana:02d}{dia}-{prep}"
inv\_df.loc\[len(inv\_df)] = \[
code, year, receta, solucion, equipo, semana, dia, prep,
frascos, ph\_aj, ph\_fin, ce, litros, dosif, date.today().isoformat()
]
inv\_df.to\_csv(INV\_FILE, index=False)
mov\_df.loc\[len(mov\_df)] = \[
datetime.now().isoformat(), "Entrada", code, frascos, f"Equipo: {equipo}"
]
mov\_df.to\_csv(HIST\_FILE, index=False)
st.success(f"Lote {code} registrado.")

# --- Consultar Stock ---

elif choice == "Consultar Stock":
st.header("📦 Consultar Stock")
st.dataframe(inv\_df, use\_container\_width=True)
st.download\_button(
"Descargar Inventario (CSV)",
inv\_df.to\_csv(index=False).encode("utf-8"),
file\_name="inventario\_medios.csv"
)

# --- Inventario Completo ---

elif choice == "Inventario Completo":
st.header("🔍 Inventario Completo")
st.dataframe(inv\_df, use\_container\_width=True)
st.markdown("---")
st.subheader("📜 Histórico de Movimientos")
st.dataframe(mov\_df, use\_container\_width=True)

# --- Baja Inventario ---

elif choice == "Baja Inventario":
st.header("⚠️ Baja de Inventario")
motivo   = st.radio("Motivo", \["Consumo","Merma"])
codigos  = inv\_df\['Código'].tolist() + sol\_df\['Código\_Solución'].tolist()
sel      = st.selectbox("Selecciona código", codigos)
cantidad = st.number\_input("Cantidad a dar de baja", 1, 999, value=1)
if st.button("Aplicar baja"):
mov\_df.loc\[len(mov\_df)] = \[
datetime.now().isoformat(),
f"Baja {motivo}",
sel,
cantidad,
f"Motivo: {motivo}"
]
mov\_df.to\_csv(HIST\_FILE, index=False)
if sel in inv\_df\['Código'].values:
idx = inv\_df\[inv\_df\['Código'] == sel].index\[0]
cur = int(inv\_df.at\[idx, "Frascos"])
inv\_df.at\[idx, "Frascos"] = max(0, cur - cantidad)
inv\_df.to\_csv(INV\_FILE, index=False)
else:
idx = sol\_df\[sol\_df\['Código\_Solución'] == sel].index\[0]
cur = float(sol\_df.at\[idx, "Cantidad"])
sol\_df.at\[idx, "Cantidad"] = max(0, cur - cantidad)
sol\_df.to\_csv(SOL\_FILE, index=False)
st.success(f"{motivo} aplicado a {sel}.")

# --- Retorno de Medio Nutritivo ---

elif choice == "Retorno Medio Nutritivo":
st.header("🔄 Retorno Medio Nutritivo")
sel        = st.selectbox("Selecciona lote", inv\_df\['Código'].tolist())
cant\_retor = st.number\_input("Cantidad de frascos a retornar", 1, 999, value=1)
if st.button("Aplicar retorno"):
idx = inv\_df\[inv\_df\['Código'] == sel].index\[0]
cur = int(inv\_df.at\[idx, "Frascos"])
inv\_df.at\[idx, "Frascos"] = cur + cant\_retor
inv\_df.to\_csv(INV\_FILE, index=False)
mov\_df.loc\[len(mov\_df)] = \[
datetime.now().isoformat(),
"Retorno",
sel,
cant\_retor,
""
]
mov\_df.to\_csv(HIST\_FILE, index=False)
st.success(f"Retorno de {cant\_retor} frascos para {sel} aplicado.")

# --- Soluciones Stock ---

elif choice == "Soluciones Stock":
st.header("🧪 Gestionar Soluciones Stock")
col1, col2 = st.columns(2)
with col1:
fecha\_sol    = st.date\_input("Fecha", value=date.today())
cantidad\_sol = st.number\_input("Cantidad (L)", min\_value=0.0, format="%.2f")
codigo\_sol   = st.text\_input("Código Solución")
with col2:
responsable   = st.text\_input("Responsable")
regulador     = st.text\_input("Regulador")
observaciones = st.text\_area("Observaciones")
if st.button("Registrar solución"):
sol\_df.loc\[len(sol\_df)] = \[
fecha\_sol.isoformat(),
cantidad\_sol,
codigo\_sol,
responsable,
regulador,
observaciones
]
sol\_df.to\_csv(SOL\_FILE, index=False)
mov\_df.loc\[len(mov\_df)] = \[
datetime.now().isoformat(),
"Stock Solución",
codigo\_sol,
cantidad\_sol,
f"Resp: {responsable}"
]
mov\_df.to\_csv(HIST\_FILE, index=False)
st.success(f"Solución {codigo\_sol} registrada.")

```
st.markdown("---")
st.subheader("📋 Inventario de Soluciones")
st.dataframe(sol_df, use_container_width=True)
st.download_button(
    "Descargar Soluciones (CSV)",
    sol_df.to_csv(index=False).encode("utf-8"),
    file_name="soluciones_stock.csv"
)
```

# --- Recetas de Medios ---

elif choice == "Recetas de Medios":
st.header("📖 Recetas de Medios")
if recipes:
for name, df in recipes.items():
st.subheader(name)
st.dataframe(df, use\_container\_width=True)
else:
st.info("No se encontró el archivo de recetas.")

# --- Imprimir Etiquetas ---

elif choice == "Imprimir Etiquetas":
st.header("🖨 Imprimir Etiquetas")
if not inv\_df.empty:
cod\_imp = st.selectbox("Selecciona lote", inv\_df\["Código"].tolist())
if st.button("Generar etiqueta"):
row = inv\_df\[inv\_df\["Código"] == cod\_imp].iloc\[0]
info = \[
f"Código: {row\['Código']}",
f"Receta: {row\['Receta']}",
f"Solución: {row\['Solución']}",
f"Fecha: {row\['Fecha']}"
]
buf   = make\_qr(cod\_imp)
label = make\_label(info, buf)
st.image(label)
bio = BytesIO()
label.save(bio, format="PNG")
bio.seek(0)
st.download\_button(
"Descargar etiqueta",
bio,
file\_name=f"etiqueta\_{cod\_imp}.png"
)
else:
st.info("No hay lotes registrados aún.")

# --- Control del Sistema ---

elif choice == "Control del Sistema":
st.header("⚙️ Control del Sistema")

```
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
```
