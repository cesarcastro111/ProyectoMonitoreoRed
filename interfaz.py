import customtkinter as ctk
from bd import GestorBD
import socket
from medicion import MonitoreoRed
from reporte import generar_reporte 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from tkinter import messagebox


ctk.set_appearance_mode("Light")  
ctk.set_default_color_theme("dark-blue") 


class VentanaAyuda(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Manual de Usuario | Ayuda")
        self.geometry("540x700") 
        self.resizable(False, True)
        self.attributes("-topmost", True)
        
        self.lbl_titulo = ctk.CTkLabel(self, text="Manual de Usuario", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_titulo.pack(pady=10)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        
        self.agregar_seccion("1. ¿Para qué sirve este software?", 
                             "Esta herramienta monitorea la calidad de tu conexión hacia servidores para detectar si tu internet está fallando.")
        
        
        self.agregar_seccion("2. ¿Qué significan las metricas?", "")
        
        self.agregar_dato("Latencia (Ping):", 
                          "Es el tiempo que tarda un dato en ir y volver. Se mide en milisegundos (ms).\n"
                          "• Ideal: Menos de 50ms.\n"
                          "• Aceptable: Entre 50ms y 100ms.\n"
                          "• Malo: Más de 150ms.")
        
        self.agregar_dato("Jitter (Inestabilidad):", 
                          "Mide qué tan constante es tu velocidad.\n"
                          "• Ideal: Menos de 30ms.\n"
                          "• Malo: Más de 30ms.")
        
        self.agregar_dato("Pérdida de Paquetes (%):", 
                          "Datos que se envían pero nunca llegan a su destino.\n"
                          "• Debe ser siempre 0%.\n"
                          "• Cualquier valor mayor a 0% indica una falla grave.")

        
        self.agregar_seccion("3. ¿Cómo leer las gráficas?", "")
        
        self.agregar_dato("Eje Horizontal (X) -> EL TIEMPO", 
                          "La línea de abajo representa el paso del tiempo.\n"
                          "• Izquierda = Pasado.\n"
                          "• Derecha = Presente.")

        self.agregar_dato("Eje Vertical (Y) -> LA CANTIDAD", 
                          "La altura de la línea indica la intensidad del problema.\n"
                          "• Gráficas Azul/Naranja: Más alto = Más lento (Milisegundos).\n"
                          "• Gráfica Roja: Más alto = Más datos perdidos (Porcentaje).")
        
        self.agregar_dato("Resumen de Colores:", 
                             "• Azul (Latencia).\n"
                             "• Naranja (Jitter):.\n"
                             "• Roja (Pérdida):.")

        
        self.agregar_seccion("4. Herramientas Adicionales", 
                             "• Filtro de Tiempo.\n"
                             "• Reporte PDF: Genera un documento PDF.")

        self.btn_cerrar = ctk.CTkButton(self.scroll, text="Entendido", command=self.destroy, fg_color="#333333")
        self.btn_cerrar.pack(pady=20)

    def agregar_seccion(self, titulo, texto):
        lbl_t = ctk.CTkLabel(self.scroll, text=titulo, anchor="w", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1F2937")
        lbl_t.pack(fill="x", pady=(15, 5))
        if texto:
            lbl_d = ctk.CTkLabel(self.scroll, text=texto, anchor="w", justify="left", wraplength=460, text_color="#4B5563")
            lbl_d.pack(fill="x")

    def agregar_dato(self, subtitulo, texto):
        lbl_s = ctk.CTkLabel(self.scroll, text=subtitulo, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2563EB")
        lbl_s.pack(fill="x", pady=(5, 0))
        lbl_d = ctk.CTkLabel(self.scroll, text=texto, anchor="w", justify="left", wraplength=460, text_color="#4B5563")
        lbl_d.pack(fill="x", pady=(0, 5))



class MonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = GestorBD()
        self.db.inicializar_tablas()
        self.monitor = MonitoreoRed()
        self.monitoreo_activo = True 
        self.iniciar_monitoreo()
        self.ventana_ayuda = None 

        self.title("Monitor de Red") 
        self.geometry("1150x700")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.id_seleccionado = None
        self.hostname_seleccionado = "" 
        
        self.crear_widgets()
        self.inicializar_graficos()
        self.actualizar_graficos_bucle()
        
    def crear_widgets(self):
        #sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#F9F9FA")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
         
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Panel de Control", 
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color="#333333"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        #Sección:Nuevo Objetivo
        self.label_host = ctk.CTkLabel(self.sidebar_frame, text="NUEVO OBJETIVO", anchor="w", 
                                       font=ctk.CTkFont(size=11, weight="bold"), text_color="#777777")
        self.label_host.grid(row=1, column=0, padx=25, pady=(10, 5), sticky="ew")
       
        self.entry_hostname = ctk.CTkEntry(self.sidebar_frame, placeholder_text="ej. google.com", height=35)
        self.entry_hostname.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.btn_agregar = ctk.CTkButton(
            self.sidebar_frame, 
            text="+ Agregar", 
            command=self.agregar_objetivo, 
            fg_color="#10B981", 
            hover_color="#059669",
            height=35,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_agregar.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        #Sección:Lista
        self.label_lista = ctk.CTkLabel(self.sidebar_frame, text="MONITOREANDO", anchor="w",
                                        font=ctk.CTkFont(size=11, weight="bold"), text_color="#777777")
        self.label_lista.grid(row=4, column=0, padx=25, pady=(25,5), sticky="ew")

        self.scroll_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="", fg_color="white")
        self.scroll_frame.grid(row=5, column=0, padx=20, pady=5, sticky="nsew")
        
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 
        self.sidebar_frame.grid_rowconfigure(7, weight=0) 

        #Sección:Acciones
        self.frame_acciones = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.frame_acciones.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_pdf = ctk.CTkButton(
            self.frame_acciones, 
            text="📄 Generar Reporte PDF", 
            command=self.exportar_pdf, 
            state="disabled",
            fg_color="#4B5563",
            hover_color="#374151"
        )
        self.btn_pdf.pack(fill="x", pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.frame_acciones, 
            text="🗑 Eliminar Objetivo", 
            command=self.eliminar_objetivo, 
            fg_color="#EF4444", 
            hover_color="#DC2626",
            state="disabled"
        )
        self.btn_eliminar.pack(fill="x", pady=5)

        #Botón Ayuda
        self.btn_ayuda = ctk.CTkButton(
            self.sidebar_frame,
            text="Ayuda",
            command=self.abrir_ayuda,
            fg_color="transparent",
            border_width=1,
            border_color="#A1A1AA",
            text_color="#52525B",
            hover_color="#E4E4E7"
        )
        self.btn_ayuda.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")


        #Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="white") 
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=40)
        self.top_bar.pack(side="top", fill="x", padx=30, pady=(20, 0))
        
        self.lbl_titulo_grafica = ctk.CTkLabel(
            self.top_bar, 
            text="Visualización de Métricas", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#333333"
        )
        self.lbl_titulo_grafica.pack(side="left")

        self.filtro_tiempo = ctk.CTkComboBox(
            self.top_bar,
            values=["Tiempo Real", "Último Minuto", "Últimos 10 Minutos", "Última Hora", "Historial Completo"],
            width=200,
            command=self.cambiar_filtro,
            state="readonly"
        )
        self.filtro_tiempo.set("Tiempo Real")
        self.filtro_tiempo.pack(side="right")
        
        self.cargar_lista_objetivos()

    def abrir_ayuda(self):
        if self.ventana_ayuda is None or not self.ventana_ayuda.winfo_exists():
            self.ventana_ayuda = VentanaAyuda(self)
            self.ventana_ayuda.focus()
        else:
            self.ventana_ayuda.focus()

    def inicializar_graficos(self):
        self.fig = Figure(figsize=(5, 6), dpi=100)
        self.fig.patch.set_facecolor('white') 

        color_latencia = '#0EA5E9' 
        color_jitter = '#F59E0B'   
        color_perdida = '#EF4444'  

        def configurar_eje(ax, titulo, color_linea):
            ax.set_facecolor('white')
            ax.set_title(titulo, color="#333333", fontsize=10, weight='bold')
            ax.tick_params(axis='x', colors='#666666', labelsize=8)
            ax.tick_params(axis='y', colors='#666666', labelsize=8)
            ax.grid(True, color='#E5E7EB', linestyle='-', linewidth=0.5)
            for spine in ax.spines.values():
                spine.set_edgecolor('#E5E7EB')
            
            linea, = ax.plot([], [], color=color_linea, linewidth=2)
            return linea

        self.ax_latencia = self.fig.add_subplot(311) 
        self.linea_latencia = configurar_eje(self.ax_latencia, "Latencia (ms)", color_latencia)
        
        self.ax_jitter = self.fig.add_subplot(312)
        self.linea_jitter = configurar_eje(self.ax_jitter, "Jitter (ms)", color_jitter)
        
        self.ax_perdida = self.fig.add_subplot(313)
        self.linea_perdida = configurar_eje(self.ax_perdida, "Pérdida de Paquetes (%)", color_perdida)
        
        self.fig.subplots_adjust(hspace=0.4, top=0.95, bottom=0.05, left=0.1, right=0.95)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=30, pady=30)    

    def seleccionar_objetivo(self, id_obj, hostname):
        self.id_seleccionado = id_obj
        self.hostname_seleccionado = hostname
        self.title(f"Analizando: {hostname}")
        
        self.btn_eliminar.configure(state="normal")
        self.btn_pdf.configure(state="normal")
        self.actualizar_graficos_bucle(reprogramar=False)

    def cargar_lista_objetivos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        lista_objetivos = self.db.obtener_objetivos()
        
        for objetivo in lista_objetivos:
            id_obj, ip, hostname = objetivo
            btn = ctk.CTkButton(
                self.scroll_frame, 
                text=f"{hostname}\n{ip}", 
                fg_color="#F3F4F6", 
                text_color="#1F2937", 
                hover_color="#E5E7EB", 
                height=50,
                anchor="w",
                font=ctk.CTkFont(size=12),
                command=lambda i=id_obj, h=hostname: self.seleccionar_objetivo(i, h)
            )
            btn.pack(pady=2, padx=5, fill="x")

    def cambiar_filtro(self, choice):
        self.actualizar_graficos_bucle(reprogramar=False)

    def actualizar_graficos_bucle(self, reprogramar=True):
        if self.id_seleccionado is not None:
            modo = self.filtro_tiempo.get()
            datos = []

            try:
                if modo == "Tiempo Real":
                    datos = self.db.obtener_historial(self.id_seleccionado, limite=30)
                elif modo == "Último Minuto":
                    datos = self.db.obtener_historial_por_tiempo(self.id_seleccionado, minutos=1)
                elif modo == "Últimos 10 Minutos":
                    datos = self.db.obtener_historial_por_tiempo(self.id_seleccionado, minutos=10)
                elif modo == "Última Hora":
                    datos = self.db.obtener_historial_por_tiempo(self.id_seleccionado, minutos=60)
                elif modo == "Historial Completo":
                    datos = self.db.obtener_historial_por_tiempo(self.id_seleccionado, minutos=0)
            except Exception as e:
                print(f"Error recuperando datos: {e}")

            if datos:
                latencias = [d[0] for d in datos]
                jitters = [d[1] for d in datos]
                perdidas = [d[2] for d in datos]
                eje_x = range(len(datos))

                self.linea_latencia.set_data(eje_x, latencias)
                self.linea_jitter.set_data(eje_x, jitters)
                self.linea_perdida.set_data(eje_x, perdidas)
                
                self.ax_latencia.relim()
                self.ax_latencia.autoscale_view()
                self.ax_jitter.relim()
                self.ax_jitter.autoscale_view()
                
                self.ax_perdida.set_ylim(-1, 101) 
                self.ax_perdida.set_xlim(0, max(len(datos)-1, 1))

                self.canvas.draw_idle() 
            else:
                self.linea_latencia.set_data([], [])
                self.linea_jitter.set_data([], [])
                self.linea_perdida.set_data([], [])
                self.canvas.draw_idle()

        if reprogramar:
            self.after(1000, self.actualizar_graficos_bucle)        

    def agregar_objetivo(self):
        hostname_raw = self.entry_hostname.get().strip()
        if not hostname_raw: return

        try:
            hostname_limpio = hostname_raw.replace("https://", "").replace("http://", "").split("/")[0]
            ip_hostname = socket.gethostbyname(hostname_limpio)
            
            self.db.agregar_objetivo(ip_hostname, hostname_limpio)
            self.cargar_lista_objetivos()
            self.entry_hostname.delete(0, "end")
            messagebox.showinfo("Éxito", f"Agregado {hostname_limpio}")
            
        except socket.gaierror:
             messagebox.showerror("Error", "No se pudo resolver el nombre.")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

    def eliminar_objetivo(self):
        if self.id_seleccionado is None: return
        
        if messagebox.askyesno("Eliminar", f"¿Eliminar {self.hostname_seleccionado}?"):
            if self.db.eliminar_objetivo(self.id_seleccionado):
                self.id_seleccionado = None
                self.hostname_seleccionado = ""
                self.btn_eliminar.configure(state="disabled")
                self.btn_pdf.configure(state="disabled")
                
                self.linea_latencia.set_data([], [])
                self.linea_jitter.set_data([], [])
                self.linea_perdida.set_data([], [])
                self.canvas.draw_idle()
                
                self.cargar_lista_objetivos()

    def exportar_pdf(self):
        if self.id_seleccionado is None: return
        datos = self.db.obtener_historial(self.id_seleccionado, limite=100)
        
        if not datos:
            messagebox.showwarning("Aviso", "Sin datos suficientes.")
            return
        try:
            nombre = generar_reporte(self.hostname_seleccionado, datos)
            messagebox.showinfo("PDF Listo", f"Reporte guardado:\n{nombre}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def iniciar_monitoreo(self):
        hilo = threading.Thread(target=self.ciclo_monitoreo)
        hilo.daemon = True
        hilo.start()

    def ciclo_monitoreo(self):
        while self.monitoreo_activo:
            objetivos = self.db.obtener_objetivos()
            if not objetivos:
                time.sleep(2)
                continue
            for objetivo in objetivos:
                if not self.monitoreo_activo: break
                try:
                    l, j, p, f = self.monitor.obtener_metricas(objetivo[1])
                    self.db.guardar_resultado(objetivo[0], l, j, p, f)
                except: pass
            time.sleep(5) 
            
    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Detener monitoreo y salir?"):
            self.monitoreo_activo = False
            self.destroy()

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()