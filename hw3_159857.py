#!/usr/bin/env python
# coding: utf-8

# In[6]:


#get_ipython().system('python --version')


# # Creación del enviroment

# In[2]:


#get_ipython().system('python -m venv env_hw3')
#get_ipython().system('env_hw3\\Scripts\\pip install jupyter ipykernel')
#get_ipython().system('env_hw3\\Scripts\\python -m ipykernel install --user --name=env_hw3 --display-name "Python (env_hw3)"')


# In[2]:


#get_ipython().run_line_magic('pip', 'install numpy streamlit matplotlib plotly pandas scipy ipykernel nbformat')


# In[1]:


#get_ipython().run_line_magic('pip', 'install folium streamlit_folium lxml geopandas')


# In[ ]:





# In[72]:


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# In[5]:


# app.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, MultiPolygon, Polygon
import os
import warnings
warnings.filterwarnings('ignore')


# # Pasar al excel en html

# In[7]:


import pandas as pd

archivo_html = 'listado_iiee.xls'  # sigue llamándose .xls pero es HTML internamente

### Cargar como si fuera HTML
df = pd.read_html(archivo_html)[0]  # [0] porque read_html devuelve una lista de tablas

### Mostrar el DataFrame
print(df.head())


# In[8]:


print(df.columns.tolist())


# In[ ]:





# In[20]:


from shapely.geometry import Point, MultiPolygon, Polygon, mapping
import os
import warnings
warnings.filterwarnings('ignore')
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap


# In[ ]:





# In[21]:


# Cargar los datos de escuelas
archivo_html = 'listado_iiee.xls'  # sigue llamándose .xls pero es HTML internamente
df = pd.read_html(archivo_html)[0]  # [0] porque read_html devuelve una lista de tablas

# Verificar los primeros registros
print(df.head())


# 

# In[36]:


# Limpieza inicial de datos
# Convertir latitud y longitud a valores numéricos
df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')

# Eliminar registros con coordenadas inválidas
df = df.dropna(subset=['Latitud', 'Longitud'])

# Verificar que nivel/modalidad contiene las categorías que necesitamos
print("Categorías de Nivel / Modalidad:")
print(df['Nivel / Modalidad'].unique())

# Crear una función para clasificar el nivel
def clasificar_nivel(nivel_modalidad):
    if 'Inicial' in nivel_modalidad:
        return 'Inicial'
    elif nivel_modalidad == 'Primaria':
        return 'Primaria'
    elif nivel_modalidad == 'Secundaria':
        return 'Secundaria'
    else:
        return 'Otro'


# In[37]:


# Crear una columna para identificar el nivel
df['Nivel'] = df['Nivel / Modalidad'].apply(clasificar_nivel)

# Filtrar solo las escuelas de los niveles requeridos
escuelas = df[df['Nivel'].isin(['Inicial', 'Primaria', 'Secundaria'])]

# Mostrar distribución después de la clasificación
print("\nDistribución después de la clasificación:")
print(escuelas['Nivel'].value_counts())


# In[38]:


# Convertir el dataframe a GeoDataFrame
from shapely.geometry import Point
geometry = [Point(xy) for xy in zip(escuelas['Longitud'], escuelas['Latitud'])]
escuelas_gdf = gpd.GeoDataFrame(escuelas, geometry=geometry, crs="EPSG:4326")

# Cargar los shapefiles de distritos de Perú
# Ajusta la ruta según la estructura de tu carpeta shape_file
distritos_path = 'shape_file/DISTRITOS.shp'
distritos_gdf = gpd.read_file(distritos_path)


# In[39]:


# Verificar las columnas del shapefile
print("\nColumnas del shapefile de distritos:")
print(distritos_gdf.columns.tolist())


# ### Acá elijo PROVINCIA

# In[40]:


# Verificar el CRS del shapefile de distritos
print(f"CRS de distritos: {distritos_gdf.crs}")

# Asegurar que ambos GeoDataFrames estén en el mismo CRS
if distritos_gdf.crs != escuelas_gdf.crs:
    distritos_gdf = distritos_gdf.to_crs(escuelas_gdf.crs)


# In[ ]:


#get_ipython().system('jupyter nbconvert --to script hw3_159857.ipynb')


# # 2. Geospatial Analysis with GeoPandas

# ####  ------ Task 1: Mapas estáticos por nivel escolar ------

# In[41]:


# Función para crear mapa de escuelas por distrito y nivel
def crear_mapa_escuelas(nivel, escuelas_gdf, distritos_gdf):
    # Filtrar escuelas por nivel
    escuelas_nivel = escuelas_gdf[escuelas_gdf['Nivel'] == nivel]
    
    # Contar escuelas por distrito
    escuelas_por_distrito = gpd.sjoin(escuelas_nivel, distritos_gdf, predicate='within')
    conteo = escuelas_por_distrito.groupby('DISTRITO').size().reset_index(name='conteo')
    
    # Unir el conteo con los distritos
    distritos_con_conteo = distritos_gdf.merge(conteo, left_on='DISTRITO', right_on='DISTRITO', how='left')
    distritos_con_conteo['conteo'] = distritos_con_conteo['conteo'].fillna(0)
    
    # Crear el mapa
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Definir colores según el nivel
    if nivel == 'Inicial':
        cmap = 'Blues'
        titulo = 'Escuelas de Nivel Inicial por Distrito'
    elif nivel == 'Primaria':
        cmap = 'Greens'
        titulo = 'Escuelas de Nivel Primaria por Distrito'
    else:  # Secundaria
        cmap = 'Reds'
        titulo = 'Escuelas de Nivel Secundaria por Distrito'
    
    # Crear mapa coroplético
    distritos_con_conteo.plot(column='conteo', cmap=cmap, linewidth=0.5, ax=ax, edgecolor='0.8',
                              legend=True, legend_kwds={'label': "Número de escuelas"})
    
    # Añadir título y ajustes estéticos
    ax.set_title(titulo, fontsize=15)
    ax.set_axis_off()
    
    # Guardar el mapa como imagen
    plt.savefig(f'mapa_{nivel.lower()}.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return distritos_con_conteo


# In[42]:


# Crear mapas para cada nivel
print("Creando mapas estáticos por nivel escolar...")
distritos_inicial = crear_mapa_escuelas('Inicial', escuelas_gdf, distritos_gdf)
distritos_primaria = crear_mapa_escuelas('Primaria', escuelas_gdf, distritos_gdf)
distritos_secundaria = crear_mapa_escuelas('Secundaria', escuelas_gdf, distritos_gdf)


# In[43]:


print("Mapas estáticos creados exitosamente.")


# In[ ]:





# ## ------ Task 2: Análisis de proximidad (Proximity Analysis) ------

# In[44]:


# Filtrar escuelas en Huancavelica y Ayacucho
regiones_interes = ['HUANCAVELICA', 'AYACUCHO']
escuelas_regiones = escuelas_gdf[escuelas_gdf['Departamento'].str.upper().isin(regiones_interes)]

# Separar escuelas primarias y secundarias
primarias = escuelas_regiones[escuelas_regiones['Nivel'] == 'Primaria']
secundarias = escuelas_regiones[escuelas_regiones['Nivel'] == 'Secundaria']


# In[45]:


print(f"Escuelas primarias en las regiones seleccionadas: {len(primarias)}")
print(f"Escuelas secundarias en las regiones seleccionadas: {len(secundarias)}")


# In[ ]:





# In[50]:


# Convertir a proyección UTM para cálculos de distancia en metros
# Perú está en la zona UTM 18S
utm_crs = 'EPSG:32718'  # UTM zona 18S
primarias_utm = primarias.to_crs(utm_crs)
secundarias_utm = secundarias.to_crs(utm_crs)

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

# Realizar el análisis de proximidad
print("Realizando análisis de proximidad... (esto puede tomar un tiempo)")
resultados_proximidad = contar_secundarias_cercanas(primarias_utm, secundarias_utm)

# Encontrar la escuela primaria con más y menos escuelas secundarias cercanas
primaria_max = resultados_proximidad.loc[resultados_proximidad['num_secundarias'].idxmax()]
primaria_min = resultados_proximidad.loc[resultados_proximidad['num_secundarias'].idxmin()]

print(f"Escuela primaria con más secundarias cercanas: {primaria_max['nombre_primaria']} ({primaria_max['num_secundarias']} escuelas)")
print(f"Escuela primaria con menos secundarias cercanas: {primaria_min['nombre_primaria']} ({primaria_min['num_secundarias']} escuelas)")

# Función para crear mapas de proximidad
def crear_mapa_proximidad(primaria_info, secundarias_utm, distritos_gdf, tipo="max"):
    # Preparar datos para el mapa
    primaria_punto = gpd.GeoDataFrame(geometry=[primaria_info['geometry']], crs=utm_crs)
    buffer = gpd.GeoDataFrame(geometry=[primaria_info['buffer']], crs=utm_crs)
    
    # Convertir a WGS84 para visualización
    primaria_punto = primaria_punto.to_crs("EPSG:4326")
    buffer = buffer.to_crs("EPSG:4326")
    
    # Obtener las secundarias dentro del buffer
    secundarias_dentro = primaria_info['secundarias_dentro'].to_crs("EPSG:4326")
    
    # Filtrar distritos para la región específica
    distrito_primaria = distritos_gdf[distritos_gdf['DISTRITO'] == primaria_info['distrito']]
    
    # Crear el mapa
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Dibujar el distrito
    distrito_primaria.plot(ax=ax, color='lightgray', edgecolor='black')
    
    # Dibujar el buffer
    buffer.plot(ax=ax, color='lightblue', alpha=0.5)
    
    # Dibujar las secundarias dentro del buffer
    if len(secundarias_dentro) > 0:
        secundarias_dentro.plot(ax=ax, color='red', markersize=50, marker='*', label='Escuelas Secundarias')
    
    # Dibujar la primaria
    primaria_punto.plot(ax=ax, color='blue', markersize=100, marker='^', label='Escuela Primaria')
    
    # Añadir leyenda y título
    if tipo == "max":
        titulo = f"Escuela Primaria con MÁS Escuelas Secundarias Cercanas\n{primaria_info['nombre_primaria']} - {primaria_info['num_secundarias']} escuelas dentro de 5km"
    else:
        titulo = f"Escuela Primaria con MENOS Escuelas Secundarias Cercanas\n{primaria_info['nombre_primaria']} - {primaria_info['num_secundarias']} escuelas dentro de 5km"
    
    ax.set_title(titulo, fontsize=12)
    ax.legend()
    ax.set_axis_off()
    
    # Guardar el mapa
    plt.savefig(f'mapa_proximidad_{tipo}.png', dpi=300, bbox_inches='tight')
    plt.close()

# Crear mapas de proximidad
print("Creando mapas de proximidad...")
crear_mapa_proximidad(primaria_max, secundarias_utm, distritos_gdf, tipo="max")
crear_mapa_proximidad(primaria_min, secundarias_utm, distritos_gdf, tipo="min")

print("Análisis geoespacial completado. Se han generado los mapas estáticos y de proximidad.")


# In[ ]:





# In[71]:


#get_ipython().system('jupyter nbconvert --to script hw3_159857.ipynb')


# In[ ]:





# In[ ]:





# In[ ]:




