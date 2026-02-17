import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Urgencias 2026", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Establecemos la conexión usando los secretos que configuraremos en la nube
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos (sin caché excesiva para ver cambios al instante)
def load_data():
    # ttl=5 significa que los datos se refrescan cada 5 segundos si hay cambios
    return conn.read(worksheet="Base Urgencias 2026", ttl="10m") 

# Función para guardar datos
def add_row_to_sheet(new_row_df, current_df):
    # Unimos el dato nuevo con lo que ya existe
    updated_df = pd.concat([current_df, new_row_df], ignore_index=True)
    # Escribimos todo de vuelta al Sheet
    conn.update(data=updated_df)

# Cargar base inicial
try:
    df = load_data()
    # Aseguramos que las fechas sean fechas y no texto
    # df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce') 
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# --- INTERFAZ ---
st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a:", ["Panel de Control", "Cargar Nuevo Caso", "Base de Datos"])

# --- PÁGINA 1: DASHBOARD ---
if page == "Panel de Control":
    st.title("📊 Panel de Control - Urgencias 2026")

    # 1. Elimina filas donde 'Local' es nulo (NaN)
df = df.dropna(subset=['Local'])

# 2. Asegura eliminar filas que tengan texto vacío o solo espacios
df = df[df['Local'].astype(str).str.strip() != '']
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Casos", len(df))
        col2.metric("Pendientes", len(df[df['ESTADO'] == 'Sin Respuesta']))
        col3.metric("En Proceso", len(df[df['ESTADO'] == 'En Proceso']))
        col4.metric("Cerrados", len(df[df['ESTADO'] == 'Cerrado']))
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Estado de los Casos")
            fig = px.pie(df, names='ESTADO', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Casos por Categoría")
            # Agrupamos para contar
            conteo = df['CATEGORIA'].value_counts().reset_index()
            conteo.columns = ['Categoría', 'Cantidad']
            fig2 = px.bar(conteo, x='Categoría', y='Cantidad', color='Categoría')
            st.plotly_chart(fig2, use_container_width=True)

# --- PÁGINA 2: CARGAR ---
elif page == "Cargar Nuevo Caso":
    st.title("📝 Nuevo Reclamo / Urgencia")
    
    with st.form("form_alta"):
        c1, c2 = st.columns(2)
        fecha = c1.date_input("Fecha", datetime.now())
        local = c2.text_input("Número de Local")
        
        direccion = st.text_input("Dirección")
        
        c3, c4, c5 = st.columns(3)
        barrio = c3.text_input("Barrio")
        estado = c4.selectbox("Estado", ["Programado", "Sin Respuesta", "En Proceso", "Cerrado"])
        categoria = c5.selectbox("Categoría", ["Edilicio", "Sanitario", "Eléctrico", "Refrigeración", "Otro"])
        
        observacion = st.text_area("Detalle del Problema")
        colaborador = st.text_input("Colaborador Asignado")
        
        submitted = st.form_submit_button("Guardar en Google Sheets")
        
        if submitted:
            # Crear la fila nueva con las mismas columnas que tu Excel
            new_data = pd.DataFrame([{
                'FECHA': fecha.strftime('%d/%m/%Y'),
                'LOCAL': local,
                'DIRECCION': direccion,
                'BARRIO': barrio,
                'ESTADO': estado,
                'CATEGORIA': categoria,
                'OBSERVACION': observacion,
                'COLABORADOR': colaborador,
                # Asegúrate de agregar aquí todos los campos obligatorios de tu CSV original
                # Los que no pongas quedarán vacíos (NaN)
            }])
            
            with st.spinner("Guardando en la nube..."):
                add_row_to_sheet(new_data, df)
                st.success("✅ ¡Guardado exitosamente en Google Sheets!")
                # Limpiamos caché para ver el dato nuevo al instante
                st.cache_data.clear()

# --- PÁGINA 3: DATOS ---
elif page == "Base de Datos":
    st.title("🔍 Explorar Base Completa")

    st.dataframe(df, use_container_width=True)

