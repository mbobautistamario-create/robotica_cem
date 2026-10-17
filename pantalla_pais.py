import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button
import numpy as np

class PantallaPais:
    def __init__(self, fig, nombre_pais="País Desconocido", info=None, callback_volver=None):
        self.fig = fig
        self.nombre_pais = nombre_pais
        self.callback_volver = callback_volver
        self.info = info or {}
        
        self.pestana_activa = 0
        self.botones = []
        self.botones_bbox = []  
        self.elementos_ui = [] 
        
        self.construir_interfaz()

    def construir_interfaz(self):
        self.fig.patch.set_facecolor('#1e272e')

        # ─── 1. EL GRAN TÍTULO DEL PAÍS (HEADER ESTILO WEB) ───
        self.ax_header = self.fig.add_axes([0.10, 0.88, 0.80, 0.08])
        self.ax_header.axis("off")
        
        # Renderizamos la imagen de la tabla PAIS como fondo
        img_header = self.info.get("header_img", np.full((100, 100, 3), 40, dtype=np.uint8))
        self.ax_header.imshow(img_header, aspect='auto')
        
        # Filtro oscuro semitransparente (alpha=0.5) para asegurar que el texto sea legible
        self.ax_header.add_patch(patches.Rectangle((0, 0), 1, 1, transform=self.ax_header.transAxes, color='black', alpha=0.5))

        # Texto centrado usando coordenadas relativas al recuadro (transAxes)
        titulo_principal = self.ax_header.text(
            0.5, 0.5, f" 🌍  {self.nombre_pais.upper()}  🌍 ",
            fontsize=26, weight="black", color="#ffffff",
            ha="center", va="center", transform=self.ax_header.transAxes
        )
        self.elementos_ui.append(self.ax_header)

        # ─── 2. LOS BOTONES DE NAVEGACIÓN ───
        nombres_pestanas = ["Resumen General", "Gastronomía Típica", "Guía de Turismo"]
        posiciones_x = [0.10, 0.40, 0.70]
        ancho_btn = 0.20
        alto_btn = 0.04
        
        for idx, nombre in enumerate(nombres_pestanas):
            rect = [posiciones_x[idx], 0.82, ancho_btn, alto_btn]
            ax_btn = self.fig.add_axes(rect)
            self.elementos_ui.append(ax_btn)

            color_fondo = '#0984e3' if idx == self.pestana_activa else '#2d3436'
            btn = Button(ax_btn, nombre, color=color_fondo, hovercolor='#74b9ff')
            btn.label.set_color('white')
            btn.label.set_weight('bold')
            btn.label.set_fontsize(11)
            
            btn.on_clicked(lambda event, i=idx: self.cambiar_pestana(i))
            self.botones.append(btn)
            self.botones_bbox.append({
                "tipo": "pestana", "indice": idx,
                "x_min": rect[0], "y_min": rect[1],
                "x_max": rect[0] + rect[2], "y_max": rect[1] + rect[3]
            })

        # ─── 3. PANEL DE IMAGEN DE CONTENIDO ───
        self.ax_imagen = self.fig.add_axes([0.10, 0.15, 0.40, 0.62])
        self.ax_imagen.axis("off")
        self.visor_imagen = self.ax_imagen.imshow(np.zeros((100, 100, 3), dtype=np.uint8), aspect='auto')
        self.elementos_ui.append(self.ax_imagen)

        # ─── 4. PANEL DE INFORMACIÓN ESTRUCTURADA ───
        self.ax_texto = self.fig.add_axes([0.55, 0.15, 0.35, 0.62])
        self.ax_texto.set_facecolor('#2d3436')
        self.ax_texto.axis("off")
        
        for spine in self.ax_texto.spines.values():
            spine.set_visible(True)
            spine.set_color('#0984e3')
            spine.set_linewidth(1.5)
        self.elementos_ui.append(self.ax_texto)

        self.ui_titulo = self.ax_texto.text(0.05, 0.94, "", fontsize=15, weight="bold", color="#fdcb6e", va="top")
        self.ui_subtit = self.ax_texto.text(0.05, 0.85, "", fontsize=12, style="italic", color="#74b9ff", va="top", wrap=True)
        self.ui_cuerpo = self.ax_texto.text(0.05, 0.70, "", fontsize=12, color="#dfe6e9", va="top", wrap=True, linespacing=1.7)
        
        self.elementos_ui.extend([self.ui_titulo, self.ui_subtit, self.ui_cuerpo])

        # ─── 5. BOTÓN VOLVER ───
        rect_volver = [0.40, 0.06, 0.20, 0.045]
        ax_volver = self.fig.add_axes(rect_volver)
        self.elementos_ui.append(ax_volver)

        self.btn_volver = Button(ax_volver, "← VOLVER AL MAPA", color='#d63031', hovercolor='#ff7675')
        self.btn_volver.label.set_color('white')
        self.btn_volver.label.set_weight('bold')
        self.btn_volver.on_clicked(self.volver_al_mapa)
        
        self.botones_bbox.append({
            "tipo": "volver", "indice": -1,
            "x_min": rect_volver[0], "y_min": rect_volver[1],
            "x_max": rect_volver[0] + rect_volver[2], "y_max": rect_volver[1] + rect_volver[3]
        })

        # Cursor Gestual
        self.ax_cursor = self.fig.add_axes([0, 0, 1, 1], zorder=10)
        self.ax_cursor.axis("off")
        self.ax_cursor.set_xlim(0, 1)
        self.ax_cursor.set_ylim(0, 1)
        self.marcador_mano, = self.ax_cursor.plot([], [], 'o', color='#00ffcc', ms=14, markeredgecolor='white', markeredgewidth=2)
        self.elementos_ui.append(self.ax_cursor)

        self.pos_mano_norm = (0.5, 0.5)
        self.mostrar_contenido()

    def mostrar_contenido(self):
        for idx, btn in enumerate(self.botones):
            color = '#0984e3' if idx == self.pestana_activa else '#2d3436'
            btn.ax.set_facecolor(color)

        if self.pestana_activa == 0:
            datos_tab = self.info.get("general", {})
        elif self.pestana_activa == 1:
            datos_tab = self.info.get("cultura", {})
        else:
            datos_tab = self.info.get("datos", {})

        self.ui_titulo.set_text(datos_tab.get("titulo", "Sin Título"))
        self.ui_subtit.set_text(datos_tab.get("subtitulo", "Subtítulo no encontrado"))
        self.ui_cuerpo.set_text(datos_tab.get("cuerpo", "Descripción no disponible en la base de datos."))
        
        img_array = datos_tab.get("imagen", np.full((300, 400, 3), 80, dtype=np.uint8))
        self.visor_imagen.set_data(img_array)
        self.visor_imagen.set_extent((0, img_array.shape[1], img_array.shape[0], 0))

        try:
            self.fig.canvas.draw_idle()
        except Exception:
            pass

    def cambiar_pestana(self, indice):
        self.pestana_activa = indice
        self.mostrar_contenido()

    def destruir_interfaz(self):
        for elemento in self.elementos_ui:
            elemento.remove()
        self.elementos_ui.clear()
        self.botones.clear()

    def volver_al_mapa(self, event=None):
        self.destruir_interfaz()
        if self.callback_volver:
            self.callback_volver()

    def actualizar_cursor(self, norm_x, norm_y):
        y_fig = 1.0 - norm_y
        self.pos_mano_norm = (norm_x, y_fig)
        self.marcador_mano.set_data([norm_x], [y_fig])
        try:
            self.fig.canvas.draw_idle()
        except Exception:
            pass

    def ejecutar_click_gesto(self):
        x, y = self.pos_mano_norm
        for btn_info in self.botones_bbox:
            if btn_info["x_min"] <= x <= btn_info["x_max"] and btn_info["y_min"] <= y <= btn_info["y_max"]:
                if btn_info["tipo"] == "pestana":
                    self.cambiar_pestana(btn_info["indice"])
                elif btn_info["tipo"] == "volver":
                    self.volver_al_mapa()
                break