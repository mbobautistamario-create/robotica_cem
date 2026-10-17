import cv2, time
import asyncio
import matplotlib.pyplot as plt
from mapamundi import Mapa

try:
    import mediapipe as mp
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_drawing
except ImportError as e:
    print(f"❌ Error de importación: {e}")

class EstadoPunto:
    def __init__(self):
        self.mapa = Mapa()

def Mano_cerrada(results):
    if results.multi_hand_landmarks[0].landmark[8].y > results.multi_hand_landmarks[0].landmark[5].y and \
        results.multi_hand_landmarks[0].landmark[12].y > results.multi_hand_landmarks[0].landmark[9].y and \
        results.multi_hand_landmarks[0].landmark[16].y > results.multi_hand_landmarks[0].landmark[13].y and \
        results.multi_hand_landmarks[0].landmark[20].y > results.multi_hand_landmarks[0].landmark[17].y:
        return True
    return False

def detectar_gesto(resultados):
    punta_indice = resultados.multi_hand_landmarks[0].landmark[8]
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_medio = resultados.multi_hand_landmarks[0].landmark[12]
    distancia_x = abs(punta_indice.x - punta_pulgar.x)
    distancia_y = abs(punta_indice.y - punta_pulgar.y)
    return distancia_x < 0.05 and distancia_y < 0.05 and punta_medio.y < punta_indice.y

def detectar_zoom_in(resultados):
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_medio = resultados.multi_hand_landmarks[0].landmark[12]
    distancia = ((punta_pulgar.x - punta_medio.x)**2 + (punta_pulgar.y - punta_medio.y)**2)**0.5
    return distancia < 0.05

def detectar_zoom_out(resultados):
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_anular = resultados.multi_hand_landmarks[0].landmark[16]
    distancia = ((punta_pulgar.x - punta_anular.x)**2 + (punta_pulgar.y - punta_anular.y)**2)**0.5
    return distancia < 0.05

def Posicion_mano(results):
    mano = results.multi_hand_landmarks[0]
    eje_y = (mano.landmark[1].y + mano.landmark[5].y + mano.landmark[9].y + mano.landmark[13].y + mano.landmark[17].y) / 5
    eje_x = (mano.landmark[1].x + mano.landmark[5].x + mano.landmark[9].x + mano.landmark[13].x + mano.landmark[17].x) / 5
    return (eje_x, eje_y)

def Entrar_Pais(estado_punto):
    estado_punto.mapa.abrir_pantalla_pais()

async def Ver_gestos(estado_punto):  
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)
    mano_cerrada = False
    mano_agarre = False
    posicion_inicial_norm = None

    while cap.isOpened() and plt.fignum_exists(estado_punto.mapa.fig.number):
        success, image = cap.read()
        if not success: break

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resultados = hands.process(image_rgb)

        if resultados.multi_hand_landmarks:
            for hand_landmarks in resultados.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image_rgb, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            norm_x, norm_y = Posicion_mano(resultados)

            if estado_punto.mapa.pantalla_info_activa:
                # Actualiza la posición y la pantalla se encarga de hacer clic por tiempo
                estado_punto.mapa.Actualizar_cursor_info(norm_x, norm_y)
                
                # Desactivamos el cierre de mano accidental mientras lee
                mano_cerrada = False
            else:
                if Mano_cerrada(resultados):
                    mano_agarre = False
                    posicion_inicial_norm = None
                    cv2.putText(image_rgb, "Estado: Cerrada (Entrar)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    if not mano_cerrada:
                        mano_cerrada = True
                        bandera_cerrada = time.time()
                    else:
                        if time.time() - bandera_cerrada > 2:
                            bandera_cerrada = time.time()
                            mano_cerrada = False
                            Entrar_Pais(estado_punto)
                    
                elif detectar_gesto(resultados):
                    cv2.putText(image_rgb, "Estado: Arrastrando Mapa", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2)
                    mano_cerrada = False

                    if not mano_agarre:
                        mano_agarre = True
                        posicion_inicial_norm = (norm_x, norm_y)
                    else:
                        dx_norm = norm_x - posicion_inicial_norm[0]
                        dy_norm = norm_y - posicion_inicial_norm[1]
                        
                        estado_punto.mapa.desplazar_mapa(dx_norm, dy_norm)
                        posicion_inicial_norm = (norm_x, norm_y)

                elif detectar_zoom_in(resultados):
                    cv2.putText(image_rgb, "Estado: Zoom IN (+)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    mano_cerrada = False
                    mano_agarre = False
                    estado_punto.mapa.aplicar_zoom(0.96)

                elif detectar_zoom_out(resultados):
                    cv2.putText(image_rgb, "Estado: Zoom OUT (-)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    mano_cerrada = False
                    mano_agarre = False
                    estado_punto.mapa.aplicar_zoom(1.04)
                
                else:
                    cv2.putText(image_rgb, "Estado: Mano Abierta", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    mano_cerrada = False
                    mano_agarre = False
                    posicion_inicial_norm = None

        if not estado_punto.mapa.pantalla_info_activa:
            # Recortar la imagen de 1280x720 a 720x720 (cuadrado perfecto central)
            h, w, _ = image_rgb.shape
            offset = (w - h) // 2
            image_cuadrada = image_rgb[:, offset:offset+h]
            estado_punto.mapa.actualizar_camara(image_cuadrada)
        
        try:
            estado_punto.mapa.fig.canvas.draw_idle()
            estado_punto.mapa.fig.canvas.flush_events()
        except Exception:
            pass

        await asyncio.sleep(0.01)

    cap.release()

async def main():
    estado_punto = EstadoPunto()
    await Ver_gestos(estado_punto)

if __name__ == "__main__":
    asyncio.run(main())