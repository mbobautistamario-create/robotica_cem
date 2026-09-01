import geopandas as gpd
import matplotlib
matplotlib.use("TkAgg")  # Fuerza el backend seguro para hilos
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.collections import PolyCollection
from pantalla_pais import PantallaPais  # Importar la nueva pantalla

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
        self.pantalla_info_activa = False

        self.dibujar_mapa_base()

        plt.show(block=False)
        try:
            fig.canvas.manager.window.state('zoomed')
        except Exception:
            pass
        plt.pause(0.1)

    def dibujar_mapa_base(self):
        global ax, texto_titulo
        fig.clf()
        fig.patch.set_facecolor('#f8f9fa')

        ax = fig.add_subplot(111)
        ax.set_facecolor('#ecf0f1')

        world.plot(
            ax=ax,
            color="#2c3e50",
            edgecolor="#34495e",
            linewidth=0.6
        )

        ax.axis("off")
        ax.set_autoscale_on(False)

        texto_titulo = ax.text(
            0.5, 0.98, "MAPA MUNDI INTERACTIVO NATIVO",
            transform=ax.transAxes,
            fontsize=11, color="#2c3e50", weight="bold",
            ha="center", va="center"
        )

        self.marcador_mano, = ax.plot([self.punto_actual.x], [self.punto_actual.y], 'ro', ms=10, zorder=5)
        self.objeto_iluminacion = None
        self.pantalla_info_activa = False

        try:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        except Exception:
            pass

    def abrir_pantalla_pais(self, nombre_pais=None, info=None):
        pais = nombre_pais or self.pais_actual or "Selección actual"
        self.pantalla_info_activa = True
        
        # Inicializa la pantalla de solapas reutilizando la figura existente
        self.pantalla_pais = PantallaPais(
            fig=fig,
            nombre_pais=pais,
            info=info,
            callback_volver=self.dibujar_mapa_base
        )

    def Actualizar_puntos(self, x, y):
        # Si la pantalla de información está abierta, no procesamos la posición del mapa
        if self.pantalla_info_activa:
            return

        self.punto_actual = Point(x, y)
        self.marcador_mano.set_data([x], [y])
        self.mover_mouse()

        try:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        except Exception:
            pass

    def Actualizar_cursor_info(self, norm_x, norm_y):
        if self.pantalla_info_activa and hasattr(self, 'pantalla_pais'):
            self.pantalla_pais.actualizar_cursor(norm_x, norm_y)

    def Ejecutar_click_info(self):
        if self.pantalla_info_activa and hasattr(self, 'pantalla_pais'):
            self.pantalla_pais.ejecutar_click_gesto()

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
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
            except Exception:
                pass

    def desplazar_punto(self, dx_pixeles, dy_pixeles, ancho_pantalla, alto_pantalla):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ancho_vista = xmax - xmin
        alto_vista = ymax - ymin

        # ─── NUEVO: Sensibilidad dinámica según el nivel de Zoom ───
        # Si vemos el planeta entero (360°), la velocidad es 0.5. 
        # A medida que hacemos zoom, baja progresivamente hasta un tope de 0.1 para dar precisión.
        sensibilidad = max(0.05, 0.5 * (ancho_vista / 360.0))

        delta_x = (dx_pixeles / ancho_pantalla) * ancho_vista * sensibilidad
        delta_y = -(dy_pixeles / alto_pantalla) * alto_vista * sensibilidad

        nuevo_x = self.punto_actual.x + delta_x
        nuevo_y = self.punto_actual.y + delta_y

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

        try:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        except Exception:
            pass