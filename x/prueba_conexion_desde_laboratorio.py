
import pymysql

connection = pymysql.connect(
    host='192.168.0.250',
    port=3306,
    user='tmagnano549',
    password='tMagnano221%',
    database='c_mundo_db'
)

if connection is not None:
    cur = connection.cursor()

    # CONSULTA SQL
    sql = "SELECT * FROM tu_tabla"

    # EJECUCIÓN
    cur.execute(sql)

    # RECUPERAR FILAS
    rows = cur.fetchall()

    # CONFIRMAR
    connection.commit()

    # MOSTRAR RESULTADOS
    print()
    print("Toda la lista en una sola línea:")
    print(rows)

    print()
    print("Toda la lista en líneas separadas:")
    for i in rows:
        print(i)

connection.close()