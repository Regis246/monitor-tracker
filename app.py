import streamlit as st
import pandas as pd
import gspread
import time
import json # <--- Nuevo ingrediente
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor de Proyectos", page_icon="🚀", layout="wide")

# Estilos CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00CC96;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Tablero de Control: Misión Educativa")
st.markdown("---")

# --- CONEXIÓN HÍBRIDA (NUBE / LOCAL) ---
@st.cache_data
def cargar_datos():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # LÓGICA INTELIGENTE DE CREDENCIALES
        # 1. Intenta buscar en la "Caja Fuerte" de la nube (Streamlit Secrets)
        if "google_credentials" in st.secrets:
            # Nota los espacios a la izquierda aquí abajo 👇
            key_dict = dict(st.secrets["google_credentials"])
            creds = Credentials.from_service_account_info(key_dict, scopes=scope)
        # 2. Si no, busca el archivo en tu compu (para cuando trabajás local)
        else:
            # Aquí también hay espacios 👇
            creds = Credentials.from_service_account_file("credenciales.json", scopes=scope)
            
        client = gspread.authorize(creds)
        
        # --- ¡CHEQUEÁ QUE TU ID ESTÉ ACÁ! ---
        spreadsheet_id = "1nfXLWBLfjIXznMIjlojpaAKD3bTRrThEvkjihCjwbUk" 
        
        sheet = client.open_by_key(spreadsheet_id).worksheet("TRACKER")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return str(e)

# --- FUNCIÓN INTELIGENTE PARA ENCONTRAR COLUMNAS ---
def buscar_columna(df, palabras_clave):
    for col in df.columns:
        if palabras_clave.lower() in col.lower():
            return col
    return None

# --- LÓGICA DE SECRETARIA VIRTUAL ---
def generar_asistente(df_criticos, col_estado, col_recursos, col_principal):
    st.info("🤖 **Asistente Virtual:** Analizando necesidades de hardware...")
    time.sleep(1.5)
    texto = "REPORTE DE RECURSOS:\n\n"
    
    for i, fila in df_criticos.iterrows():
        texto += f"📌 PROYECTO: {fila.get('Nombre del Proyecto', 'Sin nombre')}\n"
        texto += f"DOCENTE: {fila.get('Docentes Responsables', '')}\n"
        recurso = fila.get(col_principal, 'recurso no especificado')
        texto += f"ALERTA: Estado '{fila.get(col_recursos, '')}'. Se requiere gestionar: {recurso}.\n"
        texto += "-"*40 + "\n"
    return texto

# --- INTERFAZ PRINCIPAL ---
df_result = cargar_datos()

if isinstance(df_result, str):
    st.error(f"❌ Error de conexión: {df_result}")
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

    # 2. KPIS
    total = len(df)
    criticos = pd.DataFrame()
    if col_estado_recursos:
        criticos = df[df[col_estado_recursos] == "Faltante"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Proyectos Activos", total)
    col2.metric("🛑 Faltan Recursos", len(criticos), delta_color="inverse")
    
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
                # Semáforo de Recursos
                if col_estado_recursos:
                    est_rec = row[col_estado_recursos]
                    if est_rec == "Faltante":
                        st.error(f"🛑 Estado: {est_rec}")
                    elif est_rec == "A gestionar":
                        st.warning(f"✋ Estado: {est_rec}")
                    else:
                        st.success(f"✅ Estado: {est_rec}")
                
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
    if len(criticos) > 0:
        if st.button("⚡ Generar Reclamo de Recursos"):
            reporte = generar_asistente(criticos, col_estado, col_estado_recursos, col_recurso_principal)
            st.text_area("Copia este texto:", reporte, height=200)import streamlit as st
import pandas as pd
import gspread
import time
import json # <--- Nuevo ingrediente
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor de Proyectos", page_icon="🚀", layout="wide")

# Estilos CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00CC96;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Tablero de Control: Misión Educativa")
st.markdown("---")

# --- CONEXIÓN HÍBRIDA (NUBE / LOCAL) ---
@st.cache_data
def cargar_datos():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # LÓGICA INTELIGENTE DE CREDENCIALES
        # 1. Intenta buscar en la "Caja Fuerte" de la nube (Streamlit Secrets)
        if "google_credentials" in st.secrets:
            key_dict = json.loads(st.secrets["google_credentials"])
            creds = Credentials.from_service_account_info(key_dict, scopes=scope)
        # 2. Si no, busca el archivo en tu compu (para cuando trabajás local)
        else:
            creds = Credentials.from_service_account_file("credenciales.json", scopes=scope)
            
        client = gspread.authorize(creds)
        
        # --- ¡PEGÁ TU ID DE GOOGLE SHEETS AQUÍ ABAJO! ---
        spreadsheet_id = "1nfXLWBLfjIXznMIjlojpaAKD3bTRrThEvkjihCjwbUk" 
        
        sheet = client.open_by_key(spreadsheet_id).worksheet("TRACKER")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        return str(e)

# --- FUNCIÓN INTELIGENTE PARA ENCONTRAR COLUMNAS ---
def buscar_columna(df, palabras_clave):
    for col in df.columns:
        if palabras_clave.lower() in col.lower():
            return col
    return None

# --- LÓGICA DE SECRETARIA VIRTUAL ---
def generar_asistente(df_criticos, col_estado, col_recursos, col_principal):
    st.info("🤖 **Asistente Virtual:** Analizando necesidades de hardware...")
    time.sleep(1.5)
    texto = "REPORTE DE RECURSOS:\n\n"
    
    for i, fila in df_criticos.iterrows():
        texto += f"📌 PROYECTO: {fila.get('Nombre del Proyecto', 'Sin nombre')}\n"
        texto += f"DOCENTE: {fila.get('Docentes Responsables', '')}\n"
        recurso = fila.get(col_principal, 'recurso no especificado')
        texto += f"ALERTA: Estado '{fila.get(col_recursos, '')}'. Se requiere gestionar: {recurso}.\n"
        texto += "-"*40 + "\n"
    return texto

# --- INTERFAZ PRINCIPAL ---
df_result = cargar_datos()

if isinstance(df_result, str):
    st.error(f"❌ Error de conexión: {df_result}")
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

    # 2. KPIS
    total = len(df)
    criticos = pd.DataFrame()
    if col_estado_recursos:
        criticos = df[df[col_estado_recursos] == "Faltante"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Proyectos Activos", total)
    col2.metric("🛑 Faltan Recursos", len(criticos), delta_color="inverse")
    
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
                # Semáforo de Recursos
                if col_estado_recursos:
                    est_rec = row[col_estado_recursos]
                    if est_rec == "Faltante":
                        st.error(f"🛑 Estado: {est_rec}")
                    elif est_rec == "A gestionar":
                        st.warning(f"✋ Estado: {est_rec}")
                    else:
                        st.success(f"✅ Estado: {est_rec}")
                
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
    if len(criticos) > 0:
        if st.button("⚡ Generar Reclamo de Recursos"):
            reporte = generar_asistente(criticos, col_estado, col_estado_recursos, col_recurso_principal)
            st.text_area("Copia este texto:", reporte, height=200)




