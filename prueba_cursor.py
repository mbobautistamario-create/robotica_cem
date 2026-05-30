import cv2, time, os 
import pygame
import asyncio 
# Intentamos la importación alternativa que suele saltarse el error de 'solutions'
try:
    import mediapipe as mp
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    print("✅ Importación exitosa usando submódulos directos")
except ImportError as e:
    print(f"❌ Error de importación: {e}")


# --- Configuración Inicial ---
ANCHO, ALTO = 1280, 720
COLOR_FONDO = (30, 30, 30)
COLOR_PUNTO = (0, 255, 200)
RADIO_PUNTO = 10

class MotorGrafico:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Punto Asincrónico con Pygame")
        self.reloj = pygame.time.Clock()
        self.ejecutando = True
        
        # Posición inicial del punto
        self.pos_x = ANCHO // 2
        self.pos_y = ALTO // 2

    def actualizar_pos(self, nueva_x, nueva_y):
        """
        Función solicitada para decirle al script 
        dónde pintar el punto nuevamente.
        """
        self.pos_x = nueva_x
        self.pos_y = nueva_y
        #print("actualizado a: ", self.pos_x, "-", self.pos_y)
    
    def desplazar(self, delta_x, delta_y):
        """
        Función solicitada para desplazar el punto.
        """
        # Aplicamos un factor de escala si es necesario para que el movimiento sea suave
        self.pos_x += delta_x * 0.5
        self.pos_y += delta_y * 0.5
        
        # Mantener el punto dentro de la pantalla
        self.pos_x = max(0, min(ANCHO, self.pos_x))
        self.pos_y = max(0, min(ALTO, self.pos_y))
        #print("desplazado a: ", self.pos_x, "-", self.pos_y)

    async def bucle_principal(self):
        while self.ejecutando:
            # 1. Manejo de eventos (Cerrar ventana)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.ejecutando = False

            self.pantalla.fill(COLOR_FONDO)
            # Convertimos a int() para que Pygame no tenga problemas de renderizado
            pygame.draw.circle(self.pantalla, COLOR_PUNTO, (int(self.pos_x), int(self.pos_y)), RADIO_PUNTO)
            pygame.display.flip()

            # 4. Control de FPS y cedido de control asincrónico
            # Esto evita que Pygame bloquee el hilo y permite que otras tareas corran
            await asyncio.sleep(0) 
            self.reloj.tick(60)

        pygame.quit()


def Mano_cerrada(results):
    if results.multi_hand_landmarks[0].landmark[8].y > results.multi_hand_landmarks[0].landmark[5].y and \
        results.multi_hand_landmarks[0].landmark[12].y > results.multi_hand_landmarks[0].landmark[9].y and \
        results.multi_hand_landmarks[0].landmark[16].y > results.multi_hand_landmarks[0].landmark[13].y and \
        results.multi_hand_landmarks[0].landmark[20].y > results.multi_hand_landmarks[0].landmark[17].y:
        return True
    else:
        return False

def Posicion_mano(results):
    mano = results.multi_hand_landmarks[0]
    eje_y = (mano.landmark[1].y + mano.landmark[5].y + mano.landmark[9].y + mano.landmark[13].y + mano.landmark[17].y) / 5
    eje_x = (mano.landmark[1].x + mano.landmark[5].x + mano.landmark[9].x + mano.landmark[13].x + mano.landmark[17].x) / 5
    return (eje_x, eje_y)

def Cursor(results):
    posicion_en_camara = Posicion_mano(results)
    x = posicion_en_camara[0] * 1280
    y = posicion_en_camara[1] * 720
    return (x, y)

async def Ver_gestos(motor_grafico):  
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)
    mano_cerrada = False
    bandera_actualizacion = time.time()
    while cap.isOpened():
        success, image = cap.read()
        if not success: break

        image = cv2.flip(image, 1) # Efecto espejo para que sea natural
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if Mano_cerrada(results):
                cv2.putText(image, "Mano cerrada", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if mano_cerrada == False:
                    mano_cerrada = True
                    bandera_cerrada = time.time()
                    print("inicio bandera")
                else:
                    if time.time() - bandera_cerrada > 2:
                        print("Ingresando")
                        bandera_cerrada = time.time()
                        mano_cerrada = False
            
            else:
                cv2.putText(image, "Mano abierta", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                mano_cerrada = False
                bandera_cerrada = 0
            
            if time.time() - bandera_actualizacion > 0.01:
                #x, y = Posicion_mano(results)
                #cv2.circle(image, (int(x*image.shape[1]), int(y*image.shape[0])), 5, (0, 0, 255), 2)
                cursor_x, cursor_y = Cursor(results)
                motor_grafico.actualizar_pos(cursor_x, cursor_y)
                bandera_actualizacion = time.time()
                
        cv2.imshow('Conoce el Mundo - Test IA', image)
        if cv2.waitKey(5) & 0xFF == 27: break

        await asyncio.sleep(0) # Cede el control a Pygame
    cap.release()
    cv2.destroyAllWindows()

async def main():
    motor = MotorGrafico()
    await asyncio.gather(
        motor.bucle_principal(),
        Ver_gestos(motor)
    )

asyncio.run(main())

