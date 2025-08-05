import requests
import json

class NLPEngine:
    def __init__(self, ollama_host='http://localhost:11434', model='mistral'):
        self.ollama_host = ollama_host.rstrip('/')
        self.model = model
        self.session = requests.Session()

    def generate_sql(self, prompt: str):
        """
        Hazır olarak oluşturulmuş prompt'u alır, Ollama/Mistral modeline
        gönderir ve SQL sorgusu olarak döndürür.

        Args:
            prompt (str): AppController'da PromptBuilder ile oluşturulan tam prompt.
        
        Returns:
            str: Model tarafından üretilen SQL sorgusu.
        """
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False
        }
        url = f"{self.ollama_host}/api/generate"
        try:
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get('response', '').strip()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API'sine ulaşılamadı. Lütfen Ollama'nın çalıştığından emin olun. Hata: {e}")
        except Exception as e:
            raise RuntimeError(f"Ollama/Mistral API hatası: {e}")