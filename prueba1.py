#import matplotlib
#matplotlib.use("TkAgg")

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.collections import PolyCollection

# 1. Cargar el GeoJSON
world = gpd.read_file("custom.geo.json")

# 2. Crear la ventana y configurar el lienzo estático
fig, ax = plt.subplots(figsize=(16, 8))
fig.patch.set_facecolor('#f8f9fa')  # Fondo de la ventana
ax.set_facecolor('#ecf0f1')         # Fondo del océano

# 3. Dibujar el mapa base UNA SOLA VEZ al inicio
world.plot(
    ax=ax,
    color="#2c3e50",       # Color de los países
    edgecolor="#34495e",   # Color de las fronteras
    linewidth=0.6
)

# ─── CONGELACIÓN TOTAL DE LA GEOMETRÍA ───
ax.axis("off")
limites_x = ax.get_xlim()
limites_y = ax.get_ylim()

# Fijamos los límites para que NADA altere el tamaño de la ventana
ax.set_xlim(limites_x)
ax.set_ylim(limites_y)
ax.set_autoscale_on(False)
# ─────────────────────────────────────────

# Texto indicador en miniatura (dentro del mapa, escala fija)
texto_titulo = ax.text(
    0.5, 0.95, "🌎 MAPA MUNDI INTERACTIVO NATIVO",
    transform=ax.transAxes,
    fontsize=11,
    color="#2c3e50",
    weight="bold",
    ha="center",
    va="center"
)

# Variables de control
pais_actual = None
objeto_iluminacion = None  # Aquí guardamos el parche de color de forma segura

# 4. Función de actualización limpia (Matplotlib puro)
def actualizar_iluminacion(pais=None):
    global objeto_iluminacion
    
    # 1. Remueve la iluminación anterior de forma segura si existe
    if objeto_iluminacion is not None:
        objeto_iluminacion.remove()
        objeto_iluminacion = None

    # 2. Si hay un país seleccionado, extraemos sus polígonos puros
    if pais is not None:
        seleccionado = world[world["name"] == pais]
        
        if not seleccionado.empty:
            geometria = seleccionado.geometry.iloc[0]
            coordenadas = []
            
            # Extraer las coordenadas exactas según si el país es un Polígono o MultiPolígono
            if geometria.geom_type == 'Polygon':
                coordenadas.append(list(geometria.exterior.coords))
            elif geometria.geom_type == 'MultiPolygon':
                for polígono in geometria.geoms:
                    coordenadas.append(list(polígono.exterior.coords))
            
            # Creamos la colección de polígonos nativa de Matplotlib
            objeto_iluminacion = PolyCollection(
                coordenadas, 
                facecolors='#e67e22', 
                edgecolors='white', 
                linewidths=1.0
            )
            
            # Agregamos la iluminación directamente encima del mapa base sin recalcular nada
            ax.add_collection(objeto_iluminacion)
            texto_titulo.set_text(f"🌍 {pais.upper()}")
    else:
        texto_titulo.set_text("🌎 MAPA MUNDI INTERACTIVO NATIVO")

    # 3. Forzar el zoom original para evitar cualquier intento de reajuste
    ax.set_xlim(limites_x)
    ax.set_ylim(limites_y)

# 5. Detectar movimiento del mouse
def mover_mouse(event):
    global pais_actual

    if event.xdata is None or event.ydata is None:
        return

    punto = Point(event.xdata, event.ydata)
    seleccionado = world[world.geometry.intersects(punto)]

    if not seleccionado.empty:
        nombre = seleccionado.iloc[0]["name"]

        if nombre != pais_actual:
            pais_actual = nombre
            actualizar_iluminacion(nombre)
            fig.canvas.draw_idle()  # Refresco de pantalla fluido e inteligente
    else:
        if pais_actual is not None:
            pais_actual = None
            actualizar_iluminacion()
            fig.canvas.draw_idle()

# Conectar el evento de movimiento
fig.canvas.mpl_connect("motion_notify_event", mover_mouse)

plt.show()