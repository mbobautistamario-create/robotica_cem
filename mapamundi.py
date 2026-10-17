import geopandas as gpd
import matplotlib
matplotlib.use("TkAgg")  
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.collections import PolyCollection
from matplotlib.gridspec import GridSpec
from pantalla_pais import PantallaPais  
from gestor_datos import GestorDatosPais

plt.ion()

# 1. Cargar el GeoJSON
world = gpd.read_file("custom.geo.json")

class Mapa():
    def __init__(self):
        self.punto_actual = Point(0, 0)
        self.pais_actual = None
        self.objeto_iluminacion = None 
        self.pantalla_info_activa = False

        # Instanciamos el conector a la "Base de Datos"
        self.gestor_db = GestorDatosPais()

        self.fig = plt.figure(figsize=(16, 8))
        self.fig.patch.set_facecolor('#1e272e')

        self.fig = plt.figure(figsize=(16, 8))
        self.fig.patch.set_facecolor('#1e272e')

        # 2. GridSpec Matemático para el Cuadrado Perfecto
        # Al tener una figura de 16:8 (2:1), si le damos a la fila superior una altura del doble (2)
        # respecto a la inferior (1), y columnas divididas en 3, la celda [0,0] será un cuadrado exacto.
        self.gs = GridSpec(2, 3, figure=self.fig, height_ratios=[2, 1])
        self.ax_cam = self.fig.add_subplot(self.gs[0, 0])      
        self.ax_gestos = self.fig.add_subplot(self.gs[1, 0])   
        self.ax_mapa = self.fig.add_subplot(self.gs[:, 1:])    

        self.img_camara = None

        self.dibujar_mapa_base()
        self.configurar_panel_izquierdo()

        plt.show(block=False)
        try:
            self.fig.canvas.manager.window.state('zoomed') 
        except Exception:
            pass
        plt.pause(0.1)

    def configurar_panel_izquierdo(self):
        self.ax_cam.axis("off")
        self.ax_cam.set_title("CÁMARA EN VIVO", color="#f1c40f", weight="bold")

        self.ax_gestos.axis("off")
        self.texto_leyenda = self.ax_gestos.text(
            0.05, 0.95, 
            "LEYENDA DE GESTOS\n\n"
            "✋ Mano Abierta:\n   Puntero Libre (Ver Países)\n\n"
            "✊ Mano Cerrada (2s):\n   Entrar al País\n\n"
            "🤏 Pellizco (Pulgar+Índice):\n   Arrastrar Mapa\n\n"
            "👌 Pulgar + Medio:\n   Zoom In (+)\n\n"
            "🤞 Pulgar + Anular:\n   Zoom Out (-)", 
            color="#dcdde1", fontsize=11, va="top", ha="left"
        )

    def dibujar_mapa_base(self):
        self.ax_mapa.set_facecolor('#ecf0f1')
        world.plot(ax=self.ax_mapa, color="#2c3e50", edgecolor="#34495e", linewidth=0.6)

        self.ax_mapa.axis("off")
        self.ax_mapa.set_autoscale_on(False)

        self.texto_titulo = self.ax_mapa.text(
            0.5, 0.98, "MAPA MUNDI INTERACTIVO NATIVO",
            transform=self.ax_mapa.transAxes,
            fontsize=12, color="#aa41ff", weight="bold", ha="center", va="center"
        )

        # Ubicar el punto fijo exactamente en el centro de la vista
        xmin, xmax = self.ax_mapa.get_xlim()
        ymin, ymax = self.ax_mapa.get_ylim()
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        
        self.punto_actual = Point(cx, cy)
        self.marcador_mano, = self.ax_mapa.plot([cx], [cy], 'ro', ms=12, zorder=5)

    def actualizar_camara(self, frame_rgb):
        if self.img_camara is None:
            self.img_camara = self.ax_cam.imshow(frame_rgb)
        else:
            self.img_camara.set_data(frame_rgb)
            self.img_camara.set_extent((0, frame_rgb.shape[1], frame_rgb.shape[0], 0))

    def abrir_pantalla_pais(self, nombre_pais=None, info=None):
        pais_geojson = nombre_pais or self.pais_actual
        if not pais_geojson: return # Proteccion por si se hace click en el océano
        
        self.pantalla_info_activa = True
        
        self.ax_mapa.set_visible(False)
        self.ax_cam.set_visible(False)
        self.ax_gestos.set_visible(False)

        # ─── APLICAMOS LA TRADUCCIÓN AQUÍ ───
        # Traducimos el país para que se vea en español en el título de la pantalla UI
        pais_espanol = self.gestor_db.traducir_nombre(pais_geojson)

        if info is None:
            # Mandamos a buscar el país a la base de datos
            info_bd = self.gestor_db.obtener_info_pais(pais_geojson)
        else:
            info_bd = info

        self.pantalla_pais = PantallaPais(
            fig=self.fig, 
            nombre_pais=pais_espanol,  # Le pasamos el español a la interfaz visual
            info=info_bd, 
            callback_volver=self.restaurar_mapa
        )

    def restaurar_mapa(self):
        self.pantalla_info_activa = False
        self.ax_mapa.set_visible(True)
        self.ax_cam.set_visible(True)
        self.ax_gestos.set_visible(True)
        
        if hasattr(self, 'pantalla_pais'):
            self.pantalla_pais.destruir_interfaz()
            del self.pantalla_pais
        
        try:
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
        except Exception:
            pass

    def desplazar_mapa(self, dx_norm, dy_norm):
        """Mueve los límites del mapa para dar el efecto de arrastre. El punto central es estático."""
        xmin, xmax = self.ax_mapa.get_xlim()
        ymin, ymax = self.ax_mapa.get_ylim()

        ancho_vista = xmax - xmin
        alto_vista = ymax - ymin

        # El límite se mueve en la dirección opuesta al arrastre
        delta_x = -dx_norm * ancho_vista
        delta_y = dy_norm * alto_vista

        nuevo_xmin = xmin + delta_x
        nuevo_xmax = xmax + delta_x
        nuevo_ymin = ymin + delta_y
        nuevo_ymax = ymax + delta_y

        self.ax_mapa.set_xlim(nuevo_xmin, nuevo_xmax)
        self.ax_mapa.set_ylim(nuevo_ymin, nuevo_ymax)
        
        # El punto rojo se queda fijo visualmente, pero sus coordenadas geográficas cambian
        cx = (nuevo_xmin + nuevo_xmax) / 2
        cy = (nuevo_ymin + nuevo_ymax) / 2
        self.punto_actual = Point(cx, cy)
        self.marcador_mano.set_data([cx], [cy])
        
        self.mover_mouse()

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
                    coordenadas, facecolors='#e67e22', edgecolors='white', linewidths=1.0, zorder=3
                )
                self.ax_mapa.add_collection(self.objeto_iluminacion)
                self.texto_titulo.set_text(f" {pais.upper()}")
        else:
            self.texto_titulo.set_text(" MAPA MUNDI INTERACTIVO NATIVO")

    def aplicar_zoom(self, factor):
        xmin, xmax = self.ax_mapa.get_xlim()
        ymin, ymax = self.ax_mapa.get_ylim()
        
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2

        ancho_nuevo = (xmax - xmin) * factor
        alto_nuevo = (ymax - ymin) * factor

        if 2.0 < ancho_nuevo < 360.0:
            self.ax_mapa.set_xlim(cx - ancho_nuevo / 2, cx + ancho_nuevo / 2)
            self.ax_mapa.set_ylim(cy - alto_nuevo / 2, cy + alto_nuevo / 2)
            self.mover_mouse()

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

    def Actualizar_cursor_info(self, norm_x, norm_y):
        if self.pantalla_info_activa and hasattr(self, 'pantalla_pais'):
            self.pantalla_pais.actualizar_cursor(norm_x, norm_y)

    def Ejecutar_click_info(self):
        if self.pantalla_info_activa and hasattr(self, 'pantalla_pais'):
            self.pantalla_pais.ejecutar_click_gesto()