"""
database.py — ARALIK projesinin veri katmanı (Modül B)

Mimari sözleşme: Projede SQL YALNIZCA bu dosyada bulunur.
routes.py gibi diğer katmanlar sadece bu dosyadaki fonksiyonları çağırır.
Güvenlik: Kullanıcıdan gelen değerler SQL metnine ASLA doğrudan eklenmez;
her zaman ? yer tutucusu ve ayrı parametre demeti (tuple) kullanılır.
"""

import sqlite3

from flask import current_app


class DatabaseError(Exception):
    """Veritabanı işlemlerinde oluşan hataları tek tipte toplayan özel hata.

    routes.py bunu yakalayıp kullanıcıya güvenli bir JSON hata yanıtı döndürür;
    böylece ham SQLite hata mesajları dışarı sızmaz.
    """


def get_db():
    """Veritabanına bağlanır.

    row_factory = sqlite3.Row sayesinde satırlara sütun adıyla erişilir
    (örn. satir["isim"]). Bağlantı yolu config'deki DATABASE_URL'den gelir.
    Not: Flask uygulama bağlamı (app context) içinde çağrılmalıdır.
    """
    baglanti = sqlite3.connect(current_app.config["DATABASE_URL"])
    baglanti.row_factory = sqlite3.Row
    return baglanti


def init_db(app):
    """'leads' tablosunu oluşturur (yoksa). Uygulama başlarken bir kez çağrılır."""
    # get_db() current_app kullandığı için app context gerekir.
    with app.app_context():
        baglanti = None
        try:
            baglanti = get_db()
            # Bu sorguda kullanıcı verisi yok, sabit bir şema tanımıdır.
            baglanti.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim    TEXT NOT NULL,
                    telefon TEXT NOT NULL,
                    mesaj   TEXT,
                    tarih   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            baglanti.commit()
        except sqlite3.Error as hata:
            raise DatabaseError(f"Veritabanı oluşturulamadı: {hata}") from hata
        finally:
            # Hata olsa da olmasa da bağlantı kapatılır.
            if baglanti is not None:
                baglanti.close()


def lead_ekle(isim, telefon, mesaj=None):
    """Yeni bir lead (iletişim kaydı) ekler ve oluşan kaydın id'sini döndürür."""
    baglanti = None
    try:
        baglanti = get_db()
        # GÜVENLİK: Değerler ? yer tutucularıyla ayrı parametre olarak gönderilir.
        # f-string veya + ile SQL metnine değer eklemek SQL Injection'a yol açar.
        imlec = baglanti.execute(
            "INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)",
            (isim, telefon, mesaj),
        )
        baglanti.commit()
        return imlec.lastrowid
    except sqlite3.Error as hata:
        raise DatabaseError(f"Lead eklenemedi: {hata}") from hata
    finally:
        if baglanti is not None:
            baglanti.close()


def tum_leadler():
    """Tüm lead'leri en yeniden eskiye doğru, JSON'a hazır sözlük listesi olarak döndürür."""
    baglanti = None
    try:
        baglanti = get_db()
        satirlar = baglanti.execute(
            "SELECT id, isim, telefon, mesaj, tarih FROM leads "
            "ORDER BY tarih DESC, id DESC"
        ).fetchall()
        # sqlite3.Row nesnelerini düz sözlüğe çeviriyoruz (jsonify bunlarla çalışır).
        return [dict(satir) for satir in satirlar]
    except sqlite3.Error as hata:
        raise DatabaseError(f"Lead'ler getirilemedi: {hata}") from hata
    finally:
        if baglanti is not None:
            baglanti.close()
            