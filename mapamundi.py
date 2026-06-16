#import matplotlib
#matplotlib.use("TkAgg")

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.collections import PolyCollection

plt.ion()

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
    0.5, 0.98, " MAPA MUNDI INTERACTIVO NATIVO",
    transform=ax.transAxes,
    fontsize=11,
    color="#2c3e50",
    weight="bold",
    ha="center",
    va="center"
)

class Mapa():
    def __init__(self):
        self.punto_actual = Point(0, 0)

        # Variables de control
        self.pais_actual = None
        self.objeto_iluminacion = None  # Aquí guardamos el parche de color de forma segura

        # Dibujamos un punto rojo ('ro') con tamaño 10 (ms=10) y una capa alta (zorder=5)
        # para que siempre quede por encima de los mapas y las fronteras.
        self.marcador_mano, = ax.plot([], [], 'ro', ms=10, zorder=5, label="Tu Mano")

        # 3. Mostrar la ventana desde el constructor de forma explícitamente NO bloqueante
        plt.show(block=False)
        plt.pause(0.1) # Pequeña pausa para que Windows cree la ventana correctamente

    # 4. Función de actualización limpia (Matplotlib puro)
    def actualizar_iluminacion(self, pais=None):
  
        # 1. Remueve la iluminación anterior de forma segura si existe
        if self.objeto_iluminacion is not None:
            self.objeto_iluminacion.remove()
            self.objeto_iluminacion = None

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
                self.objeto_iluminacion = PolyCollection(
                    coordenadas, 
                    facecolors='#e67e22', 
                    edgecolors='white', 
                    linewidths=1.0,
                    zorder=3
                )
                
                # Agregamos la iluminación directamente encima del mapa base sin recalcular nada
                ax.add_collection(self.objeto_iluminacion)
                texto_titulo.set_text(f" {pais.upper()}")
        else:
            texto_titulo.set_text(" MAPA MUNDI INTERACTIVO NATIVO")

        # 3. Forzar el zoom original para evitar cualquier intento de reajuste
        ax.set_xlim(limites_x)
        ax.set_ylim(limites_y)

    # 5. Detectar movimiento del mouse
    def mover_mouse(self):
        # punto = Point(event.xdata, event.ydata)
        seleccionado = world[world.geometry.intersects(self.punto_actual)]

        if not seleccionado.empty:
            nombre = seleccionado.iloc[0]["name"]

            if nombre != self.pais_actual:
                self.pais_actual = nombre
                self.actualizar_iluminacion(nombre)

        else:
            if self.pais_actual is not None:
                self.pais_actual = None
                self.actualizar_iluminacion()


    def Actualizar_puntos(self, x, y):
        self.punto_actual = Point(x, y)
        self.marcador_mano.set_data([x], [y])  # Actualiza la posición del marcador de la mano
        # Aquí podrías iniciar tu bucle de Pygame o cualquier otra lógica que necesites
        # Conectar el evento de movimiento
        print("actualizando puntos: ", x, "-", y)
        self.mover_mouse()

        fig.canvas.draw_idle()
        fig.canvas.flush_events()
