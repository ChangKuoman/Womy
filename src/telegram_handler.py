"""
Handler para Telegram Bot
Configuración: Solo necesitas crear un bot con @BotFather en Telegram
"""
import requests
from typing import Dict, Optional, List
from config import settings


class TelegramHandler:
    """Clase para manejar la comunicación con Telegram"""

    def __init__(self):
        """Inicializa el handler de Telegram"""
        self.token = settings.telegram_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def enviar_mensaje(self, chat_id: str, mensaje: str) -> bool:
        """
        Envía un mensaje de texto

        Args:
            chat_id: ID del chat de Telegram
            mensaje: Texto del mensaje

        Returns:
            True si se envió correctamente
        """
        if not self.token:
            print("⚠️ Token de Telegram no configurado")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "HTML"  # Permite usar <b>, <i>, etc.
            }

            response = requests.post(url, json=data)

            if response.status_code == 200:
                print(f"✅ Mensaje enviado a {chat_id}")
                return True
            else:
                print(f"❌ Error al enviar mensaje: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")
            return False

    def enviar_audio(self, chat_id: str, audio_path: str) -> bool:
        """
        Envía un archivo de audio

        Args:
            chat_id: ID del chat de Telegram
            audio_path: Ruta del archivo de audio

        Returns:
            True si se envió correctamente
        """
        if not self.token:
            print("⚠️ Token de Telegram no configurado")
            return False

        try:
            url = f"{self.base_url}/sendVoice"

            with open(audio_path, 'rb') as audio_file:
                files = {'voice': audio_file}
                data = {'chat_id': chat_id}

                response = requests.post(url, data=data, files=files)

            if response.status_code == 200:
                print(f"✅ Audio enviado a {chat_id}")
                return True
            else:
                print(f"❌ Error al enviar audio: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error al enviar audio: {e}")
            return False

    def obtener_actualizaciones(self, offset: int = None) -> List[Dict]:
        """
        Obtiene mensajes nuevos (polling)

        Args:
            offset: ID del último mensaje procesado + 1

        Returns:
            Lista de actualizaciones
        """
        if not self.token:
            return []

        try:
            url = f"{self.base_url}/getUpdates"
            params = {"timeout": 30}

            if offset:
                params["offset"] = offset

            response = requests.get(url, params=params)

            if response.status_code == 200:
                return response.json().get('result', [])
            else:
                print(f"❌ Error al obtener actualizaciones: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error al obtener actualizaciones: {e}")
            return []

    def extraer_mensaje(self, update: Dict) -> Optional[Dict]:
        """
        Extrae información de un mensaje (texto o voz)

        Args:
            update: Actualización de Telegram

        Returns:
            Dict con información del mensaje o None
        """
        try:
            if 'message' not in update:
                return None

            mensaje = update['message']

            info = {
                'message_id': mensaje.get('message_id'),
                'chat_id': str(mensaje['chat']['id']),
                'user_id': str(mensaje['from']['id']),
                'username': mensaje['from'].get('username', 'Sin username'),
                'first_name': mensaje['from'].get('first_name', ''),
                'text': mensaje.get('text', ''),
                'timestamp': mensaje.get('date'),
                'tiene_voz': 'voice' in mensaje,
                'voice': mensaje.get('voice')  # Info del archivo de voz
            }

            return info

        except Exception as e:
            print(f"❌ Error al extraer mensaje: {e}")
            return None

    def descargar_audio(self, file_id: str) -> Optional[str]:
        """
        Descarga un archivo de audio de Telegram

        Args:
            file_id: ID del archivo de voz en Telegram

        Returns:
            Ruta del archivo descargado o None si hay error
        """
        if not self.token:
            print("⚠️ Token de Telegram no configurado")
            return None

        try:
            # Obtener información del archivo
            url_file_info = f"{self.base_url}/getFile"
            params = {"file_id": file_id}
            response = requests.get(url_file_info, params=params)

            if response.status_code != 200:
                print(f"❌ Error al obtener info del archivo: {response.status_code}")
                return None

            file_path = response.json().get('result', {}).get('file_path')
            if not file_path:
                print("❌ No se pudo obtener la ruta del archivo")
                return None

            # Descargar el archivo
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            audio_response = requests.get(download_url)

            if audio_response.status_code == 200:
                # Guardar temporalmente
                import tempfile
                import os

                # Crear directorio temporal si no existe
                temp_dir = "audio_received"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                output_path = os.path.join(temp_dir, f"voice_{file_id}.ogg")

                with open(output_path, 'wb') as f:
                    f.write(audio_response.content)

                print(f"✅ Audio descargado: {output_path}")
                return output_path
            else:
                print(f"❌ Error al descargar audio: {audio_response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error al descargar audio: {e}")
            return None

    def transcribir_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe un archivo de audio usando OpenAI Whisper API

        Args:
            audio_path: Ruta del archivo de audio

        Returns:
            Texto transcrito o None si hay error
        """
        from config import settings

        if not settings.openai_api_key:
            print("⚠️ OpenAI API Key no configurada")
            print("💡 Agrega OPENAI_API_KEY a tu archivo .env")
            return None

        try:
            url = "https://api.openai.com/v1/audio/transcriptions"

            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}"
            }

            with open(audio_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                }
                data = {
                    'model': 'whisper-1',
                    'language': 'es',  # Español por defecto
                    'response_format': 'text'
                }

                response = requests.post(url, headers=headers, files=files, data=data)

            if response.status_code == 200:
                texto = response.text.strip()
                print(f"✅ Audio transcrito: {texto[:100]}...")
                return texto
            else:
                print(f"❌ Error al transcribir: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error al transcribir audio: {e}")
            return None


# Instancia global
telegram_handler = TelegramHandler()
