import paramiko
from sshtunnel import SSHTunnelForwarder
import mysql.connector

def main():
    # Parche para compatibilidad entre Paramiko >= 3.0 y sshtunnel
    if not hasattr(paramiko, 'DSSKey'):
        paramiko.DSSKey = paramiko.RSAKey

    # Configuración del servidor SSH
    #SSH_HOST = "ismdf.dynv6.net"
    SSH_HOST = "181.104.24.24"
    SSH_PORT = 22
    SSH_USER = "alumno6to"
    SSH_PASSWORD = "Ismdf.309"

    # Configuración de la Base de Datos
    DB_HOST_DESTINO = "127.0.0.1"
    DB_PORT_DESTINO = 3306
    DB_NAME = "c_mundo_db"
    DB_USER = "mortega907"
    DB_PASSWORD = "mOrtega585$"

    # 1. Crear y abrir el túnel SSH
    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        remote_bind_address=(DB_HOST_DESTINO, DB_PORT_DESTINO)
    ) as server:

        print(f"¡Túnel SSH establecido con éxito!")

        try:
            # 2. Conexión a la Base de Datos
            conexion = mysql.connector.connect(
                host="127.0.0.1",
                port=server.local_bind_port,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )

            if conexion.is_connected():
                cursor = conexion.cursor()

                # --- PASO A: Obtenemos y mostramos la lista de tablas ---
                cursor.execute("SHOW TABLES;")
                tablas_raw = cursor.fetchall()
                
                # Extraemos los nombres de las tablas en una lista simple
                tablas = [t[0] for t in tablas_raw]

                print("\n========================================")
                print(f" Tablas disponibles en '{DB_NAME}':")
                print("========================================")
                for i, nombre_tabla in enumerate(tablas, 1):
                    print(f"  [{i}] {nombre_tabla}")

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

                    print(f"\nObteniendo datos de la tabla '{tabla_seleccionada}'...")
                    cursor.execute(f"SELECT * FROM `{tabla_seleccionada}` LIMIT 50;")
                    registros = cursor.fetchall()

                    print(f"\n--- Contenido de '{tabla_seleccionada}' (máx. 50 registros) ---")
                    if registros:
                        for fila in registros:
                            print(fila)
                    else:
                        print("La tabla está vacía.")
                else:
                    print("\nSelección no válida. Operación cancelada.")

                cursor.close()
                conexion.close()

        except mysql.connector.Error as err:
            print(f"\nError en la base de datos: {err}")

if __name__ == "__main__":
    main()