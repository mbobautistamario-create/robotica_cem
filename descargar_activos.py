import os
import requests
import paramiko
import mysql.connector
from sshtunnel import SSHTunnelForwarder

# Configuraciones
CARPETA_DESTINO = "imagenes"
ARCHIVO_MAPEO = "mapeo_imagenes.txt"

def cargar_mapeo():
    """Lee el archivo de texto plano y lo convierte en un diccionario de Python."""
    mapeo = {}
    if os.path.exists(ARCHIVO_MAPEO):
        with open(ARCHIVO_MAPEO, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if "|" in linea:
                    url, ruta_local = linea.split("|", 1)
                    mapeo[url] = ruta_local
    return mapeo

def guardar_mapeo(mapeo):
    """Guarda el diccionario en el archivo de texto plano usando el separador '|'."""
    with open(ARCHIVO_MAPEO, "w", encoding="utf-8") as f:
        for url, ruta_local in mapeo.items():
            f.write(f"{url}|{ruta_local}\n")

def obtener_urls_de_bd():
    """Se conecta al laboratorio mediante SSH y extrae todas las URLs de las 3 tablas."""
    urls = set() # Usamos un 'set' (conjunto) para evitar URLs duplicadas
    
    if not hasattr(paramiko, 'DSSKey'):
        paramiko.DSSKey = paramiko.RSAKey

    print("🌐 Conectando a la Base de Datos a través del túnel SSH...")
    try:
        with SSHTunnelForwarder(
            ("ismdf.dynv6.net", 22),
            ssh_username="alumno6to",
            ssh_password="Ismdf.309",
            remote_bind_address=("127.0.0.1", 3306)
        ) as server:
            conexion = mysql.connector.connect(
                host="127.0.0.1",
                port=server.local_bind_port,
                user="mortega907",
                password="mOrtega585$",
                database="c_mundo_db"
            )
            cursor = conexion.cursor()
            
            # Consultamos las 3 tablas donde hay imágenes
            consultas = [
                "SELECT imagen FROM GENERAL WHERE imagen IS NOT NULL AND imagen != '';",
                "SELECT imagen FROM GASTRONOMIA WHERE imagen IS NOT NULL AND imagen != '';",
                "SELECT imagen FROM TURISMO WHERE imagen IS NOT NULL AND imagen != '';"
            ]
            
            for query in consultas:
                cursor.execute(query)
                for (imagen_url,) in cursor.fetchall():
                    # Solo tomamos lo que empiece con http para ignorar archivos locales viejos
                    if imagen_url.startswith("http"):
                        urls.add(imagen_url.strip())
                        
            cursor.close()
            conexion.close()
            print(f"✅ Se encontraron {len(urls)} URLs únicas en la base de datos.")
            return urls
    except Exception as e:
        print(f"⚠️ Error al conectar con la BD: {e}")
        return set()

def main():
    # 1. Preparar el entorno
    if not os.path.exists(CARPETA_DESTINO):
        os.makedirs(CARPETA_DESTINO)
        print(f"📁 Carpeta '{CARPETA_DESTINO}' creada.")

    # 2. Cargar el estado actual (El diccionario de linkeo)
    mapeo_actual = cargar_mapeo()
    urls_bd = obtener_urls_de_bd()

    if not urls_bd:
        print("No hay URLs para procesar. Saliendo...")
        return

    # 3. Lógica de Descarga Inteligente
    nuevas_descargas = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'} # Evita bloqueos de algunos servidores

    for i, url in enumerate(urls_bd):
        # Si la URL ya está en el diccionario y el archivo físico existe, la saltamos
        if url in mapeo_actual and os.path.exists(mapeo_actual[url]):
            continue

        print(f"⬇️ Descargando ({i+1}/{len(urls_bd)}): {url[:50]}...")
        
        try:
            respuesta = requests.get(url, headers=headers, timeout=5)
            if respuesta.status_code == 200:
                # Generamos un nombre seguro usando un contador para evitar caracteres raros en la URL
                nombre_archivo = f"img_descargada_{len(mapeo_actual) + 1}.jpg"
                ruta_local = os.path.join(CARPETA_DESTINO, nombre_archivo)
                
                with open(ruta_local, 'wb') as f:
                    f.write(respuesta.content)
                
                # Actualizamos nuestro diccionario en memoria
                mapeo_actual[url] = ruta_local
                nuevas_descargas += 1
            else:
                print(f"   ❌ Error HTTP {respuesta.status_code}")
        except Exception as e:
            print(f"   ❌ Error de red: {e}")

    # 4. Guardar el estado final
    guardar_mapeo(mapeo_actual)
    
    print("\n======================================")
    print(f"🎉 Proceso finalizado.")
    print(f"   Imágenes nuevas descargadas: {nuevas_descargas}")
    print(f"   Total de imágenes en el diccionario: {len(mapeo_actual)}")
    print("======================================")

if __name__ == "__main__":
    main()