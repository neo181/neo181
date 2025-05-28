import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import datetime
import random
import webbrowser
import threading
import math
import time
import json
import os
import requests
from typing import List, Dict

# Importaciones opcionales para funciones de voz
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class ConectorIA:
    """Clase para manejar conexiones con diferentes APIs de IA"""
    
    def __init__(self):
        self.api_keys = self.cargar_api_keys()
        self.historial_conversacion = []
        self.max_historial = 10  # Mantener últimas 10 interacciones
    
    def cargar_api_keys(self):
        """Carga las API keys desde un archivo JSON"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    return json.load(f)
            else:
                return {}
        except:
            return {}
    
    def guardar_api_keys(self, keys):
        """Guarda las API keys en un archivo JSON"""
        try:
            with open("config.json", "w") as f:
                json.dump(keys, f, indent=2)
            self.api_keys = keys
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def configurar_api_key(self, servicio, api_key):
        """Configura una API key para un servicio específico"""
        if servicio not in self.api_keys:
            self.api_keys[servicio] = {}
        self.api_keys[servicio]["key"] = api_key
        self.guardar_api_keys(self.api_keys)
    
    def obtener_respuesta_openai(self, mensaje):
        """Obtiene respuesta de OpenAI GPT"""
        if "openai" not in self.api_keys or "key" not in self.api_keys["openai"]:
            return "❌ API key de OpenAI no configurada. Usa 'configurar openai' para establecerla."
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']['key']}",
                "Content-Type": "application/json"
            }
            
            # Preparar mensajes con historial
            mensajes = []
            for interaccion in self.historial_conversacion[-5:]:  # Últimas 5 interacciones
                mensajes.append({"role": "user", "content": interaccion["pregunta"]})
                mensajes.append({"role": "assistant", "content": interaccion["respuesta"]})
            
            mensajes.append({"role": "user", "content": mensaje})
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": mensajes,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                respuesta = result["choices"][0]["message"]["content"]
                self.agregar_al_historial(mensaje, respuesta)
                return respuesta
            else:
                return f"❌ Error de OpenAI: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "⏰ Tiempo de espera agotado. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error conectando con OpenAI: {str(e)}"
    
    def obtener_respuesta_gemini(self, mensaje):
        """Obtiene respuesta de Google Gemini"""
        if "gemini" not in self.api_keys or "key" not in self.api_keys["gemini"]:
            return "❌ API key de Gemini no configurada. Usa 'configurar gemini' para establecerla."
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_keys['gemini']['key']}"
            
            # Preparar contexto con historial
            contexto = ""
            for interaccion in self.historial_conversacion[-3:]:
                contexto += f"Usuario: {interaccion['pregunta']}\nAsistente: {interaccion['respuesta']}\n\n"
            
            prompt_completo = contexto + f"Usuario: {mensaje}\nAsistente:"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt_completo
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500
                }
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    respuesta = result["candidates"][0]["content"]["parts"][0]["text"]
                    self.agregar_al_historial(mensaje, respuesta)
                    return respuesta
                else:
                    return "❌ No se recibió respuesta válida de Gemini"
            else:
                return f"❌ Error de Gemini: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "⏰ Tiempo de espera agotado. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error conectando con Gemini: {str(e)}"
    
    def obtener_respuesta_huggingface(self, mensaje):
        """Obtiene respuesta de Hugging Face (modelo gratuito)"""
        try:
            # Usar modelo gratuito de Hugging Face
            url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            
            headers = {}
            if "huggingface" in self.api_keys and "key" in self.api_keys["huggingface"]:
                headers["Authorization"] = f"Bearer {self.api_keys['huggingface']['key']}"
            
            data = {"inputs": mensaje}
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    respuesta = result[0].get("generated_text", "").replace(mensaje, "").strip()
                    if respuesta:
                        self.agregar_al_historial(mensaje, respuesta)
                        return respuesta
                    else:
                        return "🤔 No pude generar una respuesta adecuada."
                else:
                    return "❌ Respuesta inesperada del modelo"
            else:
                return f"❌ Error de Hugging Face: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "⏰ Tiempo de espera agotado. Intenta de nuevo."
        except Exception as e:
            return f"❌ Error conectando con Hugging Face: {str(e)}"
    
    def agregar_al_historial(self, pregunta, respuesta):
        """Agrega una interacción al historial"""
        self.historial_conversacion.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "pregunta": pregunta,
            "respuesta": respuesta
        })
        
        # Mantener solo las últimas interacciones
        if len(self.historial_conversacion) > self.max_historial:
            self.historial_conversacion = self.historial_conversacion[-self.max_historial:]
    
    def obtener_respuesta_ia(self, mensaje, servicio="auto"):
        """Método principal para obtener respuesta de IA"""
        if servicio == "auto":
            # Detectar automáticamente qué servicio usar
            if "openai" in self.api_keys and "key" in self.api_keys["openai"]:
                return self.obtener_respuesta_openai(mensaje)
            elif "gemini" in self.api_keys and "key" in self.api_keys["gemini"]:
                return self.obtener_respuesta_gemini(mensaje)
            else:
                return self.obtener_respuesta_huggingface(mensaje)
        elif servicio == "openai":
            return self.obtener_respuesta_openai(mensaje)
        elif servicio == "gemini":
            return self.obtener_respuesta_gemini(mensaje)
        elif servicio == "huggingface":
            return self.obtener_respuesta_huggingface(mensaje)
        else:
            return "❌ Servicio de IA no reconocido"

class AsistenteVirtualIA:
    def __init__(self, nombre="Jarvis"):
        self.nombre = nombre
        self.activo = True
        self.conector_ia = ConectorIA()
        
        # Inicializar componentes de voz
        if SPEECH_AVAILABLE:
            try:
                self.reconocedor = sr.Recognizer()
                self.microfono = sr.Microphone()
            except:
                self.reconocedor = None
                self.microfono = None
        else:
            self.reconocedor = None
            self.microfono = None
        
        if TTS_AVAILABLE:
            try:
                self.motor_voz = pyttsx3.init()
                self.configurar_voz()
            except:
                self.motor_voz = None
        else:
            self.motor_voz = None

    def configurar_voz(self):
        if not self.motor_voz:
            return
        try:
            voces = self.motor_voz.getProperty('voices')
            if voces:
                for voz in voces:
                    if any(lang in voz.id.lower() for lang in ['spanish', 'es', 'spa']):
                        self.motor_voz.setProperty('voice', voz.id)
                        break
                else:
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
                self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
                audio = self.reconocedor.listen(fuente, timeout=5, phrase_time_limit=5)
                
            texto = self.reconocedor.recognize_google(audio, language="es-ES").lower()
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
        """Procesa comandos locales y de IA"""
        comando_original = comando
        comando = comando.lower().strip()
        
        # Comandos de configuración
        if comando.startswith("configurar"):
            partes = comando.split()
            if len(partes) >= 2:
                servicio = partes[1]
                return f"🔑 Para configurar {servicio}, necesito que proporciones la API key a través del botón 'Configurar IA'"
            else:
                return "💡 Uso: 'configurar [openai|gemini|huggingface]'"
        
        # Comandos básicos del sistema
        elif any(saludo in comando for saludo in ["hola", "buenos días", "buenas tardes", "hey"]):
            return "¡Hola! Soy tu asistente con IA integrada. Puedo responder cualquier pregunta. ¿En qué puedo ayudarte?"
        
        elif any(palabra in comando for palabra in ["hora", "qué hora"]):
            return f"🕐 Son las {datetime.datetime.now().strftime('%H:%M')}"
        
        elif any(palabra in comando for palabra in ["fecha", "qué día"]):
            fecha = datetime.datetime.now()
            return f"📅 Hoy es {fecha.strftime('%A, %d de %B de %Y')}"
        
        elif "abrir navegador" in comando or "abre internet" in comando:
            webbrowser.open("https://www.google.com")
            return "🌐 Abriendo el navegador web"
        
        elif comando.startswith("buscar "):
            termino = comando.replace("buscar ", "")
            webbrowser.open(f"https://www.google.com/search?q={termino.replace(' ', '+')}")
            return f"🔍 Buscando: {termino}"
        
        elif any(palabra in comando for palabra in ["adiós", "hasta luego", "bye"]):
            return random.choice([
                "¡Hasta luego! Ha sido un placer conversar contigo.",
                "¡Adiós! Vuelve cuando necesites ayuda.",
                "¡Nos vemos! Que tengas un excelente día."
            ])
        
        elif "ayuda" in comando or "qué puedes hacer" in comando:
            return """🤖 Soy un asistente con IA avanzada. Puedo:

📋 **Comandos básicos:**
• Decir la hora y fecha
• Abrir navegador web
• Realizar búsquedas

🧠 **IA Conversacional:**
• Responder cualquier pregunta
• Mantener conversaciones naturales
• Ayudar con tareas complejas
• Aprender del contexto de nuestra conversación

⚙️ **Configuración:**
• 'configurar openai/gemini' - Para usar IA premium
• Sin configuración uso IA gratuita

¡Pregúntame lo que quieras!"""
        
        # Para todo lo demás, usar IA
        else:
            return self.conector_ia.obtener_respuesta_ia(comando_original)

class InterfazAsistenteIA(tk.Tk):
    def __init__(self, asistente):
        super().__init__()
        self.asistente = asistente
        self.title("🧠 Asistente Virtual con IA")
        self.geometry("1000x800")
        self.configure(bg="#0f1923")
        self.resizable(True, True)
        
        # Variables de estado
        self.hablando = False
        self.escuchando = False
        self.pensando = False
        self.animacion_activa = True
        self.tiempo_animacion = 0
        
        self.crear_widgets()
        self.after(1000, self.saludo_inicial)

    def crear_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self, bg="#0f1923")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        titulo = tk.Label(
            main_frame, 
            text="🧠 Jarvis AI - Asistente Inteligente", 
            font=("Arial", 20, "bold"), 
            fg="#00bfff", 
            bg="#0f1923"
        )
        titulo.pack(pady=10)
        
        # Canvas para animación
        self.canvas = tk.Canvas(
            main_frame, 
            height=120, 
            bg="#0f1923", 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, pady=10)
        
        # Frame de configuración
        config_frame = tk.Frame(main_frame, bg="#0f1923")
        config_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(
            config_frame,
            text="⚙️ Configurar IA",
            command=self.configurar_ia,
            font=("Arial", 9, "bold"),
            bg="#4a4a4a",
            fg="#ffffff",
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.LEFT, padx=5)
        
        # Indicador de estado de IA
        self.estado_ia_var = tk.StringVar()
        self.actualizar_estado_ia()
        tk.Label(
            config_frame,
            textvariable=self.estado_ia_var,
            font=("Arial", 9),
            fg="#00ff00",
            bg="#0f1923"
        ).pack(side=tk.LEFT, padx=10)
        
        # Frame de entrada
        entrada_frame = tk.Frame(main_frame, bg="#0f1923")
        entrada_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            entrada_frame, 
            text="💬 Pregúntame cualquier cosa:", 
            font=("Arial", 10, "bold"), 
            fg="#00bfff", 
            bg="#0f1923"
        ).pack(anchor=tk.W)
        
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
            text="🚀 Enviar",
            command=self.procesar_texto,
            font=("Arial", 10, "bold"),
            bg="#00364e",
            fg="#ffffff",
            activebackground="#005577",
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.RIGHT)
        
        # Historial
        historial_frame = tk.Frame(main_frame, bg="#0f1923")
        historial_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(
            historial_frame, 
            text="🗨️ Conversación:", 
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
        
        # Controles
        controles_frame = tk.Frame(main_frame, bg="#0f1923")
        controles_frame.pack(fill=tk.X, pady=10)
        
        self.estado_var = tk.StringVar(value="✅ Listo para conversar")
        tk.Label(
            controles_frame,
            textvariable=self.estado_var,
            font=("Arial", 10),
            fg="#00ff00",
            bg="#0f1923"
        ).pack(side=tk.LEFT)
        
        # Botones
        if SPEECH_AVAILABLE and self.asistente.reconocedor:
            self.boton_escuchar = tk.Button(
                controles_frame,
                text="🎤 Escuchar",
                command=self.iniciar_escucha,
                font=("Arial", 10, "bold"),
                bg="#00364e",
                fg="#ffffff",
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
            relief=tk.RAISED,
            bd=2,
            padx=15
        ).pack(side=tk.RIGHT, padx=5)
        
        self.after(100, self.iniciar_animacion)

    def actualizar_estado_ia(self):
        """Actualiza el indicador de estado de la IA"""
        keys = self.asistente.conector_ia.api_keys
        if "openai" in keys and "key" in keys["openai"]:
            self.estado_ia_var.set("🟢 OpenAI conectado")
        elif "gemini" in keys and "key" in keys["gemini"]:
            self.estado_ia_var.set("🟢 Gemini conectado")
        else:
            self.estado_ia_var.set("🟡 IA gratuita activa")

    def configurar_ia(self):
        """Ventana para configurar APIs de IA"""
        config_window = tk.Toplevel(self)
        config_window.title("⚙️ Configuración de IA")
        config_window.geometry("400x300")
        config_window.configure(bg="#0f1923")
        config_window.transient(self)
        config_window.grab_set()
        
        tk.Label(
            config_window,
            text="🔑 Configurar APIs de IA",
            font=("Arial", 14, "bold"),
            fg="#00bfff",
            bg="#0f1923"
        ).pack(pady=10)
        
        # OpenAI
        openai_frame = tk.LabelFrame(
            config_window,
            text="OpenAI (ChatGPT)",
            font=("Arial", 10, "bold"),
            fg="#ffffff",
            bg="#0f1923"
        )
        openai_frame.pack(fill=tk.X, padx=20, pady=10)
        
        openai_entry = tk.Entry(openai_frame, show="*", width=40)
        openai_entry.pack(pady=5)
        
        tk.Button(
            openai_frame,
            text="Configurar OpenAI",
            command=lambda: self.guardar_api_key("openai", openai_entry.get(), config_window),
            bg="#00364e",
            fg="#ffffff"
        ).pack(pady=5)
        
        # Gemini
        gemini_frame = tk.LabelFrame(
            config_window,
            text="Google Gemini",
            font=("Arial", 10, "bold"),
            fg="#ffffff",
            bg="#0f1923"
        )
        gemini_frame.pack(fill=tk.X, padx=20, pady=10)
        
        gemini_entry = tk.Entry(gemini_frame, show="*", width=40)
        gemini_entry.pack(pady=5)
        
        tk.Button(
            gemini_frame,
            text="Configurar Gemini",
            command=lambda: self.guardar_api_key("gemini", gemini_entry.get(), config_window),
            bg="#00364e",
            fg="#ffffff"
        ).pack(pady=5)
        
        # Información
        info_text = """
💡 Información:
• OpenAI: Obtén tu API key en platform.openai.com
• Gemini: Obtén tu API key en makersuite.google.com
• Sin configurar: Usará IA gratuita (limitada)
        """
        
        tk.Label(
            config_window,
            text=info_text,
            font=("Arial", 8),
            fg="#cccccc",
            bg="#0f1923",
            justify=tk.LEFT
        ).pack(pady=10)

    def guardar_api_key(self, servicio, api_key, ventana):
        """Guarda una API key"""
        if api_key.strip():
            self.asistente.conector_ia.configurar_api_key(servicio, api_key.strip())
            self.actualizar_estado_ia()
            messagebox.showinfo("✅ Éxito", f"API key de {servicio} configurada correctamente")
            ventana.destroy()
        else:
            messagebox.showerror("❌ Error", "Por favor ingresa una API key válida")

    def iniciar_animacion(self):
        """Animación del canvas"""
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
            
            # Color según estado
            if self.pensando:
                color = "#ff6b6b"  # Rojo cuando piensa
            elif self.hablando:
                color = "#ffa500"  # Naranja cuando habla
            elif self.escuchando:
                color = "#4ecdc4"  # Verde cuando escucha
            else:
                color = "#00bfff"  # Azul normal
            
            # Círculo principal con pulso
            radio = 25 + math.sin(self.tiempo_animacion * 3) * 5
            self.canvas.create_oval(
                centro_x - radio, centro_y - radio,
                centro_x + radio, centro_y + radio,
                outline=color, width=3
            )
            
            # Ondas cerebrales cuando piensa
            if self.pensando:
                for i in range(5):
                    onda_radio = radio + 10 + (i * 8) + (self.tiempo_animacion * 15) % 40
                    if onda_radio < ancho // 2:
                        intensidad = max(0.1, 1 - (i * 0.2))
                        self.canvas.create_oval(
                            centro_x - onda_radio, centro_y - onda_radio,
                            centro_x + onda_radio, centro_y + onda_radio,
                            outline=color, width=max(1, int(2 * intensidad))
                        )
            
            self.tiempo_animacion += 0.1
            
        except Exception as e:
            print(f"Error en animación: {e}")
        
        self.after(60, self.iniciar_animacion)

    def agregar_al_historial(self, mensaje, tipo="info"):
        """Agrega mensaje al historial"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if tipo == "usuario":
            prefijo = "👤"
        elif tipo == "asistente":
            prefijo = "🧠"
        elif tipo == "error":
            prefijo = "❌"
        else:
            prefijo = "ℹ️"
        
        self.historial.insert(tk.END, f"[{timestamp}] {prefijo} {mensaje}\n\n")
        self.historial.see(tk.END)
        self.update()

    def saludo_inicial(self):
        """Saludo inicial"""
        mensaje = "¡Hola! Soy Jarvis AI, tu asistente inteligente. Puedo responder cualquier pregunta y mantener conversaciones naturales. ¿En qué puedo ayudarte?"
        self.agregar_al_historial(mensaje, "asistente")
        
        if TTS_AVAILABLE and self.asistente.motor_voz:
            threading.Thread(target=lambda: self.asistente.hablar(mensaje), daemon=True).start()

    def procesar_texto(self, event=None):
        """Procesa texto ingresado"""
        texto = self.entrada_texto