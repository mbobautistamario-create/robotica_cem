
import pymysql

connection = pymysql.connect(
    host='127.0.0.1', #192.168.0.250
    #port=3306,
    user='mortega907', #tmagnano549
    password='mOrtega585$', #tMagnano221%
    database='c_mundo_db'
)

if connection is not None:
    cur = connection.cursor()

    # CONSULTA SQL
    sql = "SELECT * FROM PAIS"

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