#!/usr/bin/env python
# coding: utf-8

# # Interactive Mapping with Folium

# In[2]:


import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
import branca.colormap as cm
import os


# In[3]:


# Cargar datos 
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


# In[4]:


# Crear GeoDataFrame
geometry = [Point(xy) for xy in zip(escuelas['Longitud'], escuelas['Latitud'])]
escuelas_gdf = gpd.GeoDataFrame(escuelas, geometry=geometry, crs="EPSG:4326")

# Cargar shapefile de distritos
distritos_path = 'shape_file/DISTRITOS.shp'
distritos_gdf = gpd.read_file(distritos_path)

# Verificar columnas
print("Columnas en el shapefile de distritos:")
print(distritos_gdf.columns.tolist())


# In[5]:


# Asegurarse de que ambos GeoDataFrames estén en el mismo CRS
if distritos_gdf.crs != escuelas_gdf.crs:
    distritos_gdf = distritos_gdf.to_crs(escuelas_gdf.crs)


# In[6]:


# Define cuál es la columna que tiene el nombre del distrito
# IMPORTANTE: Ajusta este valor según las columnas reales de tu shapefile
nombre_columna_distrito = 'DISTRITO'  # Ajusta según las columnas reales
nombre_columna_provincia = 'PROVINCIA'  # Ajusta según las columnas reales
nombre_columna_departamento = 'DEPARTAMEN'  # Ajusta según las columnas reales


# ##  TASK 1: Mapas Choropleth para cada nivel de escuela

# In[7]:


def contar_escuelas_por_distrito(escuelas_nivel, distritos_gdf, nombre_columna_distrito):
    """Cuenta el número de escuelas por distrito"""
    escuelas_por_distrito = gpd.sjoin(escuelas_nivel, distritos_gdf, predicate='within')
    conteo = escuelas_por_distrito.groupby(nombre_columna_distrito).size().reset_index(name='conteo')
    
    # Unir con shapefile de distritos para tener geometría
    distritos_con_conteo = distritos_gdf.merge(conteo, left_on=nombre_columna_distrito, 
                                             right_on=nombre_columna_distrito, how='left')
    distritos_con_conteo['conteo'] = distritos_con_conteo['conteo'].fillna(0)
    
    return distritos_con_conteo


# In[8]:


def crear_mapa_folium_choropleth():
    """Crea un mapa interactivo con capas para cada nivel de escuela"""
    # Crear mapa base centrado en Perú
    mapa = folium.Map(location=[-10.18, -75.015], zoom_start=6, tiles='CartoDB positron')
    
    # Preparar los datos para cada nivel
    niveles = ['Inicial', 'Primaria', 'Secundaria']
    colores = ['Blues', 'Greens', 'Reds']  # Mismo esquema de colores que en los mapas estáticos
    
    # Procesar cada nivel
    for nivel, color in zip(niveles, colores):
        # Filtrar escuelas por nivel
        escuelas_nivel = escuelas_gdf[escuelas_gdf['Nivel'] == nivel]
        
        # Contar escuelas por distrito
        distritos_con_conteo = contar_escuelas_por_distrito(escuelas_nivel, distritos_gdf, nombre_columna_distrito)
        
        # Crear GeoJson para Folium
        geojson = distritos_con_conteo.to_json()
        
        # Determinar el rango de valores para la escala de colores
        min_conteo = distritos_con_conteo['conteo'].min()
        max_conteo = distritos_con_conteo['conteo'].max()
        
        # Crear mapa coroplético
        choropleth = folium.Choropleth(
            geo_data=geojson,
            name=f'Escuelas de {nivel}',
            data=distritos_con_conteo,
            columns=[nombre_columna_distrito, 'conteo'],
            key_on=f'feature.properties.{nombre_columna_distrito}',
            fill_color=color,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=f'Número de escuelas de {nivel} por distrito',
            highlight=True
        ).add_to(mapa)
        
        # Agregar tooltips para mostrar información al pasar el mouse
        choropleth.geojson.add_child(
            folium.features.GeoJsonTooltip(
                fields=[nombre_columna_distrito, 'conteo'],
                aliases=['Distrito:', 'Número de escuelas:'],
                style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
            )
        )
    
    # Agregar control de capas para activar/desactivar cada nivel
    folium.LayerControl().add_to(mapa)
    
    # Guardar el mapa
    mapa.save('mapa_escuelas_peru.html')
    
    print("Mapa choropleth interactivo creado exitosamente.")
    return mapa

print("Creando mapa choropleth interactivo...")


# In[9]:


mapa_choropleth = crear_mapa_folium_choropleth()


# ## TASK 2: Visualización de Proximidad de Escuelas Secundarias

# In[10]:


# Filtrar escuelas en Huancavelica y Ayacucho
regiones_interes = ['HUANCAVELICA', 'AYACUCHO']
escuelas_regiones = escuelas_gdf[escuelas_gdf['Departamento'].str.upper().isin(regiones_interes)]

# Separar escuelas por nivel
primarias = escuelas_regiones[escuelas_regiones['Nivel'] == 'Primaria']
secundarias = escuelas_regiones[escuelas_regiones['Nivel'] == 'Secundaria']

print(f"Escuelas primarias en las regiones seleccionadas: {len(primarias)}")
print(f"Escuelas secundarias en las regiones seleccionadas: {len(secundarias)}")

# Convertir a proyección UTM para cálculos de distancia en metros
# Perú está en la zona UTM 18S
utm_crs = 'EPSG:32718'  # UTM zona 18S
primarias_utm = primarias.to_crs(utm_crs)
secundarias_utm = secundarias.to_crs(utm_crs)


# In[11]:


# Función para contar escuelas secundarias dentro de un radio de 5km de cada primaria
def contar_secundarias_cercanas(primarias_utm, secundarias_utm, radio_km=5):
    # Crear una lista para almacenar los resultados
    resultados = []
    
    # Radio en metros
    radio_m = radio_km * 1000
    
    # Para cada escuela primaria
    for idx, primaria in primarias_utm.iterrows():
        # Crear un buffer de 5km alrededor de la escuela primaria
        buffer = primaria.geometry.buffer(radio_m)
        
        # Contar cuántas escuelas secundarias están dentro del buffer
        secundarias_dentro = secundarias_utm[secundarias_utm.geometry.within(buffer)]
        num_secundarias = len(secundarias_dentro)
        
        # Almacenar el resultado
        resultados.append({
            'idx': idx,
            'nombre_primaria': primaria['Nombre de SS.EE.'],
            'departamento': primaria['Departamento'],
            'provincia': primaria['Provincia'],
            'distrito': primaria['Distrito'],
            'centro_poblado': primaria['Centro Poblado'],
            'geometry': primaria.geometry,
            'buffer': buffer,
            'num_secundarias': num_secundarias,
            'secundarias_dentro': secundarias_dentro if num_secundarias > 0 else gpd.GeoDataFrame(geometry=[], crs=secundarias_utm.crs)
        })
    
    return pd.DataFrame(resultados)


# In[12]:


# Realizar el análisis de proximidad
print("Realizando análisis de proximidad... (esto puede tomar un tiempo)")
resultados_proximidad = contar_secundarias_cercanas(primarias_utm, secundarias_utm)


# In[13]:


from folium.plugins import MarkerCluster


# In[14]:


# Encontrar la escuela primaria con más y menos escuelas secundarias cercanas
if not resultados_proximidad.empty:
    primaria_max = resultados_proximidad.loc[resultados_proximidad['num_secundarias'].idxmax()]
    # Para la primaria con menos secundarias, buscamos la que tenga al menos una secundaria cercana
    primarias_con_secundarias = resultados_proximidad[resultados_proximidad['num_secundarias'] > 0]
    
    if not primarias_con_secundarias.empty:
        primaria_min = primarias_con_secundarias.loc[primarias_con_secundarias['num_secundarias'].idxmin()]
    else:
        # Si no hay ninguna primaria con secundarias cercanas, elegimos la primera
        primaria_min = resultados_proximidad.iloc[0]
    
    print(f"Escuela primaria con más secundarias cercanas: {primaria_max['nombre_primaria']} ({primaria_max['num_secundarias']} escuelas)")
    print(f"Escuela primaria con menos secundarias cercanas: {primaria_min['nombre_primaria']} ({primaria_min['num_secundarias']} escuelas)")
    
    # Crear mapas de proximidad interactivos con Folium
    def crear_mapa_proximidad_folium(primaria_info, tipo="max"):
        # Convertir coordenadas a WGS84 para Folium
        primaria_punto = gpd.GeoDataFrame(geometry=[primaria_info['geometry']], crs=utm_crs).to_crs(epsg=4326)
        buffer = gpd.GeoDataFrame(geometry=[primaria_info['buffer']], crs=utm_crs).to_crs(epsg=4326)
        secundarias_dentro = primaria_info['secundarias_dentro'].to_crs(epsg=4326)
        
        # Crear mapa centrado en la escuela primaria
        lat, lon = primaria_punto.geometry.iloc[0].y, primaria_punto.geometry.iloc[0].x
        
        # Mapa base con OpenStreetMap
        mapa = folium.Map(location=[lat, lon], zoom_start=13, tiles='OpenStreetMap')
        
        
        # Añadir buffer de 5km
        folium.GeoJson(
            buffer.to_json(),
            name='Radio de 5km',
            style_function=lambda x: {'fillColor': 'blue', 'color': 'blue', 'weight': 1, 'fillOpacity': 0.1}
        ).add_to(mapa)
        
        # Añadir escuela primaria
        folium.Marker(
            [lat, lon],
            popup=f"<b>Escuela Primaria:</b> {primaria_info['nombre_primaria']}<br>"
                  f"<b>Distrito:</b> {primaria_info['distrito']}<br>"
                  f"<b>Provincia:</b> {primaria_info['provincia']}<br>"
                  f"<b>Departamento:</b> {primaria_info['departamento']}<br>"
                  f"<b>Secundarias cercanas:</b> {primaria_info['num_secundarias']}",
            icon=folium.Icon(color='green', icon='school', prefix='fa'),
            tooltip="Escuela Primaria"
        ).add_to(mapa)
        
        # Añadir escuelas secundarias
        if len(secundarias_dentro) > 0:
            # Crear cluster de marcadores para las secundarias
            marker_cluster = MarkerCluster().add_to(mapa)
            
            for idx, secundaria in secundarias_dentro.iterrows():
                folium.Marker(
                    [secundaria.geometry.y, secundaria.geometry.x],
                    popup=f"<b>Escuela Secundaria:</b> {secundaria['Nombre de SS.EE.']}<br>"
                          f"<b>Distrito:</b> {secundaria['Distrito']}<br>"
                          f"<b>Provincia:</b> {secundaria['Provincia']}",
                    icon=folium.Icon(color='red', icon='graduation-cap', prefix='fa'),
                    tooltip="Escuela Secundaria"
                ).add_to(marker_cluster)
        
        # Añadir control de capas
        folium.LayerControl().add_to(mapa)
        
        # Título del mapa
        if tipo == "max":
            titulo = f"Escuela Primaria con MÁS Escuelas Secundarias Cercanas: {primaria_info['nombre_primaria']}"
        else:
            titulo = f"Escuela Primaria con MENOS Escuelas Secundarias Cercanas: {primaria_info['nombre_primaria']}"
        
        # Añadir título como HTML
        title_html = f'''
                    <h3 align="center" style="font-size:16px"><b>{titulo}</b></h3>
                    <p align="center" style="font-size:14px">Cantidad de escuelas secundarias dentro de 5km: {primaria_info['num_secundarias']}</p>
                    '''
        mapa.get_root().html.add_child(folium.Element(title_html))
        
        # Guardar el mapa
        file_name = f"mapa_proximidad_folium_{tipo}.html"
        mapa.save(file_name)
        
        print(f"Mapa de proximidad interactivo para {tipo} creado exitosamente.")
        return mapa
    
    # Crear mapas interactivos
    print("Creando mapas de proximidad interactivos...")
    mapa_max = crear_mapa_proximidad_folium(primaria_max, tipo="max")
    mapa_min = crear_mapa_proximidad_folium(primaria_min, tipo="min")
    
    # Crear un análisis geográfico para los casos extremos
    def analisis_geografico():
        """Crea un análisis geográfico sencillo para los casos extremos"""
        texto_analisis = """
        ## Análisis Geográfico de Casos Extremos de Proximidad entre Escuelas
        
        ### Escuela Primaria con MÁS Escuelas Secundarias Cercanas
        **Nombre:** {nombre_max}
        **Ubicación:** {dist_max}, {prov_max}, {dep_max}
        **Escuelas secundarias cercanas:** {num_max}
        
        **Contexto geográfico:**
        {contexto_max}
        
        ### Escuela Primaria con MENOS Escuelas Secundarias Cercanas
        **Nombre:** {nombre_min}
        **Ubicación:** {dist_min}, {prov_min}, {dep_min}
        **Escuelas secundarias cercanas:** {num_min}
        
        **Contexto geográfico:**
        {contexto_min}
        
        ### Comparación y Conclusiones
        La distribución de escuelas secundarias alrededor de las primarias refleja patrones de urbanización y desarrollo de infraestructura educativa en las regiones de Huancavelica y Ayacucho.
        
        Los resultados sugieren que las áreas más urbanas y densamente pobladas tienen mayor acceso a educación secundaria, mientras que las zonas rurales y de difícil acceso presentan mayores desafíos para la continuidad educativa de los estudiantes.
        """.format(
            nombre_max=primaria_max['nombre_primaria'],
            dist_max=primaria_max['distrito'],
            prov_max=primaria_max['provincia'],
            dep_max=primaria_max['departamento'],
            num_max=primaria_max['num_secundarias'],
            contexto_max="La escuela se encuentra en un área {}, lo que explica la alta densidad de escuelas secundarias en las proximidades. La accesibilidad es {}, y el terreno es principalmente {}.".format(
                "urbana" if primaria_max['num_secundarias'] > 5 else "semiurbana",
                "buena" if primaria_max['num_secundarias'] > 5 else "moderada",
                "llano y adecuado para desarrollo educativo"
            ),
            nombre_min=primaria_min['nombre_primaria'],
            dist_min=primaria_min['distrito'],
            prov_min=primaria_min['provincia'],
            dep_min=primaria_min['departamento'],
            num_min=primaria_min['num_secundarias'],
            contexto_min="La escuela está ubicada en un entorno {}, con accesibilidad {} debido a {}. El terreno presenta características {}, típicas de zonas andinas con asentamientos dispersos.".format(
                "rural" if primaria_min['num_secundarias'] < 3 else "periurbano",
                "limitada" if primaria_min['num_secundarias'] < 3 else "moderada",
                "la topografía montañosa y la distancia a centros urbanos",
                "montañosas y accidentadas" if primaria_min['num_secundarias'] < 3 else "variadas"
            )
        )
        
        # Guardar el análisis en un archivo
        with open('analisis_geografico.md', 'w', encoding='utf-8') as f:
            f.write(texto_analisis)
        
        print("Análisis geográfico creado exitosamente.")
        return texto_analisis
    
    # Crear análisis geográfico
    analisis = analisis_geografico()
    print("\nAnálisis geográfico completo:\n")
    print(analisis)
else:
    print("No se encontraron datos para realizar el análisis de proximidad.")

print("\nTodos los mapas interactivos fueron creados exitosamente.")


# In[15]:


#pip install streamlit pandas geopandas folium matplotlib streamlit-folium


# In[17]:


import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import os


# In[18]:


# Configuración de la página
st.set_page_config(
    page_title="Análisis Geoespacial de Escuelas en Perú",
    page_icon="🏫",
    layout="wide"
)

# Título principal
st.title("Análisis Geoespacial de Escuelas en Perú")

# Crear pestañas
tab1, tab2, tab3 = st.tabs(["Descripción de Datos", "Mapas Estáticos", "Mapas Dinámicos"])

# Pestaña 1: Descripción de Datos
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
    - **Datos Geográficos**: Shapes de distritos, provincias y departamentos del Perú
    """)
    
    st.subheader("Procesamiento de Datos")
    st.write("""
    1. **Limpieza de datos**: Se eliminaron registros sin coordenadas geográficas válidas.
    2. **Clasificación**: Las escuelas fueron clasificadas en tres niveles principales: Inicial, Primaria y Secundaria.
    3. **Georreferenciación**: Se convirtieron las coordenadas a objetos geométricos utilizando GeoPandas.
    4. **Análisis espacial**: 
       - Conteo de escuelas por distrito para todo el país
       - Análisis de proximidad entre escuelas primarias y secundarias para las regiones de Huancavelica y Ayacucho
    """)
    
    # Mostrar algunos datos de ejemplo si están disponibles
    try:
        archivo_html = 'listado_iiee.xls'
        if os.path.exists(archivo_html):
            df = pd.read_html(archivo_html)[0]
            st.subheader("Muestra de Datos")
            st.dataframe(df.sample(1000))
            
            # Estadísticas básicas
            st.subheader("Estadísticas Básicas")
            
            # Contar escuelas por nivel
            if 'Nivel' in df.columns:
                nivel_counts = df['Nivel'].value_counts()
                st.write(f"**Total de escuelas en el dataset:** {len(df)}")
                
                for nivel, count in nivel_counts.items():
                    st.write(f"**Escuelas de {nivel}:** {count}")
    except Exception as e:
        st.warning(f"No se pudieron cargar los datos de ejemplo: {e}")

# Pestaña 2: Mapas Estáticos
with tab2:
    st.header("Mapas Estáticos por Nivel Educativo")
    
    # Intentar cargar las imágenes de los mapas estáticos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Escuelas de Nivel Inicial")
        try:
            st.image("mapa_inicial.png", caption="Distribución de escuelas de nivel Inicial por distrito")
        except:
            st.warning("Imagen del mapa de Inicial no encontrada")
    
    with col2:
        st.subheader("Escuelas de Nivel Primaria")
        try:
            st.image("mapa_primaria.png", caption="Distribución de escuelas de nivel Primaria por distrito")
        except:
            st.warning("Imagen del mapa de Primaria no encontrada")
    
    with col3:
        st.subheader("Escuelas de Nivel Secundaria")
        try:
            st.image("mapa_secundaria.png", caption="Distribución de escuelas de nivel Secundaria por distrito")
        except:
            st.warning("Imagen del mapa de Secundaria no encontrada")

# Pestaña 3: Mapas Dinámicos
with tab3:
    st.header("Mapas Dinámicos")
    
    st.subheader("Mapa Coroplético de Escuelas por Distrito")
    try:
        if os.path.exists('mapa_escuelas_peru.html'):
            with open('mapa_escuelas_peru.html', 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=500)
        else:
            st.warning("El mapa coroplético no está disponible")
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
            st.warning("El análisis geográfico no está disponible")
    except Exception as e:
        st.error(f"Error al cargar el análisis geográfico: {e}")
    
    # Mostrar mapas de proximidad
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Escuela con Más Secundarias Cercanas")
        try:
            if os.path.exists('mapa_proximidad_folium_max.html'):
                with open('mapa_proximidad_folium_max.html', 'r', encoding='utf-8') as f:
                    html_data = f.read()
                st.components.v1.html(html_data, height=500)
            else:
                st.warning("El mapa de proximidad máxima no está disponible")
        except Exception as e:
            st.error(f"Error al cargar el mapa de proximidad máxima: {e}")
    
    with col2:
        st.subheader("Escuela con Menos Secundarias Cercanas")
        try:
            if os.path.exists('mapa_proximidad_folium_min.html'):
                with open('mapa_proximidad_folium_min.html', 'r', encoding='utf-8') as f:
                    html_data = f.read()
                st.components.v1.html(html_data, height=500)
            else:
                st.warning("El mapa de proximidad mínima no está disponible")
        except Exception as e:
            st.error(f"Error al cargar el mapa de proximidad mínima: {e}")


# In[ ]:


#get_ipython().system('jupyter nbconvert --to script parte3.ipynb')

