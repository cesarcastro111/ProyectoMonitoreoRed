from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile
import os

class MiReporte(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte de Red', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.ln(10)

def hacer_grafica(datos):
    lats = []
    for d in datos:
        lats.append(d[0])
        
    plt.figure(figsize=(8, 4))
    plt.plot(lats)
    plt.title('Latencia (ms)')
    plt.ylabel('ms')
    plt.grid(True)
    
    f, path = tempfile.mkstemp(suffix=".png")
    plt.savefig(path)
    plt.close()
    os.close(f)
    return path

def generar_reporte(host, datos):
    pdf = MiReporte()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    suma_lat = 0
    suma_jit = 0
    suma_perdida = 0
    n = len(datos)
    
    if n > 0:
        for x in datos:
            suma_lat += x[0]
            suma_jit += x[1]
            suma_perdida += x[2]
            
        prom_lat = suma_lat / n
        prom_jit = suma_jit / n
        prom_perdida = suma_perdida / n
    else:
        prom_lat = 0
        prom_jit = 0
        prom_perdida = 0
    
    pdf.cell(0, 10, f"Objetivo: {host}", ln=True)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumen de Promedios:", ln=True)
    pdf.set_font("Arial", size=12)
    
    pdf.cell(0, 8, f"- Latencia Media: {round(prom_lat, 2)} ms", ln=True)
    pdf.cell(0, 8, f"- Jitter Medio: {round(prom_jit, 2)} ms", ln=True)
    pdf.cell(0, 8, f"- Perdida Total: {round(prom_perdida, 2)} %", ln=True)
    pdf.ln(10)

    if n > 1:
        imagen = hacer_grafica(datos)
        pdf.image(imagen, x=10, w=190)
        if os.path.exists(imagen):
            os.remove(imagen)
    else:
        pdf.cell(0, 10, "No hay datos para graficar", ln=True)
        
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "Ultimos registros (Detalle):", ln=True)
    
    pdf.cell(50, 8, "Fecha", 1)
    pdf.cell(30, 8, "Latencia", 1)
    pdf.cell(30, 8, "Jitter", 1)
    pdf.cell(30, 8, "Perdida", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    
    ultimos = datos[-15:]
    ultimos.reverse()
    
    for fila in ultimos:
        lat, jit, loss, fecha = fila
        pdf.cell(50, 7, str(fecha), 1)
        pdf.cell(30, 7, str(round(lat, 1)), 1)
        pdf.cell(30, 7, str(round(jit, 1)), 1)
        pdf.cell(30, 7, str(round(loss, 1)), 1)
        pdf.ln()

    nombre_archivo = f"reporte_{host}.pdf"
    pdf.output(nombre_archivo)
    return nombre_archivo