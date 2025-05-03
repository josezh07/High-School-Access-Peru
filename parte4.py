#!/usr/bin/env python
# coding: utf-8

# # 4. Application Deployment with Streamlit

# In[2]:


import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
import os
import warnings
warnings.filterwarnings('ignore')


# In[4]:


# ## Configuración de la página
st.set_page_config(
    page_title="Análisis Geoespacial de Escuelas en Perú",
    page_icon="🏫",
    layout="wide"
)


# In[5]:


# ## Título principal
st.title("Análisis Geoespacial de Escuelas en Perú")

# ## Funciones de carga y procesamiento de datos
@st.cache_data
def cargar_datos():
    """Carga y procesa los datos de escuelas"""
    try:
        # Cargar datos de escuelas
        archivo_html = 'listado_iiee.xls'
        df = pd.read_html(archivo_html)[0]
        
        # Limpieza de datos
        df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
        df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')
        df = df.dropna(subset=['Latitud', 'Longitud'])
        
        # Clasificar por nivel
        def clasificar_nivel(nivel_modalidad):
            if 'Inicial' in nivel_modalidad:
                return 'Inicial'
            elif nivel_modalidad == 'Primaria':
                return 'Primaria'
            elif nivel_modalidad == 'Secundaria':
                return 'Secundaria'
            else:
                return 'Otro'
        
        df['Nivel'] = df['Nivel / Modalidad'].apply(clasificar_nivel)
        escuelas = df[df['Nivel'].isin(['Inicial', 'Primaria', 'Secundaria'])]
        
        # Crear GeoDataFrame
        geometry = [Point(xy) for xy in zip(escuelas['Longitud'], escuelas['Latitud'])]
        escuelas_gdf = gpd.GeoDataFrame(escuelas, geometry=geometry, crs="EPSG:4326")
        
        return df, escuelas_gdf
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return None, None

@st.cache_data
def cargar_distritos():
    """Carga los datos de distritos"""
    try:
        # Cargar shapefile de distritos
        distritos_path = 'shape_file/DISTRITOS.shp'
        distritos_gdf = gpd.read_file(distritos_path)
        return distritos_gdf
    except Exception as e:
        st.error(f"Error al cargar los distritos: {e}")
        return None

# ## Carga de datos
with st.spinner('Cargando datos...'):
    df, escuelas_gdf = cargar_datos()
    distritos_gdf = cargar_distritos()

# ## Creación de pestañas
tab1, tab2, tab3 = st.tabs(["Descripción de Datos", "Mapas Estáticos", "Mapas Dinámicos"])

# ## Pestaña 1: Descripción de Datos
with tab1:
    st.header("Descripción de los Datos")
    
    st.subheader("Unidad de Análisis")
    st.write("""
    Este análisis se centra en la distribución geoespacial de instituciones educativas en Perú, 
    específicamente escuelas de nivel Inicial, Primaria y Secundaria. La unidad de análisis es 
    la institución educativa, georreferenciada por sus coordenadas de latitud y longitud.
    """)
    
    st.subheader("Fuentes de Datos")
    st.write("""
    - **Datos de Escuelas**: Ministerio de Educación de Perú (MINEDU) a través del 
    [Mapa Educativo](https://sigmed.minedu.gob.pe/mapaeducativo/)
    - **Datos Geográficos**: Shapes de distritos, provincias y departamentos del Perú obtenidos
    de fuentes oficiales como el Instituto Geográfico Nacional del Perú (IGN) o el Instituto 
    Nacional de Estadística e Informática (INEI).
    """)
    
    st.subheader("Metodología y Procesamiento")
    st.write("""
    1. **Limpieza de datos**: 
       - Eliminación de registros sin coordenadas geográficas válidas
       - Normalización de nombres y categorías
       
    2. **Clasificación**: 
       - Las escuelas fueron clasificadas en tres niveles principales: Inicial, Primaria y Secundaria
       - Se utilizó la columna 'Nivel / Modalidad' para realizar esta clasificación
       
    3. **Georreferenciación**: 
       - Conversión de coordenadas a objetos geométricos utilizando GeoPandas
       - Asignación del sistema de referencia de coordenadas EPSG:4326 (WGS84)
       
    4. **Análisis espacial**: 
       - Conteo de escuelas por distrito para todo el país
       - Análisis de proximidad entre escuelas primarias y secundarias (radio de 5km)
       - Enfoque especial en las regiones de Huancavelica y Ayacucho
    """)
    
    # Mostrar muestra de datos si están disponibles
    if df is not None:
        st.subheader("Muestra de Datos")
        st.dataframe(df.head())
        
        # Estadísticas básicas
        st.subheader("Estadísticas Básicas")
        
        # Distribución por nivel educativo
        if 'Nivel' in df.columns:
            total_escuelas = len(df)
            nivel_counts = df['Nivel'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Total de escuelas en el dataset:** {total_escuelas}")
                for nivel, count in nivel_counts.items():
                    if nivel in ['Inicial', 'Primaria', 'Secundaria', 'Otro']:
                        st.write(f"**Escuelas de {nivel}:** {count} ({count/total_escuelas*100:.1f}%)")
            
            with col2:
                # Gráfico de distribución por nivel
                fig, ax = plt.subplots(figsize=(8, 6))
                nivel_counts.plot(kind='bar', color=['#1f77b4', '#2ca02c', '#d62728', '#7f7f7f'])
                plt.title('Distribución de Escuelas por Nivel Educativo')
                plt.ylabel('Cantidad de Escuelas')
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # Distribución por departamento (top 10)
        if 'Departamento' in df.columns:
            st.subheader("Distribución por Departamento (Top 10)")
            dept_counts = df['Departamento'].value_counts().head(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            dept_counts.plot(kind='barh', color='#ff7f0e')
            plt.title('Top 10 Departamentos por Número de Escuelas')
            plt.xlabel('Cantidad de Escuelas')
            st.pyplot(fig)

# ## Pestaña 2: Mapas Estáticos
with tab2:
    st.header("Mapas Estáticos por Nivel Educativo")
    
    st.write("""
    Estos mapas muestran la distribución geográfica de las escuelas en Perú según su nivel educativo.
    Cada mapa utiliza una escala de colores diferente para representar la cantidad de escuelas por distrito.
    """)
    
    # Intentar cargar las imágenes de los mapas estáticos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Escuelas de Nivel Inicial")
        try:
            st.image("mapa_inicial.png", caption="Distribución de escuelas de nivel Inicial por distrito", use_column_width=True)
        except Exception as e:
            st.warning(f"No se pudo cargar el mapa de Inicial: {e}")
    
    with col2:
        st.subheader("Escuelas de Nivel Primaria")
        try:
            st.image("mapa_primaria.png", caption="Distribución de escuelas de nivel Primaria por distrito", use_column_width=True)
        except Exception as e:
            st.warning(f"No se pudo cargar el mapa de Primaria: {e}")
    
    with col3:
        st.subheader("Escuelas de Nivel Secundaria")
        try:
            st.image("mapa_secundaria.png", caption="Distribución de escuelas de nivel Secundaria por distrito", use_column_width=True)
        except Exception as e:
            st.warning(f"No se pudo cargar el mapa de Secundaria: {e}")
    
    # Mapas de proximidad
    st.header("Análisis de Proximidad: Escuelas Primarias y Secundarias")
    
    st.write("""
    Los siguientes mapas muestran el análisis de proximidad entre escuelas primarias y secundarias
    en las regiones de Huancavelica y Ayacucho. Se identificaron las escuelas primarias con mayor
    y menor número de escuelas secundarias en un radio de 5 km.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            st.image("mapa_proximidad_max.png", caption="Escuela primaria con más escuelas secundarias cercanas", use_column_width=True)
        except Exception as e:
            st.warning(f"No se pudo cargar el mapa de proximidad máxima: {e}")
            
    with col2:
        try:
            st.image("mapa_proximidad_min.png", caption="Escuela primaria con menos escuelas secundarias cercanas", use_column_width=True)
        except Exception as e:
            st.warning(f"No se pudo cargar el mapa de proximidad mínima: {e}")

# ## Pestaña 3: Mapas Dinámicos
with tab3:
    st.header("Mapas Dinámicos Interactivos")
    
    st.write("""
    Los mapas interactivos permiten explorar en detalle la distribución de escuelas en Perú.
    Puede acercar, alejar y hacer clic en los elementos para obtener más información.
    """)
    
    st.subheader("Mapa Coroplético de Escuelas por Distrito")
    try:
        if os.path.exists('mapa_escuelas_peru.html'):
            with open('mapa_escuelas_peru.html', 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=500)
        else:
            st.warning("El mapa coroplético interactivo no está disponible")
            st.info("Para generar este mapa, ejecute el script de análisis geoespacial con Folium")
    except Exception as e:
        st.error(f"Error al cargar el mapa coroplético: {e}")
    
    st.subheader("Análisis de Proximidad en Huancavelica y Ayacucho")
    
    # Mostrar el análisis geográfico si está disponible
    try:
        if os.path.exists('analisis_geografico.md'):
            with open('analisis_geografico.md', 'r', encoding='utf-8') as f:
                analisis = f.read()
            st.markdown(analisis)
        else:
            st.write("""
            ### Análisis Geográfico de Casos Extremos de Proximidad entre Escuelas
            
            Este análisis examina los casos extremos de proximidad entre escuelas primarias y secundarias
            en las regiones de Huancavelica y Ayacucho. Se identificaron las escuelas primarias con el mayor
            y menor número de escuelas secundarias en un radio de 5 km.
            
            El análisis considera factores como:
            - Ubicación urbana vs. rural
            - Accesibilidad y topografía
            - Densidad poblacional
            - Desarrollo de infraestructura educativa
            
            Los resultados muestran un claro contraste entre zonas urbanas con buena cobertura educativa
            y zonas rurales con acceso limitado a educación secundaria, reflejando desafíos de desarrollo
            educativo en regiones andinas de Perú.
            """)
    except Exception as e:
        st.error(f"Error al cargar el análisis geográfico: {e}")
    
    # Mostrar mapas de proximidad interactivos
    st.subheader("Mapas de Proximidad Interactivos")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Escuela con Mayor Número de Secundarias Cercanas**")
        try:
            if os.path.exists('mapa_proximidad_folium_max.html'):
                with open('mapa_proximidad_folium_max.html', 'r', encoding='utf-8') as f:
                    html_data = f.read()
                st.components.v1.html(html_data, height=500)
            else:
                st.warning("El mapa interactivo de proximidad máxima no está disponible")
                st.info("Este mapa muestra la escuela primaria con más escuelas secundarias en un radio de 5 km")
        except Exception as e:
            st.error(f"Error al cargar el mapa interactivo: {e}")
    
    with col2:
        st.write("**Escuela con Menor Número de Secundarias Cercanas**")
        try:
            if os.path.exists('mapa_proximidad_folium_min.html'):
                with open('mapa_proximidad_folium_min.html', 'r', encoding='utf-8') as f:
                    html_data = f.read()
                st.components.v1.html(html_data, height=500)
            else:
                st.warning("El mapa interactivo de proximidad mínima no está disponible")
                st.info("Este mapa muestra la escuela primaria con menos escuelas secundarias en un radio de 5 km")
        except Exception as e:
            st.error(f"Error al cargar el mapa interactivo: {e}")

# ## Footer
st.markdown("---")
st.markdown("**Análisis Geoespacial de Escuelas en Perú** | Tarea 3 | Curso de Análisis Geoespacial")


# In[ ]:


#get_ipython().system('jupyter nbconvert --to script parte4.ipynb')







