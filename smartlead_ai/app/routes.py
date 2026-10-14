"""
routes.py — ARALIK projesinin HTTP rotaları (Modül D)

Mimari sözleşme: Bu dosya SADECE gelen isteği karşılar, doğrular ve doğru katmana
yönlendirir. Burada SQL veya yapay zekâ API kodu YOKTUR:
  - Veri işlemleri  -> app.database fonksiyonları
  - Yapay zekâ      -> app.services.ai_service
Her API uç noktası "basari" alanı içeren bir JSON döndürür.
"""

from flask import Blueprint, jsonify, render_template, request

from app.database import DatabaseError, lead_ekle, tum_leadler
from app.services.ai_service import AIServiceError, ai_service

# İki Blueprint: biri sayfalar, biri API için.
# API Blueprint'inin "/api" öneki create_app() içinde (Modül E) url_prefix ile verilir;
# bu yüzden aşağıdaki API yolları "/sohbet" ve "/leads" olarak tanımlanır.
sayfalar_bp = Blueprint("sayfalar", __name__)
api_bp = Blueprint("api", __name__)

# Girdi sınırları (aşırı uzun metinlerle kötüye kullanımı engellemek için).
MAKS_MESAJ_UZUNLUGU = 1000
MAKS_ISIM_UZUNLUGU = 100


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar (sadece istek/yanıt biçimlendirme; SQL veya AI içermez)
# ---------------------------------------------------------------------------
def _hata(mesaj, kod):
    """Standart hata yanıtı: {"basari": false, "hata": "..."} ve durum kodu."""
    return jsonify({"basari": False, "hata": mesaj}), kod


def _json_govde():
    """İstek gövdesini sözlük olarak okur; bozuk/boş JSON gelirse boş sözlük döner."""
    veri = request.get_json(silent=True)
    return veri if isinstance(veri, dict) else {}


def _metin(veri, anahtar):
    """Sözlükten bir metin alanını okuyup kenar boşluklarını temizler (yoksa '')."""
    deger = veri.get(anahtar)
    return deger.strip() if isinstance(deger, str) else ""


def _telefon_gecerli_mi(telefon):
    """Telefon sadece rakam, +, -, parantez ve boşluk içermeli; 7-15 rakam olmalı."""
    izinli = all(harf.isdigit() or harf in "+-() " for harf in telefon)
    rakam_sayisi = sum(1 for harf in telefon if harf.isdigit())
    return izinli and 7 <= rakam_sayisi <= 15


# ---------------------------------------------------------------------------
# Sayfa rotaları
# ---------------------------------------------------------------------------
@sayfalar_bp.route("/")
def anasayfa():
    """Karşılama sayfasını gösterir."""
    return render_template("index.html")


@sayfalar_bp.route("/dashboard")
def panel():
    """Yönetim panelini gösterir."""
    return render_template("dashboard.html")


# ---------------------------------------------------------------------------
# API rotaları
# ---------------------------------------------------------------------------
@api_bp.route("/sohbet", methods=["POST"])
def sohbet():
    """Kullanıcı mesajını yapay zekâya iletir. Girdi: mesaj (+ opsiyonel gecmis)."""
    veri = _json_govde()
    mesaj = _metin(veri, "mesaj")

    # Eksik ya da çok uzun veri -> 400
    if not mesaj:
        return _hata("'mesaj' alanı zorunludur.", 400)
    if len(mesaj) > MAKS_MESAJ_UZUNLUGU:
        return _hata(f"Mesaj en fazla {MAKS_MESAJ_UZUNLUGU} karakter olabilir.", 400)

    # Geçmiş opsiyoneldir; liste değilse yok sayılır (içeriği ai_service süzer).
    gecmis = veri.get("gecmis")
    if not isinstance(gecmis, list):
        gecmis = []

    try:
        cevap = ai_service.yanit_uret(mesaj, gecmis)
    except AIServiceError as hata:
        # AI hatası -> 503; AIServiceError mesajları kullanıcıya gösterilmeye güvenlidir.
        return _hata(str(hata), 503)

    return jsonify({"basari": True, "cevap": cevap})


@api_bp.route("/leads", methods=["POST"])
def lead_kaydet():
    """Yeni lead kaydeder. Girdi: isim, telefon (zorunlu), mesaj (opsiyonel)."""
    veri = _json_govde()
    isim = _metin(veri, "isim")
    telefon = _metin(veri, "telefon")
    mesaj = _metin(veri, "mesaj") or None  # boşsa veritabanına NULL gider

    # Eksik veri -> 400
    if not isim or not telefon:
        return _hata("'isim' ve 'telefon' alanları zorunludur.", 400)
    if len(isim) > MAKS_ISIM_UZUNLUGU:
        return _hata(f"İsim en fazla {MAKS_ISIM_UZUNLUGU} karakter olabilir.", 400)
    if not _telefon_gecerli_mi(telefon):
        return _hata("Geçerli bir telefon numarası giriniz.", 400)
    if mesaj and len(mesaj) > MAKS_MESAJ_UZUNLUGU:
        return _hata(f"Mesaj en fazla {MAKS_MESAJ_UZUNLUGU} karakter olabilir.", 400)

    try:
        yeni_id = lead_ekle(isim, telefon, mesaj)
    except DatabaseError:
        # Ham veritabanı hatasını dışarı sızdırmıyoruz.
        return _hata("Kayıt şu anda yapılamıyor, lütfen daha sonra deneyin.", 500)

    # Yeni kayıt -> 201
    return jsonify({"basari": True, "id": yeni_id}), 201


@api_bp.route("/leads", methods=["GET"])
def lead_listele():
    """Tüm lead'leri en yeniden eskiye getirir."""
    try:
        leadler = tum_leadler()
    except DatabaseError:
        return _hata("Kayıtlar şu anda getirilemiyor, lütfen daha sonra deneyin.", 500)

    # Wix Velo Repeater her objede "_id" ister; id'yi metin olarak ekliyoruz.
    for lead in leadler:
        lead["_id"] = str(lead["id"])

    return jsonify({"basari": True, "toplam": len(leadler), "leads": leadler})
