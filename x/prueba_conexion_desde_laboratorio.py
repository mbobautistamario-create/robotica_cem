import mysql.connector
from sshtunnel import SSHTunnelForwarder

# Configuración del servidor SSH
SSH_HOST = "ismdf.dynv6.net"
SSH_PORT = 22
SSH_USER = "alumno6to"
SSH_PASSWORD = "Ismdf.309"  # O puedes usar ssh_pkey para claves privadas RSA/ED25519

# Configuración de la Base de Datos tal como la ve el servidor SSH
DB_HOST_DESTINO = "127.0.0.1"     # O la IP privada de la BD vista desde el servidor SSH
DB_PORT_DESTINO = 3306            # Puerto original de MySQL
DB_NAME = "mortega907"
DB_USER = "mortega907"
DB_PASSWORD = "mOrtega585$"

# --- 1. Crear y abrir el túnel SSH ---
with SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    # Si usas clave RSA en lugar de contraseña:
    # ssh_pkey="ruta/a/tu/id_rsa",
    remote_bind_address=(DB_HOST_DESTINO, DB_PORT_DESTINO)
) as server:

    print(f"¡Túnel SSH establecido con éxito!")
    print(f"Puerto local asignado para la conexión: {server.local_bind_port}")

    # --- 2. Conectarse a la Base de Datos a través del túnel ---
    try:
        conexion = mysql.connector.connect(
            host="127.0.0.1",                  # La conexión ahora apunta a tu propia máquina
            port=server.local_bind_port,        # Usa el puerto local que abrió el túnel
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        if conexion.is_connected():
            cursor = conexion.cursor(dictionary=True)
           
            # Consulta de prueba
            cursor.execute("SELECT * FROM elementos WHERE pais = %s", ("Argentina",))
            resultados = cursor.fetchall()
           
            print("Datos obtenidos correctamente:")
            for fila in resultados:
                print(fila)

            cursor.close()
            conexion.close()

    except mysql.connector.Error as err:
        print(f"Error en la consulta a la base de datos: {err}")

# Al salir del bloque 'with', el túnel SSH se cierra automáticamente de forma segura.