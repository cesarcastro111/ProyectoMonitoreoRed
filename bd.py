import sqlite3
from datetime import datetime

class GestorBD:
    def __init__(self, nombre_db="monitoreo.db"):
        self.nombre_db = nombre_db

    def conectar(self):
        
        conexion = sqlite3.connect(self.nombre_db)
        
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion
    
    def inicializar_tablas(self):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()

            sql_tabla_objetivos = "CREATE TABLE IF NOT EXISTS objetivos (id_objetivo INTEGER PRIMARY KEY AUTOINCREMENT,ip TEXT NOT NULL, hostname TEXT NOT NULL);"
            
            
            sql_tabla_historial = """
                CREATE TABLE IF NOT EXISTS historial (
                    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                    latencia REAL NOT NULL,
                    jitter REAL NOT NULL,
                    perdida REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    id_objetivo INTEGER,
                    FOREIGN KEY(id_objetivo) REFERENCES objetivos(id_objetivo) ON DELETE CASCADE
                );
            """

            cursor.execute(sql_tabla_objetivos)
            cursor.execute(sql_tabla_historial)

            conexion.commit()
            print("Base de datos inicializada correctamente")
        except Exception as e:
            print(f"Error inicializando la base de datos: {e}")
        finally:
            conexion.close()

    def agregar_objetivo(self, ip, hostname):
        conexion = self.conectar()
        cursor = conexion.cursor()

        sql = "INSERT INTO objetivos (ip, hostname) VALUES(?, ?)"
        cursor.execute(sql, (ip, hostname))

        conexion.commit()
        conexion.close()

    def obtener_objetivos(self):
        conexion = self.conectar()
        cursor = conexion.cursor()

        sql = "SELECT * FROM objetivos"

        cursor.execute(sql)
        resultados = cursor.fetchall() 

        conexion.close()
        return resultados
    
    def guardar_resultado(self, id_objetivo, latencia, jitter, perdida, fecha):
        conexion = self.conectar()
        cursor = conexion.cursor()

        sql = "INSERT into historial (latencia, jitter, perdida, fecha, id_objetivo) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(sql, (latencia, jitter, perdida, fecha, id_objetivo))

        conexion.commit()
        conexion.close() 

    def obtener_historial(self, id_objetivo, limite=20):
       
        conexion = self.conectar()
        cursor = conexion.cursor()

        sql = "SELECT latencia, jitter, perdida, fecha FROM historial WHERE id_objetivo = ? ORDER BY id_registro DESC LIMIT ?" 

        cursor.execute(sql, (id_objetivo, limite))
        resultados = cursor.fetchall()
        conexion.close()

        
        return resultados[::-1]

    def obtener_historial_por_tiempo(self, id_objetivo, minutos):
        
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        
        sql = "SELECT latencia, jitter, perdida, fecha FROM historial WHERE id_objetivo = ? ORDER BY id_registro DESC"
        cursor.execute(sql, (id_objetivo,))
        todos_los_datos = cursor.fetchall()
        conexion.close()

        
        if minutos == 0:
            return todos_los_datos[::-1]

        datos_filtrados = []
        ahora = datetime.now()
        
        for fila in todos_los_datos:
            fecha_str = fila[3] 
            try:
                
                fecha_dt = datetime.strptime(fecha_str, "%d-%m-%Y %H:%M:%S")
                diferencia = ahora - fecha_dt
                
                
                minutos_diferencia = diferencia.total_seconds() / 60
                
                if minutos_diferencia <= minutos:
                    datos_filtrados.append(fila)
                else:
                    
                    break 
            except ValueError:
                
                continue

        
        return datos_filtrados[::-1]

    def eliminar_objetivo(self, id_objetivo):
        conexion = self.conectar()
        cursor = conexion.cursor()
        try:
            
            cursor.execute("DELETE FROM historial WHERE id_objetivo = ?", (id_objetivo,))
            
            
            cursor.execute("DELETE FROM objetivos WHERE id_objetivo = ?", (id_objetivo,))
            
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar: {e}")
            return False
        finally:
            conexion.close()

if __name__ == "__main__":
    db = GestorBD()
    db.inicializar_tablas()