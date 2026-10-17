import paramiko
import mysql.connector
import os
from PIL import Image
import numpy as np
from sshtunnel import SSHTunnelForwarder

class GestorDatosPais:
    def __init__(self):
        if not hasattr(paramiko, 'DSSKey'):
            paramiko.DSSKey = paramiko.RSAKey

        self.cache_paises = {}
        self.conexion = None
        self.server = None
        
        # 1. Cargar el libro de mapeo en memoria
        self.mapeo_local = self._cargar_mapeo_local()
        
        self.traducciones = {
            "United States of America": "Estados Unidos",
            "United States": "Estados Unidos",
            "Brazil": "Brasil",
            "Mexico": "México",
            "Canada": "Canadá",
            "Peru": "Perú",
            "Panama": "Panamá",
            "Haiti": "Haití",
            "Belize": "Belice",
            "Suriname": "Surinam",
            "The Bahamas": "Bahamas",
            "Bahamas": "Bahamas",
            "Grenada": "Granada",
            "Dominican Rep.": "República Dominicana",
            "Dominican Republic": "República Dominicana",
            "Antigua and Barb.": "Antigua y Barbuda",
            "Antigua and Barbuda": "Antigua y Barbuda",
            "Saint Kitts and Nevis": "San Cristóbal y Nieves",
            "St. Kitts and Nevis": "San Cristóbal y Nieves",
            "Saint Lucia": "Santa Lucía",
            "Saint Vincent and the Grenadines": "San Vicente y las Granadinas",
            "St. Vin. and Gren.": "San Vicente y las Granadinas",
            "Trinidad and Tobago": "Trinidad y Tobago"
        }

        print("🌐 Estableciendo túnel SSH y conexión a la base de datos...")
        try:
            self.server = SSHTunnelForwarder(
                ("ismdf.dynv6.net", 22),
                ssh_username="alumno6to",
                ssh_password="Ismdf.309",
                remote_bind_address=("127.0.0.1", 3306)
            )
            self.server.start()
            
            self.conexion = mysql.connector.connect(
                host="127.0.0.1",
                port=self.server.local_bind_port,
                user="mortega907",
                password="mOrtega585$",
                database="c_mundo_db",
                connection_timeout=5
            )
            print("✅ Conexión a la base de datos establecida y lista.")
        except Exception as e:
            print(f"⚠️ Error crítico de conexión: {e}")

    def _cargar_mapeo_local(self):
        """Lee el archivo generado por descargar_activos.py y retorna un diccionario."""
        mapeo = {}
        ruta_archivo = "mapeo_imagenes.txt"
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if "|" in linea:
                        url, ruta_local = linea.split("|", 1)
                        mapeo[url] = ruta_local
            print(f"✅ Mapeo cargado: {len(mapeo)} imágenes indexadas localmente.")
        else:
            print("⚠️ No se encontró 'mapeo_imagenes.txt'. Las imágenes no se cargarán.")
        return mapeo

    def traducir_nombre(self, nombre_ing):
        return self.traducciones.get(nombre_ing, nombre_ing)

    def cargar_imagen_local(self, ruta_db):
        """Busca la URL en el diccionario y carga el archivo físico correspondiente."""
        imagen_error = np.full((300, 400, 3), 80, dtype=np.uint8)
        
        if not ruta_db:
            return imagen_error

        ruta_db = ruta_db.strip()
        ruta_fisica = None

        # Si es una URL de la BD, buscamos su equivalente local en el mapeo
        if ruta_db.startswith("http"):
            ruta_fisica = self.mapeo_local.get(ruta_db)
        else:
            # Para casos como 'surinam.png' que ya son rutas relativas en la BD
            ruta_fisica = ruta_db

        # Intentamos abrir el archivo físico
        if ruta_fisica and os.path.exists(ruta_fisica):
            try:
                img_pil = Image.open(ruta_fisica).convert("RGB")
                return np.array(img_pil)
            except Exception as e:
                print(f"⚠️ Archivo corrupto o ilegible ({ruta_fisica}): {e}")
        else:
            print(f"⚠️ Imagen no encontrada en disco para: {ruta_db[:40]}...")

        return imagen_error

    def obtener_info_pais(self, nombre_geojson):
        nombre_es = self.traducir_nombre(nombre_geojson)

        if nombre_es in self.cache_paises:
            return self.cache_paises[nombre_es]

        info = {
            "general": {"titulo": "Sin Datos", "subtitulo": "", "cuerpo": "No hay información.", "imagen": np.zeros((10,10,3), dtype=np.uint8)},
            "cultura": {"titulo": "Sin Datos", "subtitulo": "", "cuerpo": "No hay información.", "imagen": np.zeros((10,10,3), dtype=np.uint8)},
            "datos": {"titulo": "Sin Datos", "subtitulo": "", "cuerpo": "No hay información.", "imagen": np.zeros((10,10,3), dtype=np.uint8)}
        }

        if not self.conexion or not self.conexion.is_connected():
            return info

        try:
            cursor = self.conexion.cursor(dictionary=True)
            cursor.execute("SELECT ID_pais FROM PAIS WHERE nombre = %s LIMIT 1;", (nombre_es,))
            pais_db = cursor.fetchone()
            
            if pais_db:
                id_pais = pais_db['ID_pais']

                # ─── 1. GENERAL ───
                cursor.execute("SELECT descripcion, historia, relieve, imagen FROM GENERAL WHERE ID_pais = %s LIMIT 1;", (id_pais,))
                general = cursor.fetchone()
                if not general: 
                    cursor.execute("SELECT descripcion, historia, relieve, imagen FROM GENERAL WHERE descripcion LIKE %s LIMIT 1;", (f"{nombre_es} -%",))
                    general = cursor.fetchone()

                if general:
                    desc_cruda = general.get('descripcion', '')
                    subtitulo = desc_cruda.split('-', 1)[1].strip() if '-' in desc_cruda else desc_cruda
                    cuerpo_gen = f"■ HISTORIA:\n{general.get('historia', '')}\n\n■ RELIEVE:\n{general.get('relieve', '')}"
                    
                    info["general"] = {
                        "titulo": "Resumen Geopolítico",
                        "subtitulo": subtitulo,
                        "cuerpo": cuerpo_gen,
                        "imagen": self.cargar_imagen_local(general.get('imagen'))
                    }

                # ─── 2. CULTURA (GASTRONOMÍA) ───
                cursor.execute("SELECT descripcion, imagen FROM GASTRONOMIA WHERE ID_pais = %s LIMIT 1;", (id_pais,))
                gastro = cursor.fetchone()
                if gastro:
                    desc_cruda = gastro.get('descripcion', '')
                    # Separador inteligente para extraer "Argentina - Asado: Carne..." -> "Asado"
                    if '-' in desc_cruda and ':' in desc_cruda:
                        partes = desc_cruda.split('-', 1)[1].split(':', 1)
                        plato = partes[0].strip()
                        receta = partes[1].strip()
                    else:
                        plato = "Plato Tradicional"
                        receta = desc_cruda

                    info["cultura"] = {
                        "titulo": "Gastronomía Regional",
                        "subtitulo": f"Plato Destacado: {plato}",
                        "cuerpo": receta,
                        "imagen": self.cargar_imagen_local(gastro.get('imagen'))
                    }

                # ─── 3. TURISMO ───
                cursor.execute("SELECT descripcion, cant_lugares, imagen FROM TURISMO WHERE id_pais = %s LIMIT 1;", (id_pais,))
                turismo = cursor.fetchone()
                if turismo:
                    desc_cruda = turismo.get('descripcion', '')
                    if '-' in desc_cruda and ':' in desc_cruda:
                        lugar = desc_cruda.split('-', 1)[1].split(':', 1)
                        nombre_lugar = lugar[0].strip()
                        desc_lugar = lugar[1].strip()
                    else:
                        nombre_lugar = "Punto de Interés"
                        desc_lugar = desc_cruda

                    cuerpo_tur = f"{desc_lugar}\n\n► Destinos catalogados en el país: {turismo.get('cant_lugares', 0)}"
                    info["datos"] = {
                        "titulo": "Turismo y Exploración",
                        "subtitulo": f"Destino Principal: {nombre_lugar}",
                        "cuerpo": cuerpo_tur,
                        "imagen": self.cargar_imagen_local(turismo.get('imagen'))
                    }

            cursor.close()
            self.cache_paises[nombre_es] = info

        except mysql.connector.Error as err:
            print(f"⚠️ Error SQL: {err}")

        return info

    def cerrar_conexion(self):
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
        if self.server:
            self.server.stop()