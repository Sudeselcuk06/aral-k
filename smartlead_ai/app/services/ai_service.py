"""
ai_service.py — ARALIK projesinin yapay zekâ servis katmanı (Modül C)

Mimari sözleşme: Projede yapay zekâ API çağrıları YALNIZCA bu dosyada bulunur.
Bu dosya Flask, HTTP rotaları veya veritabanı kavramlarını BİLMEZ; sadece
yapay zekâ ile konuşur. Sağlayıcıyı değiştirmek (Groq -> Gemini) bu dosyayla sınırlıdır.
"""

import requests

from config import Config

# Groq'un OpenAI uyumlu sohbet (chat completions) adresi ve kullanılacak model.
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# İstek bu süre (saniye) içinde dönmezse vazgeçilir; sunucu sonsuza kadar beklemez.
ZAMAN_ASIMI = 20

# Modele gönderilecek en fazla geçmiş mesaj sayısı (maliyet ve hız için sınır).
MAKS_GECMIS = 10


class AIServiceError(Exception):
    """Yapay zekâ servisine özel hata.

    routes.py bunu yakalayıp kullanıcıya güvenli bir JSON hata yanıtı (503) döndürür.
    Böylece ham hata metinleri ve anahtar bilgisi dışarı sızmaz.
    """


class AIService:
    """Kullanıcı mesajını yapay zekâya gönderip yanıtı döndüren servis."""

    def __init__(self):
        # Ayarlar config.py'den (dolayısıyla .env'den) gelir; anahtar kodda tutulmaz.
        self.api_key = Config.GROQ_API_KEY
        self.provider = Config.AI_PROVIDER

    def _sistem_talimati(self):
        """Yapay zekânın kişiliğini tanımlayan BUSINESS_CONTEXT metnini döndürür."""
        return Config.BUSINESS_CONTEXT

    def _demo_modu_mu(self):
        """Anahtar yoksa ya da .env.example'daki yer tutucu duruyorsa demo moduna geçilir."""
        return (not self.api_key) or self.api_key.startswith("gsk_buraya")

    def _mesajlari_hazirla(self, mesaj, gecmis):
        """Groq'a gidecek 'messages' dizisini kurar.

        Sıra: önce sistem talimatı (system), sonra geçmiş mesajlar, en sonda yeni
        kullanıcı mesajı (user). Geçmiş: [{"role": "user"|"assistant", "content": "..."}]
        """
        mesajlar = [{"role": "system", "content": self._sistem_talimati()}]

        for oge in (gecmis or [])[-MAKS_GECMIS:]:
            # Bozuk/yetkisiz rol ya da boş içerik içeren öğeleri sessizce atla.
            if (
                isinstance(oge, dict)
                and oge.get("role") in ("user", "assistant")
                and isinstance(oge.get("content"), str)
                and oge["content"].strip()
            ):
                mesajlar.append({"role": oge["role"], "content": oge["content"]})

        mesajlar.append({"role": "user", "content": mesaj})
        return mesajlar

    def _groq_istegi(self, mesajlar):
        """Groq API'sine istek atar ve yapay zekânın metin yanıtını döndürür."""
        basliklar = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        govde = {
            "model": GROQ_MODEL,
            "messages": mesajlar,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        # Dış servis çağrısı: ağ hataları, zaman aşımı vb. try-except ile yakalanır.
        try:
            yanit = requests.post(
                GROQ_URL, headers=basliklar, json=govde, timeout=ZAMAN_ASIMI
            )
        except requests.exceptions.Timeout as hata:
            raise AIServiceError("Yapay zekâ servisi zaman aşımına uğradı.") from hata
        except requests.exceptions.RequestException as hata:
            raise AIServiceError("Yapay zekâ servisine ulaşılamadı.") from hata

        if yanit.status_code == 401:
            raise AIServiceError("Yapay zekâ API anahtarı geçersiz.")
        if yanit.status_code == 429:
            raise AIServiceError("Yapay zekâ servisi şu an yoğun, lütfen biraz sonra deneyin.")
        if yanit.status_code != 200:
            # Ham hata gövdesini dışarı vermiyoruz, sadece durum kodunu bildiriyoruz.
            raise AIServiceError(f"Yapay zekâ servisi hata döndürdü (HTTP {yanit.status_code}).")

        try:
            return yanit.json()["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError, AttributeError) as hata:
            raise AIServiceError("Yapay zekâ yanıtı beklenmeyen bir biçimde geldi.") from hata

    def yanit_uret(self, mesaj, gecmis=None):
        """Kullanıcı mesajına yapay zekâ yanıtı üretir.

        mesaj : kullanıcının yeni mesajı (str)
        gecmis: önceki konuşma, [{"role": "user"|"assistant", "content": "..."}] (opsiyonel)
        Hata durumunda AIServiceError fırlatır.
        """
        if not isinstance(mesaj, str) or not mesaj.strip():
            raise AIServiceError("Mesaj boş olamaz.")

        # Anahtar yoksa çökmek yerine anlaşılır bir demo mesajı döndür.
        if self._demo_modu_mu():
            return (
                "[DEMO MODU] Yapay zekâ API anahtarı tanımlı değil. "
                "Gerçek yanıt almak için .env dosyasına GROQ_API_KEY ekleyin. "
                f"Mesajınız alındı: {mesaj.strip()}"
            )

        if self.provider != "groq":
            raise AIServiceError(f"Desteklenmeyen yapay zekâ sağlayıcısı: {self.provider}")

        mesajlar = self._mesajlari_hazirla(mesaj.strip(), gecmis)
        return self._groq_istegi(mesajlar)


# Uygulama genelinde kullanılacak tek örnek (routes.py bunu import edecek).
ai_service = AIService()
