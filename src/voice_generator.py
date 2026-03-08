"""
Integración con ElevenLabs para generación de voz
"""
import requests
import tempfile
import os
from typing import Optional
from config import settings


class GeneradorVoz:
    """Clase para generar audio con ElevenLabs"""

    def __init__(self):
        """Inicializa el generador de voz"""
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
        self.base_url = "https://api.elevenlabs.io/v1"
        self.audio_desactivado_por_plan = False

        # Crear directorio temporal para audios si no existe
        self.audio_dir = "audio_temp"
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    def generar_audio(self, texto: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Genera un archivo de audio a partir de texto

        Args:
            texto: Texto a convertir en voz
            output_path: Ruta donde guardar el audio (opcional)

        Returns:
            Ruta del archivo de audio generado o None si hay error
        """
        if not self.api_key or not self.voice_id:
            print("⚠️ API Key o Voice ID de ElevenLabs no configurados")
            return None

        if self.audio_desactivado_por_plan:
            return None

        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }

            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                # Guardar el audio
                if output_path is None:
                    # Crear un archivo temporal
                    output_path = os.path.join(
                        self.audio_dir,
                        f"audio_{tempfile._get_candidate_names().__next__()}.mp3"
                    )

                with open(output_path, "wb") as f:
                    f.write(response.content)

                print(f"✅ Audio generado: {output_path}")
                return output_path
            elif response.status_code == 402:
                self.audio_desactivado_por_plan = True
                detalle = ""
                try:
                    payload = response.json()
                    detalle = payload.get("detail", {}).get("message", "")
                except Exception:
                    detalle = response.text

                print("❌ ElevenLabs bloqueó la generación de audio por plan gratis.")
                print("💡 Solución 1: usa una voz propia de 'My Voices' en ELEVENLABS_VOICE_ID.")
                print("💡 Solución 2: desactiva audio con ENVIAR_AUDIO_RESPUESTA=false en .env.")
                if detalle:
                    print(f"ℹ️ Detalle: {detalle}")
                return None
            else:
                print(f"❌ Error al generar audio: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error al generar audio con ElevenLabs: {e}")
            return None

    def limpiar_audios_temporales(self, max_archivos: int = 50):
        """
        Limpia archivos de audio antiguos para no saturar el disco

        Args:
            max_archivos: Número máximo de archivos a mantener
        """
        try:
            archivos = [
                os.path.join(self.audio_dir, f)
                for f in os.listdir(self.audio_dir)
                if f.endswith('.mp3')
            ]

            # Ordenar por fecha de modificación
            archivos.sort(key=lambda x: os.path.getmtime(x))

            # Si hay más archivos que el máximo, eliminar los más antiguos
            if len(archivos) > max_archivos:
                archivos_a_eliminar = archivos[:len(archivos) - max_archivos]
                for archivo in archivos_a_eliminar:
                    os.remove(archivo)
                print(f"🗑️ Limpiados {len(archivos_a_eliminar)} audios antiguos")

        except Exception as e:
            print(f"⚠️ Error al limpiar audios temporales: {e}")

    def listar_voces_disponibles(self):
        """
        Lista las voces disponibles en la cuenta de ElevenLabs
        Útil para configuración inicial
        """
        if not self.api_key:
            print("⚠️ API Key de ElevenLabs no configurado")
            return None

        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                voces = response.json()
                print("\n🎤 Voces disponibles:")
                for voz in voces.get('voices', []):
                    print(f"  - {voz['name']}: {voz['voice_id']}")
                    if voz.get('labels'):
                        print(f"    Etiquetas: {voz['labels']}")
                return voces
            else:
                print(f"❌ Error al obtener voces: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error al listar voces: {e}")
            return None


# Instancia global del generador de voz
generador_voz = GeneradorVoz()


if __name__ == "__main__":
    # Código de prueba
    print("🧪 Probando ElevenLabs...")

    # Listar voces disponibles
    generador_voz.listar_voces_disponibles()

    # Generar un audio de prueba
    texto_prueba = "Hola amiga, soy tu asistente financiera. Estoy aquí para ayudarte a cuidar tu dinero."
    audio_path = generador_voz.generar_audio(texto_prueba)

    if audio_path:
        print(f"✅ Audio de prueba generado en: {audio_path}")
    else:
        print("❌ No se pudo generar el audio de prueba")
