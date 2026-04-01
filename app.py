import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

# --- NOTA: Para el escáner se recomienda instalar: pip install streamlit-camera-input-live ---
# Como alternativa robusta para web, usaremos el input nativo de cámara de Streamlit.

# --- CONFIGURACIÓN Y FUNCIONES BASE ---
st.set_page_config(page_title="Sistema InVitRo", layout="wide")

def safe_int(val, default=0):
    try: return int(float(val)) if not pd.isna(val) else default
    except: return default

def safe_float(val, default=0.0):
    try: return float(val) if not pd.isna(val) else default
    except: return default

# --- PERSISTENCIA ---
INV_FILE = "inventario_medios.csv"
HISTORIAL_BAJAS = "historial_bajas.csv"

def load_df():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE, dtype=str)
        df['frascos'] = pd.to_numeric(df['frascos'], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=["Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", "frascos", "Fecha_Prep", "pH_Final"])

def save_baja(lote, cantidad, tipo, motivo):
    # Guarda un registro de por qué se dio de baja para auditoría
    nueva_baja = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Lote": lote,
        "Cantidad": cantidad,
        "Tipo": tipo,
        "Motivo": motivo
    }])
    if not os.path.exists(HISTORIAL_BAJAS):
        nueva_baja.to_csv(HISTORIAL_BAJAS, index=False)
    else:
        nueva_baja.to_csv(HISTORIAL_BAJAS, mode='a', header=False, index=False)

inv_df = load_df()

# --- INTERFAZ ---
st.title("🧪 Control de Medios InVitRo")
menu = ["Registrar Lote", "Consultar Stock", "Incubación", "Recetas", "Baja Inventario", "Etiquetas"]
choice = st.sidebar.selectbox("Menú", menu)

# ... (Secciones anteriores: Registrar, Stock, Incubación, Recetas se mantienen) ...

# --- 5. BAJA INVENTARIO (CON ESCÁNER Y MENÚ DE MOTIVOS) ---
if choice == "Baja Inventario":
    st.header("⚠️ Registro de Bajas")
    
    col_scan, col_manual = st.columns([1, 1])
    
    with col_scan:
        st.subheader("📷 Escanear QR")
        # El widget de cámara permite capturar el código si tienes el QR impreso
        img_file = st.camera_input("Enfoca el código QR de la etiqueta")
        # Nota: Para decodificar automáticamente el QR de la foto en tiempo real
        # se requiere la librería 'pyzbar', pero aquí lo haremos simple por ID.
        if img_file:
            st.info("Imagen capturada. Procesando...")

    with col_manual:
        st.subheader("🛠️ Detalles de la Baja")
        # Búsqueda manual o por selección (el código escaneado se pegaría aquí)
        lote_id = st.selectbox("Lote a descontar:", [""] + list(inv_df['Código'].unique()))
        
        if lote_id:
            idx = inv_df[inv_df['Código'] == lote_id].index[0]
            stock_actual = inv_df.at[idx, 'frascos']
            st.metric("Stock disponible", f"{stock_actual} frascos")

            with st.form("form_baja"):
                cant_b = st.number_input("Cantidad a retirar:", 1, stock_actual, 1)
                
                # Menú solicitado por tipo de baja
                tipo_baja = st.selectbox("Tipo de Movimiento:", ["Consumo (Uso en Laboratorio)", "Merma (Contaminación/Error)"])
                
                # Sub-motivos específicos
                motivo = st.text_area("Comentarios adicionales (opcional):", placeholder="Ej: Contaminación por hongo, Lote utilizado para siembra de Arándano...")
                
                enviar_baja = st.form_submit_button("Confirmar Movimiento")

                if enviar_baja:
                    # Actualizar Inventario
                    inv_df.at[idx, 'frascos'] = stock_actual - cant_b
                    inv_df.to_csv(INV_FILE, index=False)
                    
                    # Guardar Historial
                    save_baja(lote_id, cant_b, tipo_baja, motivo)
                    
                    st.success(f"✅ Se han retirado {cant_b} frascos por concepto de '{tipo_baja}'.")
                    st.balloons()
                    st.rerun()

# --- 6. ETIQUETAS (PDF 3.5x2cm) ---
elif choice == "Etiquetas":
    # (Se mantiene el código anterior de generación de PDF que te pasé)
    st.header("🖨 Generador de Etiquetas PDF")
    # ... código PDF ...
