from icmplib import ping
import numpy as np
from datetime import datetime

class MonitoreoRed:
    def obtener_metricas(self, ip_objetivo):
    #Lanzamos cuatro pings con un intervalo de 0.2 s para rapidez
        #priviled=False nos permite correr esto sin permisos de administrador en algunos sistemas
        respuesta = ping(ip_objetivo, count=4, interval=0.2, privileged=False)

        #Latencia
        #icmplib nos da latencia
        latencia = respuesta.avg_rtt

        #Perdida de paquetes
        #icmplib nos da la perdida de paquetes
        perdida = respuesta.packet_loss

        #Jitter
        #icmplib no nos da jitter
        rtts = respuesta.rtts #Lista de round trip times (cuanto tiempo tarda un paquete en ir y su respuesta en llegar) en ms [ms, ms, ms, ms]

        if len(rtts) > 1:
            np_rtts = np.array(rtts) #Convertimos lista a numpy array para poder hacer operaciones con np
            diferencias = np.diff(np_rtts) #np calcula la diferencias entre datos consecutivos
            jitter = np.mean(np.abs(diferencias)) #Aplicamos valor absoluto a las diferencias y sobre el resultado la media de los valores
        else:
            jitter = 0 

        fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S") #formato dias/mes/año hora/minutos/segundos
        return latencia, jitter, perdida, fecha_actual        


