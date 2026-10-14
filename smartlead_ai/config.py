"""
config.py — ARALIK projesinin yapılandırma katmanı (Modül A)

Tüm ayarlar ve gizli anahtarlar BURADA toplanır.
Değerler .env dosyasından okunur; anahtar yoksa güvenli bir varsayılan kullanılır.
Bu dosya Flask, SQL veya yapay zekâ kodu İÇERMEZ — sadece ayar sağlar.
"""

import os

from dotenv import load_dotenv

# .env dosyasını okur. Bunu en başta çağırmazsak os.environ.get() .env'deki
# değerleri göremez.
load_dotenv()


# ---------------------------------------------------------------------------
# Yapay zekânın kişiliğini tanımlayan metin (SİSTEM TALİMATI)
# Projeye özel tek "konu" kısmı burasıdır; kodun geri kalanı konudan bağımsızdır.
# İstenirse .env içindeki BUSINESS_CONTEXT ile ezilebilir.
# ---------------------------------------------------------------------------
VARSAYILAN_BUSINESS_CONTEXT = """Sen ARALIK'ın akıllı seyahat ve rotalama asistanısın.
ARALIK, A noktası ile B noktası arasındaki zamanı ve günlük mikro ihtiyaçları
(kahve molası, ATM, eczane, şarj, yemek, tuvalet, kısa alışveriş) verimli
yönetmeye yardımcı olan yapay zekâ destekli bir seyahat ve rotalama platformudur.
Kullanıcının nereden nereye gittiğini, ne kadar zamanı olduğunu ve yolda neye
ihtiyaç duyduğunu sor; rotasına uygun, zamanı boşa harcatmayan öneriler sun.
Kısa, net, kibar ve samimi ol. Türkçe konuş.
Kullanıcı ilgilenirse, kendisine ulaşabilmemiz için isim ve telefon bırakmasını
nazikçe öner. Bilmediğin bir konuda uydurma bilgi verme.
Gerçek mekân adı, kesin mesafe veya fiyat uydurma; emin değilsen genel öneri ver.
Yanıtlarında Markdown kullanma (yıldız, diyez, tablo yok); düz metin ve kısa
cümleler yaz. En fazla 5-6 cümle yaz."""


class Config:
    """Tüm ortamlar için ortak (temel) ayarlar."""

    # Flask oturum/imza anahtarı. Üretimde MUTLAKA .env'den güçlü bir değer verin.
    SECRET_KEY = os.environ.get("SECRET_KEY", "gelistirme-icin-gizli-anahtar")

    # SQLite veritabanı dosya yolu (database.py bunu kullanacak).
    DATABASE_URL = os.environ.get("DATABASE_URL", "smartlead.db")

    # Groq API anahtarı (gsk_... ile başlar). Boşsa ai_service "demo modu"na geçer.
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

    # Kullanılacak yapay zekâ sağlayıcısı (ileride groq -> gemini geçişi kolay olsun).
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq")

    # Yapay zekânın kişiliği: .env'de varsa onu, yoksa yukarıdaki varsayılanı kullan.
    BUSINESS_CONTEXT = os.environ.get("BUSINESS_CONTEXT", VARSAYILAN_BUSINESS_CONTEXT)

    # CORS'a izin verilen adresler (Wix sitesi vb.). Virgülle ayrılmış liste olarak
    # okunur: "https://a.com,https://b.com" -> ["https://a.com", "https://b.com"]
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    DEBUG = False


class DevelopmentConfig(Config):
    """Geliştirme ortamı: hata ayıklama açık."""

    DEBUG = True


class ProductionConfig(Config):
    """Üretim (Render) ortamı: hata ayıklama kapalı."""

    DEBUG = False


# APP_ENV değerine göre doğru sınıfı seçen sözlük.
# Kullanım (Modül E'de): app.config.from_object(config[ortam_adi])
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}