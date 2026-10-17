import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

class PantallaPais:
    def __init__(self, fig, nombre_pais="País Desconocido", info=None, callback_volver=None):
        self.fig = fig
        self.nombre_pais = nombre_pais
        self.callback_volver = callback_volver
        
        # Estructura por defecto si falla la carga
        self.info = info or {
            "general": {"texto": "Cargando...", "imagen": np.zeros((10,10,3), dtype=np.uint8)},
            "cultura": {"texto": "Cargando...", "imagen": np.zeros((10,10,3), dtype=np.uint8)},
            "datos": {"texto": "Cargando...", "imagen": np.zeros((10,10,3), dtype=np.uint8)}
        }
        
        self.pestana_activa = 0
        self.botones = []
        self.botones_bbox = []  
        self.elementos_ui = [] 
        
        self.construir_interfaz()

    def construir_interfaz(self):
        self.fig.patch.set_facecolor('#1e272e')

        self.ax_header = self.fig.add_axes([0.15, 0.88, 0.70, 0.08])
        self.ax_header.set_facecolor('#2f3640')
        self.ax_header.axis("off")
        self.elementos_ui.append(self.ax_header)

        titulo = self.ax_header.text(
            0.5, 0.5, f"INFORMACIÓN DETALLADA: {self.nombre_pais.upper()}",
            fontsize=18, weight="heavy", color="#f1c40f",
            ha="center", va="center"
        )
        self.elementos_ui.append(titulo)

        nombres_pestanas = ["General e Historia", "Gastronomía Típica", "Puntos de Turismo"]
        posiciones_x = [0.15, 0.40, 0.65]
        ancho_btn = 0.20
        alto_btn = 0.045
        
        for idx, nombre in enumerate(nombres_pestanas):
            rect = [posiciones_x[idx], 0.80, ancho_btn, alto_btn]
            ax_btn = self.fig.add_axes(rect)
            self.elementos_ui.append(ax_btn)

            color_fondo = '#00a8ff' if idx == self.pestana_activa else '#353b48'
            btn = Button(ax_btn, nombre, color=color_fondo, hovercolor='#0097e6')
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

        # --- SECCIÓN DE CONTENIDO DIVIDIDA (IMAGEN IZQ / TEXTO DER) ---
        
        # Eje para la Imagen
        self.ax_imagen = self.fig.add_axes([0.15, 0.20, 0.33, 0.55])
        self.ax_imagen.axis("off")
        self.visor_imagen = self.ax_imagen.imshow(np.zeros((100, 100, 3), dtype=np.uint8))
        self.elementos_ui.append(self.ax_imagen)

        # Eje para el Texto
        self.ax_texto = self.fig.add_axes([0.50, 0.20, 0.35, 0.55])
        self.ax_texto.set_facecolor('#2f3640')
        self.ax_texto.axis("off")
        self.texto_cuerpo = self.ax_texto.text(
            0.05, 0.95, "",
            fontsize=13, color="#f5f6fa",
            va="top", ha="left", wrap=True, linespacing=1.6
        )
        self.elementos_ui.append(self.ax_texto)

        # -------------------------------------------------------------

        rect_volver = [0.40, 0.08, 0.20, 0.05]
        ax_volver = self.fig.add_axes(rect_volver)
        self.elementos_ui.append(ax_volver)

        self.btn_volver = Button(ax_volver, "← RETORNAR AL MAPAMUNDI", color='#e84118', hovercolor='#c23616')
        self.btn_volver.label.set_color('white')
        self.btn_volver.label.set_weight('bold')
        self.btn_volver.on_clicked(self.volver_al_mapa)
        
        self.botones_bbox.append({
            "tipo": "volver", "indice": -1,
            "x_min": rect_volver[0], "y_min": rect_volver[1],
            "x_max": rect_volver[0] + rect_volver[2], "y_max": rect_volver[1] + rect_volver[3]
        })

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
            color = '#00a8ff' if idx == self.pestana_activa else '#353b48'
            btn.ax.set_facecolor(color)

        if self.pestana_activa == 0:
            datos_tab = self.info.get("general", {})
        elif self.pestana_activa == 1:
            datos_tab = self.info.get("cultura", {})
        else:
            datos_tab = self.info.get("datos", {})

        # Actualizamos el texto
        self.texto_cuerpo.set_text(datos_tab.get("texto", ""))
        
        # Actualizamos la imagen y reescalamos los bordes
        img_array = datos_tab.get("imagen", np.zeros((10,10,3), dtype=np.uint8))
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