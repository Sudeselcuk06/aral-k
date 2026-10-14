"""
app/__init__.py — ARALIK uygulama fabrikası (Modül E)

create_app() tüm parçaları sırasıyla birleştirir:
  ayarları yükle -> CORS aç -> veritabanını hazırla -> blueprint'leri kaydet -> uygulamayı döndür.
Bu dosya iş mantığı içermez; sadece katmanları birbirine bağlar.
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS

from app.database import init_db
from app.routes import api_bp, sayfalar_bp
from config import config


def create_app():
    """Flask uygulamasını oluşturup yapılandırır ve döndürür (application factory)."""
    app = Flask(__name__)

    # 1) Ayarları yükle: APP_ENV (development/production) .env'den okunur.
    ortam = os.environ.get("APP_ENV", "development")
    app.config.from_object(config.get(ortam, config["default"]))

    # 2) CORS: Wix sitesinin API'ye tarayıcıdan istek atabilmesi için izin verilir.
    #    İzin verilen adresler config'deki CORS_ORIGINS'ten gelir (canlıda Wix adresiniz).
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # 3) Veritabanını hazırla: init_db bir uygulama bağlamı (app context) ister.
    with app.app_context():
        init_db(app)

    # 4) Blueprint'leri kaydet: API yollarının başına /api öneki eklenir.
    app.register_blueprint(sayfalar_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Sunucu canlılık kontrolü (Render ve manuel test için).
    @app.route("/health")
    def health():
        return jsonify({"basari": True, "durum": "aktif"})

    return app
