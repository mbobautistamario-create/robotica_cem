import os
import requests
import paramiko
import mysql.connector
from sshtunnel import SSHTunnelForwarder

CARPETA_DESTINO = "imagenes"
ARCHIVO_MAPEO = "mapeo_imagenes.txt"

def cargar_mapeo():
    mapeo = {}
    if os.path.exists(ARCHIVO_MAPEO):
        with open(ARCHIVO_MAPEO, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if "|" in linea:
                    url, ruta = linea.split("|", 1)
                    mapeo[url] = ruta
    return mapeo

def guardar_mapeo(mapeo):
    with open(ARCHIVO_MAPEO, "w", encoding="utf-8") as f:
        for url, ruta in mapeo.items():
            f.write(f"{url}|{ruta}\n")

def obtener_urls_de_bd():
    urls = set()
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
                host="127.0.0.1", port=server.local_bind_port,
                user="mortega907", password="mOrtega585$", database="c_mundo_db"
            )
            cursor = conexion.cursor()
            
            # ─── AÑADIDA LA TABLA PAIS A LAS CONSULTAS ───
            consultas = [
                "SELECT imagen FROM PAIS WHERE imagen IS NOT NULL AND imagen != '';",
                "SELECT imagen FROM GENERAL WHERE imagen IS NOT NULL AND imagen != '';",
                "SELECT imagen FROM GASTRONOMIA WHERE imagen IS NOT NULL AND imagen != '';",
                "SELECT imagen FROM TURISMO WHERE imagen IS NOT NULL AND imagen != '';"
            ]
            for query in consultas:
                cursor.execute(query)
                for (img_url,) in cursor.fetchall():
                    if img_url.startswith("http"):
                        urls.add(img_url.strip())
            cursor.close()
            conexion.close()
            return urls
    except Exception as e:
        print(f"⚠️ Error BD: {e}")
        return set()

def main():
    if not os.path.exists(CARPETA_DESTINO):
        os.makedirs(CARPETA_DESTINO)

    mapeo_actual = cargar_mapeo()
    urls_bd = obtener_urls_de_bd()

    if not urls_bd:
        print("No hay URLs para procesar.")
        return

    nuevas_descargas = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for i, url in enumerate(urls_bd):
        if url in mapeo_actual and os.path.exists(mapeo_actual[url]):
            continue

        print(f"⬇️ Evaluando ({i+1}/{len(urls_bd)}): {url[:50]}...")
        try:
            respuesta = requests.get(url, headers=headers, timeout=5)
            content_type = respuesta.headers.get('Content-Type', '').lower()
            
            if respuesta.status_code == 200 and 'image' in content_type:
                ext = content_type.split('/')[-1] 
                if ext == 'jpeg': ext = 'jpg'
                
                nombre_archivo = f"img_descargada_{len(mapeo_actual) + 1}.{ext}"
                ruta_local = os.path.join(CARPETA_DESTINO, nombre_archivo)
                
                with open(ruta_local, 'wb') as f:
                    f.write(respuesta.content)
                
                mapeo_actual[url] = ruta_local
                nuevas_descargas += 1
                print(f"   ✅ Descargada con éxito.")
            else:
                print(f"   ❌ Ignorada: El link no es una foto directa (Content-Type: {content_type}).")
        except Exception as e:
            print(f"   ❌ Error de red: {e}")

    guardar_mapeo(mapeo_actual)
    print(f"\n🎉 Proceso finalizado. Imágenes reales descargadas: {nuevas_descargas}")

if __name__ == "__main__":
    main()