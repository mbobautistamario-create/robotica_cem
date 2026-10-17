import time  # <--- NUEVO IMPORT
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
        
        # ─── VARIABLES PARA EL CLIC POR TIEMPO (DWELL CLICK) ───
        self.boton_hover_actual = None
        self.tiempo_inicio_hover = 0
        
        self.construir_interfaz()

    def construir_interfaz(self):
        self.fig.patch.set_facecolor('#1e272e')

        # Barra lateral
        self.ax_sidebar_bg = self.fig.add_axes([0.03, 0.05, 0.22, 0.90])
        self.ax_sidebar_bg.set_facecolor('#2d3436')
        self.ax_sidebar_bg.axis("off")
        self.elementos_ui.append(self.ax_sidebar_bg)

        # Recuadro Título Superior
        self.ax_title_img = self.fig.add_axes([0.03, 0.65, 0.22, 0.30])
        self.ax_title_img.axis("off")
        
        img_header = self.info.get("header_img", np.full((100, 100, 3), 40, dtype=np.uint8))
        self.ax_title_img.imshow(img_header, aspect='auto') 
        self.ax_title_img.add_patch(patches.Rectangle((0, 0), 1, 1, transform=self.ax_title_img.transAxes, color='black', alpha=0.55))

        nombre_vertical = self.nombre_pais.upper().replace(" ", "\n")
        titulo_principal = self.ax_title_img.text(
            0.5, 0.5, nombre_vertical,
            fontsize=26, weight="black", color="#ffffff",
            ha="center", va="center", transform=self.ax_title_img.transAxes
        )
        self.elementos_ui.extend([self.ax_title_img, titulo_principal])

        # Botón Volver
        rect_volver = [0.04, 0.08, 0.20, 0.05]
        ax_volver = self.fig.add_axes(rect_volver)
        self.elementos_ui.append(ax_volver)
        self.btn_volver = Button(ax_volver, "← SALIR", color='#d63031', hovercolor='#ff7675')
        self.btn_volver.label.set_color('white')
        self.btn_volver.label.set_weight('bold')
        self.btn_volver.on_clicked(self.volver_al_mapa)
        self.botones_bbox.append({"tipo": "volver", "indice": -1, "x_min": rect_volver[0], "y_min": rect_volver[1], "x_max": rect_volver[0] + rect_volver[2], "y_max": rect_volver[1] + rect_volver[3]})

        # Área derecha
        self.ax_fondo_der = self.fig.add_axes([0.27, 0.05, 0.70, 0.90])
        self.ax_fondo_der.set_facecolor('#222f3e')
        self.ax_fondo_der.axis("off")
        for spine in self.ax_fondo_der.spines.values():
            spine.set_visible(True)
            spine.set_color('#0984e3')
            spine.set_linewidth(1.5)
        self.elementos_ui.append(self.ax_fondo_der)

        # Pestañas
        nombres_pestanas = ["Resumen General", "Gastronomía Típica", "Guía de Turismo"]
        posiciones_x = [0.29, 0.51, 0.73]
        for idx, nombre in enumerate(nombres_pestanas):
            rect = [posiciones_x[idx], 0.86, 0.21, 0.05]
            ax_btn = self.fig.add_axes(rect)
            self.elementos_ui.append(ax_btn)
            color_fondo = '#0984e3' if idx == self.pestana_activa else '#576574'
            btn = Button(ax_btn, nombre, color=color_fondo, hovercolor='#48dbfb')
            btn.label.set_color('white')
            btn.label.set_weight('bold')
            btn.label.set_fontsize(12)
            btn.on_clicked(lambda event, i=idx: self.cambiar_pestana(i))
            self.botones.append(btn)
            self.botones_bbox.append({"tipo": "pestana", "indice": idx, "x_min": rect[0], "y_min": rect[1], "x_max": rect[0] + rect[2], "y_max": rect[1] + rect[3]})

        # Panel Imagen 
        self.ax_imagen = self.fig.add_axes([0.29, 0.20, 0.33, 0.55])
        self.ax_imagen.axis("off")
        self.elementos_ui.append(self.ax_imagen)

        # Panel Texto
        self.ax_texto = self.fig.add_axes([0.64, 0.20, 0.31, 0.55])
        self.ax_texto.axis("off")
        self.elementos_ui.append(self.ax_texto)
        self.ui_titulo = self.ax_texto.text(0.0, 1.0, "", fontsize=18, weight="bold", color="#feca57", va="top")
        self.ui_subtit = self.ax_texto.text(0.0, 0.88, "", fontsize=13, style="italic", color="#48dbfb", va="top", wrap=True)
        self.ui_cuerpo = self.ax_texto.text(0.0, 0.72, "", fontsize=13, color="#c8d6e5", va="top", wrap=True, linespacing=1.8)
        self.elementos_ui.extend([self.ui_titulo, self.ui_subtit, self.ui_cuerpo])

        # Cursor Gestual
        self.ax_cursor = self.fig.add_axes([0, 0, 1, 1], zorder=10)
        self.ax_cursor.axis("off")
        self.ax_cursor.set_xlim(0, 1)
        self.ax_cursor.set_ylim(0, 1)
        self.marcador_mano, = self.ax_cursor.plot([], [], 'o', color='#00d2d3', ms=14, markeredgecolor='white', markeredgewidth=2)
        self.elementos_ui.append(self.ax_cursor)
        self.pos_mano_norm = (0.5, 0.5)

        self.mostrar_contenido()

    def mostrar_contenido(self):
        for idx, btn in enumerate(self.botones):
            color = '#0984e3' if idx == self.pestana_activa else '#576574'
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
        
        img_array = datos_tab.get("imagen", np.full((300, 400, 3), 40, dtype=np.uint8))
        self.ax_imagen.clear()
        self.ax_imagen.axis("off")
        self.ax_imagen.imshow(img_array)

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

        # ─── LÓGICA DE DWELL CLICK (CLIC POR TIEMPO) ───
        boton_detectado = None
        for btn_info in self.botones_bbox:
            # Comprobamos si el puntero está dentro de los límites de algún botón
            if btn_info["x_min"] <= norm_x <= btn_info["x_max"] and btn_info["y_min"] <= y_fig <= btn_info["y_max"]:
                boton_detectado = btn_info
                break

        if boton_detectado:
            # Feedback visual: Cursor amarillo y más grande
            self.marcador_mano.set_color('#feca57')
            self.marcador_mano.set_markersize(18)
            
            # Si acabamos de entrar a un botón nuevo, iniciamos el cronómetro
            if self.boton_hover_actual != boton_detectado:
                self.boton_hover_actual = boton_detectado
                self.tiempo_inicio_hover = time.time()
            else:
                # Si seguimos en el mismo botón, verificamos el tiempo
                tiempo_transcurrido = time.time() - self.tiempo_inicio_hover
                if tiempo_transcurrido >= 1.5:  # 1.5 segundos
                    self.ejecutar_click_gesto()
                    
                    # Reseteamos para no hacer clics infinitos consecutivos
                    self.boton_hover_actual = None
                    self.tiempo_inicio_hover = 0
        else:
            # Feedback visual: Cursor vuelve a la normalidad al salir del botón
            self.marcador_mano.set_color('#00d2d3')
            self.marcador_mano.set_markersize(14)
            self.boton_hover_actual = None
            self.tiempo_inicio_hover = 0

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