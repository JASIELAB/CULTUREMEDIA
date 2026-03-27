import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date
from PIL import Image
from fpdf import FPDF # <-- Nueva librería para PDF

# --- CONFIGURACIÓN Y FUNCIONES BASE (SE MANTIENEN IGUAL) ---
st.set_page_config(page_title="Sistema InVitRo", layout="wide")

def safe_int(val, default=0):
    try: return int(float(val)) if not pd.isna(val) else default
    except: return default

def safe_float(val, default=0.0):
    try: return float(val) if not pd.isna(val) else default
    except: return default

# --- PERSISTENCIA ---
INV_FILE = "inventario_medios.csv"
RECETAS_JSON = "recetas_config.json"

def load_df():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE, dtype=str)
        df['frascos'] = pd.to_numeric(df['frascos'], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=["Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", "frascos", "Fecha_Prep", "pH_Final"])

inv_df = load_df()

# --- INTERFAZ ---
st.title("🧪 Control de Medios InVitRo")
menu = ["Registrar Lote", "Consultar Stock", "Incubación", "Recetas", "Etiquetas"]
choice = st.sidebar.selectbox("Menú", menu)

# ... (Las secciones de Registrar, Stock, Incubación y Recetas se mantienen igual que el código anterior) ...

# --- SECCIÓN: ETIQUETAS (AHORA EN PDF) ---
if choice == "Etiquetas":
    st.header("🖨 Generador de Etiquetas PDF (3.5 x 2.0 cm)")
    
    if not inv_df.empty:
        sel_e = st.selectbox("Selecciona Lote para la etiqueta:", inv_df['Código'])
        lote_info = inv_df[inv_df['Código'] == sel_e].iloc[0]
        
        if st.button("Generar PDF de Etiqueta"):
            # 1. Crear el QR en memoria
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(sel_e)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Guardar QR temporalmente para el PDF
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            
            # 2. Crear el PDF con medidas personalizadas (35mm x 20mm)
            # 'P' = Portrait, 'mm' = milímetros, format=(ancho, alto)
            pdf = FPDF('L', 'mm', (20, 35)) 
            pdf.add_page()
            pdf.set_margins(1, 1, 1)
            pdf.set_auto_page_break(False)

            # Insertar QR (Posición x, y, ancho, alto en mm)
            pdf.image(qr_buffer, x=1, y=2, w=16, h=16)
            
            # Configurar texto a la derecha del QR
            pdf.set_xy(17, 2)
            pdf.set_font("Arial", "B", 6)
            pdf.cell(0, 3, "RECETA:", ln=True)
            pdf.set_x(17)
            pdf.set_font("Arial", "", 7)
            pdf.cell(0, 4, f"{lote_info['Receta']}", ln=True)
            
            pdf.set_x(17)
            pdf.set_font("Arial", "B", 6)
            pdf.cell(0, 3, "FECHA:", ln=True)
            pdf.set_x(17)
            pdf.set_font("Arial", "", 7)
            pdf.cell(0, 4, f"{lote_info['Fecha_Prep']}", ln=True)
            
            pdf.set_x(17)
            pdf.set_font("Arial", "B", 6)
            pdf.cell(0, 3, "LOTE:", ln=True)
            pdf.set_x(17)
            pdf.set_font("Arial", "B", 7)
            pdf.cell(0, 4, f"{sel_e}", ln=True)
            
            # 3. Descargar el PDF
            pdf_output = pdf.output() # Devuelve bytes en fpdf2
            st.success("✅ Etiqueta PDF generada con éxito")
            st.download_button(
                label="📥 Descargar Etiqueta PDF",
                data=bytes(pdf_output),
                file_name=f"Etiqueta_{sel_e}.pdf",
                mime="application/pdf"
            )
            
            # Vista previa visual (opcional)
            st.info("Nota: El archivo PDF está optimizado para impresoras térmicas de 35mm x 20mm.")
    else:
        st.warning("No hay datos para generar etiquetas.")
