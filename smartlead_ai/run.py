"""
run.py — ARALIK sunucusunu başlatan giriş noktası (Modül E)

Yerelde:  python run.py
Canlıda (Render): gunicorn run:app   (aşağıdaki 'app' nesnesini kullanır)
"""

import os

from app import create_app

# Fabrikadan uygulamayı al. gunicorn bu 'app' nesnesini bulup çalıştırır.
app = create_app()

if __name__ == "__main__":
    # Sadece yerel geliştirme için: DEBUG ayarı config'deki ortama göre belirlenir.
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=app.config["DEBUG"])
    