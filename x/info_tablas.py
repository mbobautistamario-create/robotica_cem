import paramiko
import socket
from sshtunnel import SSHTunnelForwarder
import mysql.connector

ROJO = "\033[31m"
VERDE = "\033[32m"
AMARILLO = "\033[33m"
NORMAL = "\033[0m"


def main():
    # Parche para compatibilidad entre Paramiko >= 3.0 y sshtunnel
    if not hasattr(paramiko, 'DSSKey'):
        paramiko.DSSKey = paramiko.RSAKey

    # Configuración del servidor SSH
    SSH_HOST = "ismdf.dynv6.net"
    #SSH_HOST = "181.104.24.24"
    SSH_PORT = 22
    SSH_USER = "alumno6to"
    SSH_PASSWORD = "Ismdf.309"

    # Configuración de la Base de Datos
    DB_HOST_DESTINO = "127.0.0.1"
    DB_PORT_DESTINO = 3306
    DB_NAME = "c_mundo_db"
    DB_USER = "mortega907"
    DB_PASSWORD = "mOrtega585$"

    try:
        print(AMARILLO + "Intentando abrir el túnel SSH..." + NORMAL, flush=True)

        # 1. Crear y abrir el túnel SSH
        with SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST_DESTINO, DB_PORT_DESTINO)
        ) as server:
            print(VERDE + "¡Túnel SSH establecido con éxito!" + NORMAL, flush=True)
            print(
                AMARILLO
                + f"Puerto local del túnel: {server.local_bind_port}"
                + NORMAL,
                flush=True
            )

            # 2. Conexión a la Base de Datos
            print(AMARILLO + "Comprobando el puerto MySQL a través del túnel..." + NORMAL, flush=True)
            try:
                with socket.create_connection(
                    ("127.0.0.1", server.local_bind_port),
                    timeout=5
                ):
                    print(VERDE + "El puerto MySQL responde." + NORMAL, flush=True)
            except OSError as err:
                raise ConnectionError(
                    "El servidor SSH responde, pero MySQL no responde en "
                    f"{DB_HOST_DESTINO}:{DB_PORT_DESTINO} a través del túnel: {err}"
                ) from err

            print(AMARILLO + "Intentando conectar con MySQL..." + NORMAL, flush=True)
            conexion = mysql.connector.connect(
                host="127.0.0.1",
                port=server.local_bind_port,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connection_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            print(VERDE + "Conexión con MySQL establecida." + NORMAL, flush=True)

            if conexion.is_connected():
                cursor = conexion.cursor()

                # --- PASO A: Obtenemos y mostramos la lista de tablas ---
                print(AMARILLO + "Consultando las tablas..." + NORMAL, flush=True)
                cursor.execute("SHOW TABLES;")
                tablas_raw = cursor.fetchall()

                # Extraemos los nombres de las tablas en una lista simple
                tablas = [t[0] for t in tablas_raw]

                print(VERDE + "\n========================================" + NORMAL)
                print(VERDE + f" Tablas disponibles en '{DB_NAME}':" + NORMAL)
                print(VERDE + "========================================" + NORMAL)
                for i, nombre_tabla in enumerate(tablas, 1):
                    print(VERDE + f"  [{i}] {nombre_tabla}" + NORMAL)

                if not tablas:
                    print(ROJO + "No hay tablas disponibles." + NORMAL)

                # --- PASO B: Selección interactiva de la tabla ---
                opcion = input("\nIngresa el número o el nombre de la tabla que deseas abrir: ").strip()

                tabla_seleccionada = None
                if opcion.isdigit():
                    indice = int(opcion) - 1
                    if 0 <= indice < len(tablas):
                        tabla_seleccionada = tablas[indice]
                elif opcion in tablas:
                    tabla_seleccionada = opcion

                # --- PASO C: Mostrar el contenido de la tabla seleccionada ---
                if tabla_seleccionada:
                    # Usamos dictionary=True para ver las columnas con sus nombres
                    cursor.close()
                    cursor = conexion.cursor(dictionary=True)

                    print(
                        VERDE
                        + f"\nObteniendo datos de la tabla '{tabla_seleccionada}'..."
                        + NORMAL
                    )
                    cursor.execute(f"SELECT * FROM `{tabla_seleccionada}` LIMIT 50;")
                    registros = cursor.fetchall()

                    print(
                        VERDE
                        + f"\n--- Contenido de '{tabla_seleccionada}' (máx. 50 registros) ---"
                        + NORMAL
                    )
                    if registros:
                        for fila in registros:
                            print(VERDE + str(fila) + NORMAL)
                    else:
                        print(ROJO + "La tabla está vacía." + NORMAL)
                else:
                    print(ROJO + "\nSelección no válida. Operación cancelada." + NORMAL)

                cursor.close()
                conexion.close()

    except mysql.connector.Error as err:
        print(ROJO + f"\nError en la base de datos: {err}" + NORMAL, flush=True)
    except Exception as err:
        print(ROJO + f"\nError en SSH o en la conexión: {err}" + NORMAL, flush=True)

if __name__ == "__main__":
    main()