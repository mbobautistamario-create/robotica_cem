import matplotlib.pyplot as plt
from matplotlib.widgets import Button

class PantallaPais:
    def __init__(self, fig, nombre_pais="País Desconocido", info=None, callback_volver=None):
        self.fig = fig
        self.nombre_pais = nombre_pais
        self.callback_volver = callback_volver
        
        self.info = info or {
            "general": f"Información general sobre {nombre_pais}.\n\nAquí puedes colocar datos históricos o un resumen introductorio.",
            "cultura": "• Idioma oficial: -\n• Capital: -\n• Moneda: -\n• Costumbres destacadas.",
            "datos": "• Población estimada: -\n• Superficie total: -\n• Continente: -\n• Datos económicos relevantes."
        }
        
        self.pestana_activa = 0
        self.botones = []
        self.botones_bbox = []  
        self.elementos_ui = [] # Rastrea todos los ejes creados para eliminarlos al volver
        
        self.construir_interfaz()

    def construir_interfaz(self):
        # Título principal
        titulo = self.fig.text(
            0.5, 0.93, f"PAÍS: {self.nombre_pais.upper()}",
            fontsize=20, weight="bold", color="#f5f6fa",
            ha="center", va="center"
        )
        self.elementos_ui.append(titulo)

        nombres_pestanas = ["General", "Geografía & Cultura", "Datos & Economía"]
        posiciones_x = [0.15, 0.40, 0.65]
        ancho_btn = 0.20
        alto_btn = 0.045
        
        for idx, nombre in enumerate(nombres_pestanas):
            rect = [posiciones_x[idx], 0.83, ancho_btn, alto_btn]
            ax_btn = self.fig.add_axes(rect)
            self.elementos_ui.append(ax_btn)

            color_fondo = '#e67e22' if idx == self.pestana_activa else '#34495e'
            btn = Button(ax_btn, nombre, color=color_fondo, hovercolor='#d35400')
            btn.label.set_color('white')
            btn.label.set_weight('bold')
            btn.label.set_fontsize(10)
            
            btn.on_clicked(lambda event, i=idx: self.cambiar_pestana(i))
            self.botones.append(btn)
            self.botones_bbox.append({
                "tipo": "pestana", "indice": idx,
                "x_min": rect[0], "y_min": rect[1],
                "x_max": rect[0] + rect[2], "y_max": rect[1] + rect[3]
            })

        # Botón volver
        rect_volver = [0.40, 0.08, 0.20, 0.045]
        ax_volver = self.fig.add_axes(rect_volver)
        self.elementos_ui.append(ax_volver)

        self.btn_volver = Button(ax_volver, "← Volver al Mapa", color='#c0392b', hovercolor='#e74c3c')
        self.btn_volver.label.set_color('white')
        self.btn_volver.label.set_weight('bold')
        self.btn_volver.on_clicked(self.volver_al_mapa)
        
        self.botones_bbox.append({
            "tipo": "volver", "indice": -1,
            "x_min": rect_volver[0], "y_min": rect_volver[1],
            "x_max": rect_volver[0] + rect_volver[2], "y_max": rect_volver[1] + rect_volver[3]
        })

        # Área de contenido
        self.ax_contenido = self.fig.add_axes([0.15, 0.18, 0.70, 0.60])
        self.ax_contenido.set_facecolor('#2f3640')
        self.ax_contenido.axis("off")
        self.elementos_ui.append(self.ax_contenido)

        self.texto_cuerpo = self.ax_contenido.text(
            0.05, 0.90, "",
            fontsize=13, color="#dcdde1",
            va="top", ha="left", wrap=True
        )

        # Cursor de la mano transparente
        self.ax_cursor = self.fig.add_axes([0, 0, 1, 1], zorder=10)
        self.ax_cursor.axis("off")
        self.ax_cursor.set_xlim(0, 1)
        self.ax_cursor.set_ylim(0, 1)
        self.marcador_mano, = self.ax_cursor.plot([], [], 'o', color='#00ffcc', ms=12, markeredgecolor='white', markeredgewidth=1.5)
        self.elementos_ui.append(self.ax_cursor)

        self.pos_mano_norm = (0.5, 0.5)
        self.mostrar_contenido()

    def mostrar_contenido(self):
        for idx, btn in enumerate(self.botones):
            color = '#e67e22' if idx == self.pestana_activa else '#34495e'
            btn.ax.set_facecolor(color)

        if self.pestana_activa == 0:
            texto = self.info.get("general", "")
        elif self.pestana_activa == 1:
            texto = self.info.get("cultura", "")
        else:
            texto = self.info.get("datos", "")

        self.texto_cuerpo.set_text(texto)
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