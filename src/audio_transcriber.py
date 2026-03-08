"""
Transcripción de audio usando Fish Audio API
"""
import requests
import os
from typing import Optional
from groq import Groq
from config import settings


class TranscriptorAudio:
    """Clase para transcribir audio con Fish Audio o Groq Whisper"""

    def __init__(self):
        """Inicializa el transcriptor de audio"""
        self.fish_api_key = settings.fish_audio_api_key
        self.groq_api_key = settings.groq_api_key
        self.fish_base_url = "https://api.fish.audio/v1/asr"
        self.transcripcion_desactivada = False

        # Inicializar cliente de Groq
        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None

        # Crear directorio temporal para audios si no existe
        self.audio_dir = "audio_temp"
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    def transcribir_audio(self, audio_path: str, idioma: str = "es") -> Optional[str]:
        """
        Transcribe un archivo de audio a texto usando Fish Audio o Groq Whisper

        Args:
            audio_path: Ruta del archivo de audio
            idioma: Código del idioma (es, en, pt, fr)

        Returns:
            Texto transcrito o None si hay error
        """
        if self.transcripcion_desactivada:
            return None

        # Intentar primero con Groq (gratis)
        if self.groq_api_key:
            resultado = self._transcribir_con_groq(audio_path, idioma)
            if resultado:
                return resultado

        # Fallback a Fish Audio
        if self.fish_api_key:
            resultado = self._transcribir_con_fish(audio_path, idioma)
            if resultado:
                return resultado

        print("⚠️ No hay API keys configuradas para transcripción")
        print("💡 Configura GROQ_API_KEY (gratis) en .env")
        return None

    def _transcribir_con_groq(self, audio_path: str, idioma: str) -> Optional[str]:
        """Transcribe usando Groq Whisper (gratis)"""
        if not self.groq_client:
            return None

        try:
            with open(audio_path, 'rb') as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file),
                    model="whisper-large-v3",
                    response_format="json"
                )

            texto = transcription.text
            print(f"✅ Audio transcrito con Groq: {texto[:50]}...")
            return texto

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                print("❌ Groq: API key inválida o sin permisos")
                print(f"   Detalle: {error_msg}")
                print("💡 Solución:")
                print("   1. Ve a https://console.groq.com/keys")
                print("   2. Genera una nueva API key")
                print("   3. Actualiza GROQ_API_KEY en .env")
                print("   4. Reinicia el bot")
            elif "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                print("⚠️ Groq: límite de créditos alcanzado")
            else:
                print(f"⚠️ Error con Groq: {error_msg}")
            return None

    def _transcribir_con_fish(self, audio_path: str, idioma: str) -> Optional[str]:
        """Transcribe usando Fish Audio"""
        try:
            idioma_map = {"es": "es", "en": "en", "pt": "pt", "fr": "fr"}
            language = idioma_map.get(idioma, "es")

            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                headers = {'Authorization': f'Bearer {self.fish_api_key}'}
                data = {'language': language}

                response = requests.post(
                    self.fish_base_url,
                    files=files,
                    headers=headers,
                    data=data
                )

            if response.status_code == 200:
                resultado = response.json()
                texto = resultado.get('text', '')
                print(f"✅ Audio transcrito con Fish Audio: {texto[:50]}...")
                return texto
            elif response.status_code == 402:
                print("❌ Fish Audio: API key inválida o sin balance")
                print("💡 Usa GROQ_API_KEY (gratis) en .env como alternativa")
                self.transcripcion_desactivada = True
                return None
            else:
                print(f"❌ Fish Audio error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error con Fish Audio: {e}")
            return None

    def limpiar_audio_temporal(self, audio_path: str):
        """
        Limpia un archivo de audio temporal

        Args:
            audio_path: Ruta del archivo a eliminar
        """
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"🗑️ Audio temporal eliminado: {audio_path}")
        except Exception as e:
            print(f"⚠️ No se pudo eliminar audio temporal: {e}")


# Instancia global
transcriptor = TranscriptorAudio()


# Test
if __name__ == "__main__":
    print("🎤 Fish Audio Transcriptor Test")
    print(f"API Key configurada: {'✅' if transcriptor.api_key else '❌'}")

    # Para probar, necesitas un archivo de audio
    # audio_path = "test_audio.ogg"
    # texto = transcriptor.transcribir_audio(audio_path)
    # print(f"Transcripción: {texto}")
