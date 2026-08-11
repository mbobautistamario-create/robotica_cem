import geopandas as gpd
import matplotlib
matplotlib.use("TkAgg")  # Fuerza el backend seguro para hilos
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

# 3. Dibujar el mapa base
world.plot(
    ax=ax,
    color="#2c3e50",       # Color de los países
    edgecolor="#34495e",   # Color de las fronteras
    linewidth=0.6
)

# Configuración inicial del mapa
ax.axis("off")
ax.set_autoscale_on(False)

# Texto indicador en miniatura
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
        self.pais_actual = None
        self.objeto_iluminacion = None 

        # Marcador visual de la mano
        self.marcador_mano, = ax.plot([], [], 'ro', ms=10, zorder=5, label="Tu Mano")

        plt.show(block=False)
        plt.pause(0.1)

    def actualizar_iluminacion(self, pais=None):
        if self.objeto_iluminacion is not None:
            self.objeto_iluminacion.remove()
            self.objeto_iluminacion = None

        if pais is not None:
            seleccionado = world[world["name"] == pais]
            
            if not seleccionado.empty:
                geometria = seleccionado.geometry.iloc[0]
                coordenadas = []
                
                if geometria.geom_type == 'Polygon':
                    coordenadas.append(list(geometria.exterior.coords))
                elif geometria.geom_type == 'MultiPolygon':
                    for poligono in geometria.geoms:
                        coordenadas.append(list(poligono.exterior.coords))
                
                self.objeto_iluminacion = PolyCollection(
                    coordenadas, 
                    facecolors='#e67e22', 
                    edgecolors='white', 
                    linewidths=1.0,
                    zorder=3
                )
                
                ax.add_collection(self.objeto_iluminacion)
                texto_titulo.set_text(f" {pais.upper()}")
        else:
            texto_titulo.set_text(" MAPA MUNDI INTERACTIVO NATIVO")

    def aplicar_zoom(self, factor):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        cx = self.punto_actual.x
        cy = self.punto_actual.y

        if cx == 0 and cy == 0:
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2

        ancho_nuevo = (xmax - xmin) * factor
        alto_nuevo = (ymax - ymin) * factor

        if 2.0 < ancho_nuevo < 360.0:
            ax.set_xlim(cx - ancho_nuevo / 2, cx + ancho_nuevo / 2)
            ax.set_ylim(cy - alto_nuevo / 2, cy + alto_nuevo / 2)

            try:
                fig.canvas.draw() # Forzar dibujado inmediato
            except Exception:
                pass

    def desplazar_punto(self, dx_pixeles, dy_pixeles, ancho_pantalla, alto_pantalla):
        """
        Mueve el punto Y desplaza la cámara (Pan) proporcionalmente al zoom actual.
        """
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ancho_vista = xmax - xmin
        alto_vista = ymax - ymin

        delta_x = (dx_pixeles / ancho_pantalla) * ancho_vista * 0.5
        delta_y = -(dy_pixeles / alto_pantalla) * alto_vista * 0.5 # Invertido para eje Y

        nuevo_x = self.punto_actual.x + delta_x
        nuevo_y = self.punto_actual.y + delta_y

        # Si el mapa tiene zoom aplicado, desplazamos los límites de la cámara también
        if ancho_vista < 350.0:
            ax.set_xlim(xmin + delta_x, xmax + delta_x)
            ax.set_ylim(ymin + delta_y, ymax + delta_y)

        self.Actualizar_puntos(nuevo_x, nuevo_y)

    def mover_mouse(self):
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
        self.marcador_mano.set_data([x], [y])
        self.mover_mouse()

        # Forzar la actualización visual inmediata del lienzo sin depender del estado idle
        try:
            fig.canvas.draw()
        except Exception:
            pass