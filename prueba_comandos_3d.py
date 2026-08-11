import cv2, time, os, matplotlib.pyplot as plt
import asyncio
from mapamundi import Mapa

try:
    import mediapipe as mp
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    print("✅ Importación exitosa usando submódulos directos")
except ImportError as e:
    print(f"❌ Error de importación: {e}")

ANCHO, ALTO = 1280, 720
resultados = None 

class EstadoPunto:
    def __init__(self):
        self.mapa = Mapa()
        self.pos_x = ANCHO // 2
        self.pos_y = ALTO // 2

    def actualizar_pos(self, nueva_x, nueva_y):
        self.pos_x = nueva_x
        self.pos_y = nueva_y
    
    def desplazar(self, delta_x, delta_y):
        self.pos_x += delta_x * 0.5
        self.pos_y += delta_y * 0.5
        self.pos_x = max(0, min(ANCHO, self.pos_x))
        self.pos_y = max(0, min(ALTO, self.pos_y))


def Mano_cerrada(results):
    if results.multi_hand_landmarks[0].landmark[8].y > results.multi_hand_landmarks[0].landmark[5].y and \
        results.multi_hand_landmarks[0].landmark[12].y > results.multi_hand_landmarks[0].landmark[9].y and \
        results.multi_hand_landmarks[0].landmark[16].y > results.multi_hand_landmarks[0].landmark[13].y and \
        results.multi_hand_landmarks[0].landmark[20].y > results.multi_hand_landmarks[0].landmark[17].y:
        return True
    return False

def detectar_gesto(resultados):
    # Apretón (Pulgar + Índice)
    punta_indice = resultados.multi_hand_landmarks[0].landmark[8]
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_medio = resultados.multi_hand_landmarks[0].landmark[12]
    
    distancia_x = abs(punta_indice.x - punta_pulgar.x)
    distancia_y = abs(punta_indice.y - punta_pulgar.y)
    
    return distancia_x < 0.05 and distancia_y < 0.05 and punta_medio.y < punta_indice.y

def detectar_zoom_in(resultados):
    # Zoom In: Pulgar (4) + Dedo Medio (12)
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_medio = resultados.multi_hand_landmarks[0].landmark[12]
    
    distancia = ((punta_pulgar.x - punta_medio.x)**2 + (punta_pulgar.y - punta_medio.y)**2)**0.5
    return distancia < 0.05

def detectar_zoom_out(resultados):
    # Zoom Out: Pulgar (4) + Dedo Anular (16)
    punta_pulgar = resultados.multi_hand_landmarks[0].landmark[4]
    punta_anular = resultados.multi_hand_landmarks[0].landmark[16]
    
    distancia = ((punta_pulgar.x - punta_anular.x)**2 + (punta_pulgar.y - punta_anular.y)**2)**0.5
    return distancia < 0.05

def Posicion_mano(results):
    mano = results.multi_hand_landmarks[0]
    eje_y = (mano.landmark[1].y + mano.landmark[5].y + mano.landmark[9].y + mano.landmark[13].y + mano.landmark[17].y) / 5
    eje_x = (mano.landmark[1].x + mano.landmark[5].x + mano.landmark[9].x + mano.landmark[13].x + mano.landmark[17].x) / 5
    return (eje_x, eje_y)

def Obtener_Posicion_Pixeles():
    global resultados
    if resultados is None or not resultados.multi_hand_landmarks:
        return None
    posicion_en_camara = Posicion_mano(resultados)
    return (posicion_en_camara[0] * ANCHO, posicion_en_camara[1] * ALTO)

def Entrar_Pais(pais):
    print(f"Entrando al paquete {pais}")

async def Ver_gestos(estado_punto):  
    global resultados
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)
    mano_cerrada = False
    mano_agarre = False
    posicion_inicial = None

    while cap.isOpened():
        success, image = cap.read()
        if not success: break

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resultados = hands.process(image_rgb)

        if resultados.multi_hand_landmarks:
            for hand_landmarks in resultados.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # 1. Gesto: Mano cerrada (Ingresar al País)
            if Mano_cerrada(resultados):
                mano_agarre = False
                posicion_inicial = None
                cv2.putText(image, "Mano cerrada", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if not mano_cerrada:
                    mano_cerrada = True
                    bandera_cerrada = time.time()
                else:
                    if time.time() - bandera_cerrada > 2:
                        print("Ingresando")
                        bandera_cerrada = time.time()
                        mano_cerrada = False
                        Entrar_Pais(estado_punto.mapa.pais_actual)
                
            # 2. Gesto: Apretón (Mover / Arrastrar Alfiler)
            elif detectar_gesto(resultados):
                cv2.putText(image, "Moviendo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                mano_cerrada = False
                posicion_actual_mano = Obtener_Posicion_Pixeles()

                if not mano_agarre:
                    mano_agarre = True
                    inicio_agarre = time.time()
                    posicion_inicial = posicion_actual_mano
                else:
                    if time.time() - inicio_agarre > 0.01:
                        dx = posicion_actual_mano[0] - posicion_inicial[0]
                        dy = posicion_actual_mano[1] - posicion_inicial[1]
                        
                        estado_punto.desplazar(dx, dy)

                        x_mapa = (estado_punto.pos_x / ANCHO * 360) - 180
                        y_mapa = 90 - (estado_punto.pos_y / ALTO * 180)
                        
                        estado_punto.mapa.Actualizar_puntos(x=x_mapa, y=y_mapa)

                        posicion_inicial = posicion_actual_mano
                        inicio_agarre = time.time()

            # 3. Gesto: Zoom In (Pulgar + Medio)
            elif detectar_zoom_in(resultados):
                cv2.putText(image, "Zoom +", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                mano_cerrada = False
                mano_agarre = False
                estado_punto.mapa.aplicar_zoom(0.96)  # Factor < 1 acerca la vista

            # 4. Gesto: Zoom Out (Pulgar + Anular)
            elif detectar_zoom_out(resultados):
                cv2.putText(image, "Zoom -", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2)
                mano_cerrada = False
                mano_agarre = False
                estado_punto.mapa.aplicar_zoom(1.04)  # Factor > 1 aleja la vista
            
            # 5. Estado por defecto: Mano Abierta
            else:
                cv2.putText(image, "Mano abierta", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                mano_cerrada = False
                mano_agarre = False
                posicion_inicial = None
            
            x, y = Posicion_mano(resultados)
            cv2.circle(image, (int(x*image.shape[1]), int(y*image.shape[0])), 5, (0, 0, 255), 2)
                
        cv2.imshow('Conoce el Mundo - Test IA', image)
        if cv2.waitKey(5) & 0xFF == 27: break
        
        await asyncio.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()

async def main():
    estado_punto = EstadoPunto()
    await Ver_gestos(estado_punto)

if __name__ == "__main__":
    asyncio.run(main())