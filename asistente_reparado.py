import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import datetime
import random
import webbrowser
import threading
import math
import time
import sys
import os

# Importaciones opcionales para funciones de voz
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("⚠️  speech_recognition no está instalado. Funciones de voz deshabilitadas.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  pyttsx3 no está instalado. Síntesis de voz deshabilitada.")

class AsistenteVirtual:
    def __init__(self, nombre="Jarvis"):
        self.nombre = nombre
        self.activo = True
        
        # Inicializar componentes de voz solo si están disponibles
        if SPEECH_AVAILABLE:
            try:
                self.reconocedor = sr.Recognizer()
                self.microfono = sr.Microphone()
                print("✅ Reconocimiento de voz inicializado")
            except Exception as e:
                print(f"❌ Error inicializando micrófono: {e}")
                self.reconocedor = None
                self.microfono = None
        else:
            self.reconocedor = None
            self.microfono = None
        
        if TTS_AVAILABLE:
            try:
                self.motor_voz = pyttsx3.init()
                self.configurar_voz()
                print("✅ Síntesis de voz inicializada")
            except Exception as e:
                print(f"❌ Error inicializando síntesis de voz: {e}")
                self.motor_voz = None
        else:
            self.motor_voz = None

    def configurar_voz(self):
        if not self.motor_voz:
            return
        try:
            voces = self.motor_voz.getProperty('voices')
            if voces:
                # Buscar voz en español o usar la primera disponible
                for voz in voces:
                    if any(lang in voz.id.lower() for lang in ['spanish', 'es', 'spa']):
                        self.motor_voz.setProperty('voice', voz.id)
                        break
                else:
                    # Si no encuentra español, usar la primera voz
                    self.motor_voz.setProperty('voice', voces[0].id)
            
            self.motor_voz.setProperty('rate', 150)
            self.motor_voz.setProperty('volume', 0.8)
        except Exception as e:
            print(f"Error configurando voz: {e}")

    def hablar(self, texto):
        print(f"{self.nombre}: {texto}")
        if self.motor_voz:
            try:
                self.motor_voz.say(texto)
                self.motor_voz.runAndWait()
            except Exception as e:
                print(f"Error al hablar: {e}")

    def escuchar(self):
        if not self.reconocedor or not self.microfono:
            return "Reconocimiento de voz no disponible"
        
        try:
            with self.microfono as fuente:
                print("🎤 Ajustando ruido ambiente...")
                self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
                print("🎤 Escuchando...")
                audio = self.reconocedor.listen(fuente, timeout=5, phrase_time_limit=5)
                
            print("🔄 Procesando audio...")
            texto = self.reconocedor.recognize_google(audio, language="es-ES").lower()
            print(f"✅ Reconocido: {texto}")
            return texto
            
        except sr.WaitTimeoutError:
            return "⏰ Tiempo de espera agotado"
        except sr.UnknownValueError:
            return "❌ No pude entender lo que dijiste"
        except sr.RequestError as e:
            return f"❌ Error de conexión: {str(e)}"
        except Exception as e:
            return f"❌ Error inesperado: {str(e)}"

    def procesar_comando(self, comando):
        """Procesa los comandos del usuario"""
        comando = comando.lower().strip()
        
        # Comandos de saludo
        if any(saludo in comando for saludo in ["hola", "buenos días", "buenas tardes", "buenas noches", "hey"]):
            respuestas = [
                "¡Hola! ¿En qué puedo ayudarte hoy?",
                "¡Saludos! Estoy aquí para asistirte.",
                "¡Hola! ¿Qué necesitas que haga por ti?",
                "¡Buenos días! ¿Cómo puedo ser útil?"
            ]
            return random.choice(respuestas)
        
        # Consultas de tiempo
        elif any(palabra in comando for palabra in ["hora", "tiempo", "qué hora"]):
            hora_actual = datetime.datetime.now().strftime("%H:%M")
            return f"🕐 Son las {hora_actual}"
        
        # Consultas de fecha
        elif any(palabra in comando for palabra in ["fecha", "día", "qué día", "calendario"]):
            fecha_actual = datetime.datetime.now()
            dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            
            dia_semana = dias_semana[fecha_actual.weekday()]
            mes = meses[fecha_actual.month - 1]
            
            return f"📅 Hoy es {dia_semana}, {fecha_actual.day} de {mes} de {fecha_actual.year}"
        
        # Abrir navegador
        elif any(palabra in comando for palabra in ["abre navegador", "abrir navegador", "internet", "web"]):
            try:
                webbrowser.open("https://www.google.com")
                return "🌐 Abriendo el navegador web"
            except Exception as e:
                return f"❌ Error abriendo navegador: {str(e)}"
        
        # Búsquedas
        elif any(palabra in comando for palabra in ["busca", "buscar", "search"]):
            # Extraer término de búsqueda
            terminos_busqueda = ["busca", "buscar", "search"]
            termino = comando
            for termino_busqueda in terminos_busqueda:
                termino = termino.replace(termino_busquida, "").strip()
            
            if termino:
                try:
                    url = f"https://www.google.com/search?q={termino.replace(' ', '+')}"
                    webbrowser.open(url)
                    return f"🔍 Buscando información sobre: {termino}"
                except Exception as e:
                    return f"❌ Error realizando búsqueda: {str(e)}"
            else:
                return "❓ ¿Qué quieres que busque?"
        
        # YouTube
        elif "youtube" in comando:
            try:
                webbrowser.open("https://www.youtube.com")
                return "📺 Abriendo YouTube"
            except Exception as e:
                return f"❌ Error abriendo YouTube: {str(e)}"
        
        # Clima (abre página de clima)
        elif any(palabra in comando for palabra in ["clima", "tiempo", "temperatura"]):
            try:
                webbrowser.open("https://weather.com")
                return "🌤️ Abriendo información del clima"
            except Exception as e:
                return f"❌ Error abriendo clima: {str(e)}"
        
        # Despedidas
        elif any(palabra in comando for palabra in ["adiós", "hasta luego", "bye", "chao", "nos vemos"]):
            respuestas = [
                "¡Hasta luego! Que tengas un excelente día.",
                "¡Adiós! Estaré aquí cuando me necesites.",
                "¡Nos vemos! Cuídate mucho.",
                "¡Hasta la próxima! Que todo te vaya bien."
            ]
            return random.choice(respuestas)
        
        # Agradecimientos
        elif any(palabra in comando for palabra in ["gracias", "grazie", "thanks"]):
            respuestas = [
                "¡De nada! Estoy aquí para ayudarte.",
                "¡Un placer ayudarte!",
                "¡Para eso estoy! ¿Necesitas algo más?",
                "¡Siempre a tu servicio!"
            ]
            return random.choice(respuestas)
        
        # Estado del asistente
        elif any(palabra in comando for palabra in ["cómo estás", "como estas", "qué tal"]):
            respuestas = [
                "¡Estoy funcionando perfectamente! ¿Y tú qué tal?",
                "¡Muy bien, gracias por preguntar! ¿Cómo puedo ayudarte?",
                "¡Excelente! Listo para cualquier tarea.",
                "¡De maravilla! ¿En qué puedo ser útil?"
            ]
            return random.choice(respuestas)
        
        # Ayuda
        elif any(palabra in comando for palabra in ["ayuda", "help", "qué puedes hacer", "comandos"]):
            return """🤖 Puedo ayudarte con:
• Decirte la hora y fecha
• Abrir el navegador web
• Buscar información en Google
• Abrir YouTube
• Mostrar información del clima
• Mantener conversaciones básicas
            
¡Solo pregúntame lo que necesites!"""
        
        # Respuesta por defecto
        else:
            respuestas_default = [
                "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes ser más específico?",
                "❓ No entendí completamente. Puedes pedirme la hora, abrir el navegador, o buscar algo.",
                "🤷 Disculpa, no reconozco ese comando. Escribe 'ayuda' para ver qué puedo hacer.",
                "💭 Hmm, no sé cómo responder a eso. ¿Podrías reformular tu pregunta?"
            ]
            return random.choice(respuestas_default)

class InterfazAsistente(tk.Tk):
    def __init__(self, asistente):
        super().__init__()
        self.asistente = asistente
        self.title("🤖 Asistente Virtual Jarvis")
        self.geometry("900x700")
        self.configure(bg="#0f1923")
        self.resizable(True, True)
        
        # Variables de estado
        self.hablando = False
        self.escuchando = False
        self.amplitud = 5
        self.animacion_activa = True
        self.tiempo_animacion = 0
        
        # Configurar el icono de la ventana (opcional)
        try:
            self.iconbitmap("")  # Puedes agregar un archivo .ico aquí
        except:
            pass
        
        self.crear_widgets()
        self.after(1000, self.saludo_inicial)

    def crear_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self, bg="#0f1923")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título con emoji
        titulo = tk.Label(
            main_frame, 
            text=f"🤖 {self.asistente.nombre} - Asistente Virtual", 
            font=("Arial", 20, "bold"), 
            fg="#00bfff", 
            bg="#0f1923"
        )
        titulo.pack(pady=10)
        
        # Canvas para animación
        canvas_frame = tk.Frame(main_frame, bg="#0f1923")
        canvas_frame.pack(fill=tk.X, pady=10)
        
        self.canvas = tk.Canvas(
            canvas_frame, 
            height=150, 
            bg="#0f1923", 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X)
        
        # Frame para entrada de texto
        entrada_frame = tk.Frame(main_frame, bg="#0f1923")
        entrada_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            entrada_frame, 
            text="💬 Escribe tu mensaje:", 
            font=("Arial", 10, "bold"), 
            fg="#00bfff", 
            bg="#0f1923"
        ).pack(anchor=tk.W)
        
        # Frame para entrada y botón
        input_frame = tk.Frame(entrada_frame, bg="#0f1923")
        input_frame.pack(fill=tk.X, pady=5)
        
        self.entrada_texto = tk.Entry(
            input_frame,
            font=("Arial", 12),
            bg="#1a2634",
            fg="#ffffff",
            insertbackground="#00bfff",
            relief=tk.FLAT,
            bd=5
        )
        self.entrada_texto.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entrada_texto.bind("<Return>", self.procesar_texto)
        
        tk.Button(
            input_frame,
            text="📤 Enviar",
            command=self.procesar_texto,
            font=("Arial", 10, "bold"),
            bg="#00364e",
            fg="#ffffff",
            activebackground="#005577",
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.RIGHT)
        
        # Área de historial
        historial_frame = tk.Frame(main_frame, bg="#0f1923")
        historial_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(
            historial_frame, 
            text="📜 Historial de Conversación:", 
            font=("Arial", 12, "bold"), 
            fg="#00bfff", 
            bg="#0f1923"
        ).pack(anchor=tk.W)
        
        self.historial = scrolledtext.ScrolledText(
            historial_frame,
            font=("Consolas", 10),
            bg="#1a2634",
            fg="#ffffff",
            insertbackground="#00bfff",
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=5
        )
        self.historial.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Frame de controles
        controles_frame = tk.Frame(main_frame, bg="#0f1923")
        controles_frame.pack(fill=tk.X, pady=10)
        
        # Estado del asistente
        self.estado_var = tk.StringVar(value="✅ Listo para conversar")
        estado_label = tk.Label(
            controles_frame,
            textvariable=self.estado_var,
            font=("Arial", 10),
            fg="#00ff00",
            bg="#0f1923"
        )
        estado_label.pack(side=tk.LEFT)
        
        # Botones de control
        if SPEECH_AVAILABLE and self.asistente.reconocedor:
            self.boton_escuchar = tk.Button(
                controles_frame,
                text="🎤 Escuchar",
                command=self.iniciar_escucha,
                font=("Arial", 10, "bold"),
                bg="#00364e",
                fg="#ffffff",
                activebackground="#005577",
                relief=tk.RAISED,
                bd=2,
                padx=15
            )
            self.boton_escuchar.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            controles_frame,
            text="🗑️ Limpiar",
            command=self.limpiar_historial,
            font=("Arial", 10, "bold"),
            bg="#4a4a4a",
            fg="#ffffff",
            activebackground="#666666",
            relief=tk.RAISED,
            bd=2,
            padx=15
        ).pack(side=tk.RIGHT, padx=5)
        
        # Iniciar animación
        self.after(100, self.iniciar_animacion)

    def iniciar_animacion(self):
        if not self.animacion_activa:
            return
            
        try:
            self.canvas.delete("all")
            ancho = self.canvas.winfo_width()
            alto = self.canvas.winfo_height()
            
            if ancho <= 1 or alto <= 1:
                self.after(100, self.iniciar_animacion)
                return
            
            centro_x = ancho // 2
            centro_y = alto // 2
            
            # Círculo principal animado
            radio_base = 30
            pulso = math.sin(self.tiempo_animacion * 2) * 5
            radio = radio_base + pulso
            
            # Color que cambia según el estado
            if self.hablando:
                color = "#ff6b6b"  # Rojo cuando habla
            elif self.escuchando:
                color = "#4ecdc4"  # Verde cuando escucha
            else:
                color = "#00bfff"  # Azul normal
            
            # Círculo principal
            self.canvas.create_oval(
                centro_x - radio, centro_y - radio,
                centro_x + radio, centro_y + radio,
                outline=color, width=3
            )
            
            # Círculos concéntricos
            for i in range(1, 4):
                radio_ext = radio + (i * 10)
                intensidad = max(0.1, 1 - (i * 0.3))
                self.canvas.create_oval(
                    centro_x - radio_ext, centro_y - radio_ext,
                    centro_x + radio_ext, centro_y + radio_ext,
                    outline=color, width=max(1, int(3 * intensidad))
                )
            
            # Ondas cuando está activo
            if self.hablando or self.escuchando:
                for i in range(3):
                    onda_radio = radio + 40 + (i * 20) + (self.tiempo_animacion * 10) % 60
                    if onda_radio < ancho // 2:
                        self.canvas.create_oval(
                            centro_x - onda_radio, centro_y - onda_radio,
                            centro_x + onda_radio, centro_y + onda_radio,
                            outline=color, width=1
                        )
            
            self.tiempo_animacion += 0.1
            
        except Exception as e:
            print(f"Error en animación: {e}")
        
        self.after(50, self.iniciar_animacion)

    def agregar_al_historial(self, mensaje, tipo="info"):
        """Agrega un mensaje al historial"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Colores según el tipo de mensaje
        if tipo == "usuario":
            prefijo = "👤"
        elif tipo == "asistente":
            prefijo = "🤖"
        elif tipo == "error":
            prefijo = "❌"
        else:
            prefijo = "ℹ️"
        
        mensaje_completo = f"[{timestamp}] {prefijo} {mensaje}\n"
        self.historial.insert(tk.END, mensaje_completo)
        self.historial.see(tk.END)
        self.update()

    def saludo_inicial(self):
        """Saludo inicial del asistente"""
        mensaje = f"¡Hola! Soy {self.asistente.nombre}, tu asistente virtual. ¿En qué puedo ayudarte hoy?"
        self.agregar_al_historial(mensaje, "asistente")
        
        # Hablar solo si TTS está disponible
        if TTS_AVAILABLE and self.asistente.motor_voz:
            threading.Thread(target=lambda: self.asistente.hablar(mensaje), daemon=True).start()

    def procesar_texto(self, event=None):
        """Procesa el texto ingresado manualmente"""
        texto = self.entrada_texto.get().strip()
        if not texto:
            return
        
        self.entrada_texto.delete(0, tk.END)
        self.agregar_al_historial(texto, "usuario")
        
        # Procesar comando
        respuesta = self.asistente.procesar_comando(texto)
        self.agregar_al_historial(respuesta, "asistente")
        
        # Hablar respuesta si está disponible
        if TTS_AVAILABLE and self.asistente.motor_voz:
            self.hablando = True
            threading.Thread(target=self.hablar_respuesta, args=(respuesta,), daemon=True).start()

    def hablar_respuesta(self, respuesta):
        """Habla la respuesta en un hilo separado"""
        try:
            self.asistente.hablar(respuesta)
        finally:
            self.hablando = False

    def iniciar_escucha(self):
        """Inicia el proceso de escucha por voz"""
        if self.escuchando or not hasattr(self, 'boton_escuchar'):
            return
        
        self.escuchando = True
        self.boton_escuchar.config(state=tk.DISABLED, text="🎤 Escuchando...")
        self.estado_var.set("🎤 Escuchando... Habla ahora")
        threading.Thread(target=self.procesar_voz, daemon=True).start()

    def procesar_voz(self):
        """Procesa el comando de voz"""
        try:
            comando = self.asistente.escuchar()
            
            # Actualizar desde el hilo principal
            self.after(0, lambda: self.agregar_al_historial(comando, "usuario"))
            
            if not any(error in comando for error in ["❌", "⏰", "Tiempo de espera"]):
                respuesta = self.asistente.procesar_comando(comando)
                self.after(0, lambda: self.agregar_al_historial(respuesta, "asistente"))
                
                # Hablar respuesta
                if TTS_AVAILABLE and self.asistente.motor_voz:
                    self.hablando = True
                    self.asistente.hablar(respuesta)
                    self.hablando = False
            
        except Exception as e:
            error_msg = f"Error procesando voz: {str(e)}"
            self.after(0, lambda: self.agregar_al_historial(error_msg, "error"))
        
        finally:
            self.after(0, self.restaurar_estado_voz)

    def restaurar_estado_voz(self):
        """Restaura el estado después de escuchar"""
        self.escuchando = False
        self.estado_var.set("✅ Listo para conversar")
        if hasattr(self, 'boton_escuchar'):
            self.boton_escuchar.config(state=tk.NORMAL, text="🎤 Escuchar")

    def limpiar_historial(self):
        """Limpia el historial de conversación"""
        self.historial.delete(1.0, tk.END)
        self.agregar_al_historial("Historial limpiado", "info")

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.animacion_activa = False
        try:
            if self.asistente.motor_voz:
                self.asistente.motor_voz.stop()
        except:
            pass
        self.destroy()

def main():
    """Función principal"""
    print("🚀 Iniciando Asistente Virtual...")
    
    # Verificar dependencias
    dependencias_faltantes = []
    if not SPEECH_AVAILABLE:
        dependencias_faltantes.append("speech_recognition")
    if not TTS_AVAILABLE:
        dependencias_faltantes.append("pyttsx3")
    
    if dependencias_faltantes:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        print("Para instalar: pip install " + " ".join(dependencias_faltantes))
        print("La aplicación funcionará en modo texto.\n")
    
    try:
        asistente = AsistenteVirtual("Jarvis")
        app = InterfazAsistente(asistente)
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("✅ Interfaz iniciada correctamente")
        print("💡 Puedes escribir comandos o usar el botón de micrófono (si está disponible)")
        
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        messagebox.showerror("Error", f"Error iniciando la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()
