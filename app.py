import streamlit as st
import pandas as pd
import gspread
import time
import json
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Project Tracker", page_icon="🚀", layout="wide")

# Estilos CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00CC96;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Tablero de Control Escuela #DE#: Misión Educativa")
st.markdown("---")

# --- CONEXIÓN HÍBRIDA (NUBE / LOCAL) ---
@st.cache_data
def cargar_datos():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # LÓGICA INTELIGENTE DE CREDENCIALES
        if "google_credentials" in st.secrets:
            # Opción 1: Nube (Streamlit Cloud)
            key_dict = dict(st.secrets["google_credentials"])
            creds = Credentials.from_service_account_info(key_dict, scopes=scope)
        else:
            # Opción 2: Local (Tu compu)
            creds = Credentials.from_service_account_file("credenciales.json", scopes=scope)
            
        client = gspread.authorize(creds)
        
        # ⚠️ IMPORTANTE: REEMPLAZÁ ESTO CON TU ID ANTES DE GUARDAR ⚠️
        spreadsheet_id = "1nfXLWBLfjIXznMIjlojpaAKD3bTRrThEvkjihCjwbUk" 
        
        # ... código anterior ...
    sheet = client.open_by_key(spreadsheet_id).worksheet("TRACKER")
    
    # --- CAMBIO INICIO: Versión a prueba de errores ---
    # 1. Traemos todo #1 crudo (lista de listas), esto NO falla por encabezados
    all_values = sheet.get_all_values()
    
    # 2. Si la hoja está vacía, devolvemos un DataFrame vacío para no romper nada
    if not all_values:
            return pd.DataFrame()

    # 3. Separamos encabezados (fila 1) de los datos (resto)
    headers = all_values[0]
    rows = all_values[1:]

    # 4. Creamos el DataFrame
    df = pd.DataFrame(rows, columns=headers)

    # 5. EL FILTRO MÁGICO: Eliminamos cualquier columna que no tenga nombre
    # Esto borra las columnas "fantasma" que causaban el error
    df = df.loc[:, df.columns != '']

    return df
    # --- CAMBIO FIN ---

    except Exception as e:
        return str(e)

# --- FUNCIÓN INTELIGENTE PARA ENCONTRAR COLUMNAS ---
def buscar_columna(df, palabras_clave):
    for col in df.columns:
        if palabras_clave.lower() in col.lower():
            return col
    return None

# --- LÓGICA DE SECRETARIA VIRTUAL (VERSIÓN HÍBRIDA) ---
def generar_asistente(df, col_recursos, col_principal, col_avance, col_dias):
    st.info("🤖 **Asistente Virtual:** Analizando recursos y redacción de correos...")
    time.sleep(1.5)
    texto = "--- REPORTE DE GESTIÓN ---\n\n"
    
    # 1. LISTADO DE RECURSOS PENDIENTES
    texto += "🚨 RECURSOS CRÍTICOS:\n"
    # Filtramos acá mismo los que tienen problemas
    df_recursos = df[df[col_recursos].isin(["Faltante", "A gestionar"])]
    
    if len(df_recursos) > 0:
        for i, fila in df_recursos.iterrows():
            nombre = fila.get('Nombre del Proyecto', 'Sin nombre')
            estado = fila.get(col_recursos, '')
            item = fila.get(col_principal, '')
            texto += f"- {nombre}: {estado} ({item})\n"
    else:
        texto += "No hay recursos pendientes.\n"
    
    texto += "\n" + "="*40 + "\n\n"

    # 2. GENERADOR DE EMAILS (Proyectos con avance bajo y poco tiempo)
    texto += "📧 BORRADORES DE CORREO (Proyectos < 50% avance):\n\n"
    
    # Filtramos proyectos con menos de 50% de avance
    if col_avance and col_dias:
        df_atrasados = df[df[col_avance] < 50]
        
        for i, fila in df_atrasados.iterrows():
            profe = fila.get('Docentes Responsables', 'Profe')
            proyecto = fila.get('Nombre del Proyecto', 'Proyecto')
            avance = fila.get(col_avance, 0)
            dias = fila.get(col_dias, '?')
            
            texto += f"PARA: {profe}\n"
            texto += f"ASUNTO: Seguimiento - {proyecto}\n"
            texto += f"Hola {profe},\n"
            texto += f"Te escribo porque notamos que el avance registrado es del {avance}% "
            texto += f"y restan {dias} días para la entrega.\n"
            texto += "¿Necesitás ayuda con algún bloqueo? Avísanos.\n"
            texto += "-"*20 + "\n\n"
            
    return texto

# --- INTERFAZ PRINCIPAL ---
df_result = cargar_datos()

if isinstance(df_result, str):
    st.error(f"❌ Error de conexión: {df_result}")
    st.warning("Revisá que el ID de la planilla sea el correcto y que el archivo Secrets en Streamlit esté bien configurado.")
else:
    df = df_result
    
    # LIMPIEZA DE COLUMNAS
    df.columns = df.columns.str.strip()

    # --- DETECTIVES DE COLUMNAS ---
    col_area = buscar_columna(df, "Area Principal")
    if not col_area: col_area = buscar_columna(df, "Area")
    
    col_otras = buscar_columna(df, "Otras") 
    col_avance = buscar_columna(df, "Avance")
    col_estado = buscar_columna(df, "Estado") 
    col_estado_recursos = buscar_columna(df, "Estado Recursos")
    col_recurso_principal = buscar_columna(df, "Recurso Principal")
    col_recurso_adicional = buscar_columna(df, "Adicional")
    col_dias = buscar_columna(df, "Dias")

    # --- LIMPIEZA MATEMÁTICA ---
    if col_avance:
        df[col_avance] = pd.to_numeric(df[col_avance], errors='coerce').fillna(0)

    # 1. FILTROS LATERALES
    st.sidebar.header("🔍 Filtros")
    if col_area:
        filtro_area = st.sidebar.multiselect("Filtrar por Área", df[col_area].unique())
        if filtro_area:
            df = df[df[col_area].isin(filtro_area)]

    # 2. KPIS (MÉTRICAS)
    total = len(df)
    
    # --- CAMBIO 1: AHORA INCLUIMOS "A gestionar" ---
    criticos = pd.DataFrame()
    if col_estado_recursos:
        # Filtramos los que dicen "Faltante" O "A gestionar"
        criticos = df[df[col_estado_recursos].isin(["Faltante", "A gestionar"])]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Proyectos Activos", total)
    
    # Cambiamos el título del KPI para que sea más abarcativo
    col2.metric("⚠️ Recursos Pendientes", len(criticos), delta_color="inverse")
    
    if total > 0 and col_avance:
        progreso = int(df[col_avance].mean())
        col3.metric("📈 Avance Promedio", f"{progreso}%")
        st.progress(progreso)

    st.divider()

    # 3. EL TABLERO VISUAL
    st.subheader("📋 Estado de Situación")

    for i, row in df.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            
            with c1:
                st.subheader(f"🔹 {row.get('Nombre del Proyecto', 'Sin Título')}")
                
                # Áreas
                area_txt = row.get(col_area, '') if col_area else ''
                otras_txt = row.get(col_otras, '') if col_otras else ''
                
                if "Interdisciplinario" in str(area_txt):
                    st.caption(f"🎓 **{area_txt}** con: {otras_txt}")
                else:
                    st.caption(f"📚 Área: {area_txt}")
                
                # Días Restantes
                if col_dias:
                    try:
                        dias = int(row[col_dias])
                        if dias < 7:
                            st.write(f"⏳ **Vence en:** :red[{dias} días] 🔥")
                        else:
                            st.write(f"⏳ **Vence en:** {dias} días")
                    except:
                        st.write("⏳ Vencimiento: Sin fecha")

            with c2:
                # --- CAMBIO 2: ETIQUETAS MÁS CLARAS ---
                if col_estado_recursos:
                    est_rec = row[col_estado_recursos]
                    if est_rec == "Faltante":
                        st.error(f"🛑 Estado de Recursos: {est_rec}")
                    elif est_rec == "A gestionar":
                        st.warning(f"✋ Estado de Recursos: {est_rec}")
                    else:
                        st.success(f"✅ Estado de Recursos: {est_rec}")
                
                # Recursos
                principal = row.get(col_recurso_principal, '-')
                adicional = row.get(col_recurso_adicional, '')
                
                st.write(f"🖥️ **Principal:** {principal}")
                if adicional:
                    st.write(f"🔌 **Extra:** {adicional}")

            with c3:
                if col_avance:
                    val = int(row[col_avance])
                    estado_p = row.get(col_estado, '')
                    st.write(f"Avance: **{val}%** ({estado_p})")
                    st.progress(val)
                
                link = row.get('Link Carpeta', '')
                if link:
                    st.markdown(f"[📂 Ver Planificación]({link})")

            st.markdown("---")

  # 4. ZONA DE ACCIÓN
    st.subheader("⚡ Acciones Rápidas")
    
    # Botón único que genera todo el reporte
    if st.button("Generar Reporte de Asistente Virtual"):
        # Llamamos a la nueva función pasándole TODAS las columnas necesarias
        reporte = generar_asistente(df, col_estado_recursos, col_recurso_principal, col_avance, col_dias)
        st.text_area("Copiar Reporte y Mails:", reporte, height=300)


