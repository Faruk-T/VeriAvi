import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import time
import unicodedata
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Veri Avı",
    page_icon="🕵️",
    layout="wide"
)

DB_PATH = Path(__file__).with_name("veri_avi.db")
QUESTION_TIME_LIMIT = 45  # Her soru için 45 saniye süre
ADMIN_PIN = "i<==>Bır#bıd&ık!?"  # Sadece arka planda (sunucuda) kontrol edilir; arayüzde veya HTML'de asla gösterilmez

# Seçenek seçilmediğinde varsayılan boş (0 puanlık) başlangıç seçeneği
PLACEHOLDER_OPTION = "— Lütfen analiz edip bir seçim yapınız —"

# 25 satırlık zenginleştirilmiş veri seti:
# Veri temizleme VE veri dönüştürme senaryolarını, ayrıca sadece tüm tabloya bakılarak
# fark edilebilecek çapraz kayıt çelişkilerini (Kayıt No, Öğrenci No, Ad Soyad, Yaş, Bölüm, Not) içerir.
DATA = [
    {"ID": 1, "Öğrenci No": "202401", "Ad Soyad": None, "Yaş": 20, "Bölüm": "Bilişim", "Not": "85"},
    {"ID": 2, "Öğrenci No": "202402", "Ad Soyad": "Ayşe Kaya", "Yaş": None, "Bölüm": "Bilişim", "Not": "90"},
    {"ID": 3, "Öğrenci No": "ANONİM", "Ad Soyad": "Anonim Katılımcı", "Yaş": 21, "Bölüm": "Yazılım", "Not": None},
    {"ID": 4, "Öğrenci No": "202404", "Ad Soyad": "Elif Yıldız", "Yaş": 19, "Bölüm": "Bilişim", "Not": "88"},
    {"ID": 5, "Öğrenci No": "202405", "Ad Soyad": "Zeynep Çelik", "Yaş": 150, "Bölüm": "Yazılım", "Not": "95"},
    {"ID": 6, "Öğrenci No": "202406", "Ad Soyad": "Can Şahin", "Yaş": 21, "Bölüm": " yazılım ", "Not": "78"},
    {"ID": 7, "Öğrenci No": "202404", "Ad Soyad": "Elif Yıldız", "Yaş": 19, "Bölüm": "Bilişim", "Not": "88"},
    {"ID": 8, "Öğrenci No": "202408", "Ad Soyad": "Mert Öztürk", "Yaş": 22, "Bölüm": "Veri Bilimi", "Not": "76"},
    {"ID": 9, "Öğrenci No": "202409", "Ad Soyad": "Selin Aydın", "Yaş": 23, "Bölüm": None, "Not": "92"},
    {"ID": 10, "Öğrenci No": "202410", "Ad Soyad": "Burak Özdemir", "Yaş": 21, "Bölüm": "Yazılım", "Not": "0.68 (Oran)"},
    {"ID": 11, "Öğrenci No": "202411", "Ad Soyad": "Ece Arslan", "Yaş": 20, "Bölüm": "bilişim", "Not": "81"},
    {"ID": 12, "Öğrenci No": "202412", "Ad Soyad": "Deniz Doğan", "Yaş": 24, "Bölüm": "Veri Bilimi", "Not": "-15"},
    {"ID": 13, "Öğrenci No": "202413", "Ad Soyad": "Oğuz Yalçın", "Yaş": 19, "Bölüm": "Yazılım", "Not": "BA (Harf)"},
    {"ID": 14, "Öğrenci No": "202408", "Ad Soyad": "Sude Aslan", "Yaş": 22, "Bölüm": "Yazılım", "Not": "89"},
    {"ID": 15, "Öğrenci No": "202415", "Ad Soyad": "Kaan Çetin", "Yaş": 20, "Bölüm": "Bilişim", "Not": "73"},
    {"ID": 16, "Öğrenci No": "ANONİM", "Ad Soyad": None, "Yaş": None, "Bölüm": None, "Not": None},
    {"ID": 17, "Öğrenci No": "202417", "Ad Soyad": "Arda Koç", "Yaş": 21, "Bölüm": "Yazılım", "Not": "110"},
    {"ID": 18, "Öğrenci No": "202418", "Ad Soyad": "Duru Kurt", "Yaş": 20, "Bölüm": " Bilişim", "Not": "86"},
    {"ID": 19, "Öğrenci No": "202419", "Ad Soyad": "Eren Özkan", "Yaş": -3, "Bölüm": "Veri Bilimi", "Not": "79"},
    {"ID": 20, "Öğrenci No": "202420", "Ad Soyad": "Naz Şimşek", "Yaş": 19, "Bölüm": "Yazılım Müh.", "Not": "91"},
    {"ID": 21, "Öğrenci No": "202408", "Ad Soyad": "Mert Öztürk", "Yaş": 22, "Bölüm": "Veri Bilimi", "Not": "76"},
    {"ID": 22, "Öğrenci No": "202422", "Ad Soyad": "Lara Polat", "Yaş": 20, "Bölüm": "Bilişim", "Not": "87,5"},
    {"ID": 23, "Öğrenci No": "202423", "Ad Soyad": "Ozan Korkmaz", "Yaş": 25, "Bölüm": "yazılım", "Not": "82"},
    {"ID": 24, "Öğrenci No": "202424", "Ad Soyad": "Mert Öztürk", "Yaş": 20, "Bölüm": "Bilişim", "Not": "93"},
    {"ID": 25, "Öğrenci No": "202425", "Ad Soyad": "Bora Erdoğan", "Yaş": 20, "Bölüm": "Veri Bilimi", "Not": "3.40 / 4.00"},
]

# Sorun türü seçenekleri (İlk sırada 0 puanlık seçim zorunluluğu sağlayan placeholder bulunur)
PROBLEM_OPTIONS = [
    PLACEHOLDER_OPTION,
    "Sorun yok (Veri temiz ve tutarlı)",
    "Eksik veri — Kaynaktan doğrulanabilir öğrenci kaydı",
    "Eksik veri — Kaynağı bilinmeyen anonim/anket kaydı",
    "Tamamen boş / kurtarılamaz gürültülü kayıt",
    "Tekrarlanan kayıt (Birebir kopya satır)",
    "Anahtar / Kimlik çakışması (Aynı Öğrenci No farklı kişide)",
    "Aykırı veya mantıksız sayısal değer (Outlier / Gürültü)",
    "Yazım, büyük-küçük harf veya kenar boşluğu hatası",
    "Ölçek / Birim farklılığı (0-1 oranı veya 4'lük sistem notu)",
    "Veri tipi veya kategori kodlama uyumsuzluğu (Harf notu / Virgüllü metin / Kısaltma)",
]

# Yapılacak işlem seçenekleri (İlk sırada 0 puanlık seçim zorunluluğu sağlayan placeholder bulunur)
ACTION_OPTIONS = [
    PLACEHOLDER_OPTION,
    "Herhangi bir değişiklik yapma (Kayıt doğru)",
    "Eksik bilgiyi öğrenci işlerinden / resmi kaynaktan öğrenip tamamla",
    "Eksik sayısal veriyi bölüm/sınıf ortalaması (Imputation) ile doldur",
    "Kaydı tamamen veri setinden çıkar (Drop Row)",
    "Tekrarlanan (kopya) satırı tablodan sil (Drop Duplicates)",
    "Öğrenci numarasını kaynak sistemden kontrol edip benzersiz (unique) hale getir",
    "Hatalı girilen uç/negatif sayısal değeri kaynak belgeyle düzelt",
    "Gereksiz boşlukları sil (strip) ve standart baş harf düzenine (title) çevir",
    "Min-Max / Ölçek dönüştürme ile değeri 0–100 puan sistemine normalize et",
    "Tip dönüştürme (Type Casting) veya Kategori Eşleme (Mapping) ile standartlaştır",
]

# Doğru cevaplar: (sorun türü, yapılacak işlem, anlaşılır açıklama)
ISSUES = {
    1: (
        "Eksik veri — Kaynaktan doğrulanabilir öğrenci kaydı",
        "Eksik bilgiyi öğrenci işlerinden / resmi kaynaktan öğrenip tamamla",
        "Öğrenci No (202401) bilindiği için Ad Soyad tahmin edilmez; öğrenci işleri sisteminden doğrulanarak tamamlanır."
    ),
    2: (
        "Eksik veri — Kaynaktan doğrulanabilir öğrenci kaydı",
        "Eksik bilgiyi öğrenci işlerinden / resmi kaynaktan öğrenip tamamla",
        "Ayşe Kaya'nın öğrenci numarası (202402) mevcuttur. Yaş bilgisi resmi kayıttan bakılarak tamamlanmalıdır."
    ),
    3: (
        "Eksik veri — Kaynağı bilinmeyen anonim/anket kaydı",
        "Eksik sayısal veriyi bölüm/sınıf ortalaması (Imputation) ile doldur",
        "Kayıt 'ANONİM' olduğu için öğrenci işlerinden gerçek not öğrenilemez. İstatistiksel analizde satırı kaybetmemek için bölüm/sınıf ortalaması ile doldurulur (Imputation)."
    ),
    4: (
        "Sorun yok (Veri temiz ve tutarlı)",
        "Herhangi bir değişiklik yapma (Kayıt doğru)",
        "Kayıt #4 tüm kurallara uygun ve ilk (orijinal) kayıttır. (7. satır bu kaydın kopyasıdır, ancak 4. satır korunmalıdır)."
    ),
    5: (
        "Aykırı veya mantıksız sayısal değer (Outlier / Gürültü)",
        "Hatalı girilen uç/negatif sayısal değeri kaynak belgeyle düzelt",
        "150 yaş değeri olanaksız bir uç değerdir (Outlier). Kaynak kayıt kontrol edilerek gerçek yaş ile düzeltilmelidir."
    ),
    6: (
        "Yazım, büyük-küçük harf veya kenar boşluğu hatası",
        "Gereksiz boşlukları sil (strip) ve standart baş harf düzenine (title) çevir",
        "Bölüm değerinde (' yazılım ') hem başta/sonda boşluk hem küçük harf var. strip() ve title() ile 'Yazılım' yapılmalı."
    ),
    7: (
        "Tekrarlanan kayıt (Birebir kopya satır)",
        "Tekrarlanan (kopya) satırı tablodan sil (Drop Duplicates)",
        "Tablo incelendiğinde 7. satırın Öğrenci No (202404) ve tüm bilgileriyle 4. satırın birebir kopyası olduğu görülür; kopya silinmelidir."
    ),
    8: (
        "Sorun yok (Veri temiz ve tutarlı)",
        "Herhangi bir değişiklik yapma (Kayıt doğru)",
        "Mert Öztürk'ün (202408) ilk ve doğru kaydıdır. Tablodaki 21. satır bunun kopyasıdır ama 8. satır orijinal olduğu için dokunulmaz."
    ),
    9: (
        "Eksik veri — Kaynaktan doğrulanabilir öğrenci kaydı",
        "Eksik bilgiyi öğrenci işlerinden / resmi kaynaktan öğrenip tamamla",
        "Selin Aydın'ın Öğrenci No (202409) bilgisi mevcuttur; eksik olan Bölüm alanı resmi kayıttan tamamlanmalıdır."
    ),
    10: (
        "Ölçek / Birim farklılığı (0-1 oranı veya 4'lük sistem notu)",
        "Min-Max / Ölçek dönüştürme ile değeri 0–100 puan sistemine normalize et",
        "Not '0.68 (Oran)' şeklinde 0–1 ölçeğinde kaydedilmiş. Veri dönüştürme (ölçekleme) ile 100'lük sisteme (68) dönüştürülmelidir."
    ),
    11: (
        "Yazım, büyük-küçük harf veya kenar boşluğu hatası",
        "Gereksiz boşlukları sil (strip) ve standart baş harf düzenine (title) çevir",
        "'bilişim' küçük harfle yazıldığı için gruplamalarda ayrı bir kategori gibi görünür. 'Bilişim' olarak standartlaştırılmalıdır."
    ),
    12: (
        "Aykırı veya mantıksız sayısal değer (Outlier / Gürültü)",
        "Hatalı girilen uç/negatif sayısal değeri kaynak belgeyle düzelt",
        "-15 sınav notu olamaz (0–100 aralığı dışı). Muhtemelen 15 yazılırken tire eklendi; kaynak sınav kağıdından doğrulanıp düzeltilmeli."
    ),
    13: (
        "Veri tipi veya kategori kodlama uyumsuzluğu (Harf notu / Virgüllü metin / Kısaltma)",
        "Tip dönüştürme (Type Casting) veya Kategori Eşleme (Mapping) ile standartlaştır",
        "Sınav notu sayısal yerine 'BA (Harf)' olarak girilmiş. Kategori eşleme (Mapping) tablosuyla sayısal karşılığına dönüştürülmelidir."
    ),
    14: (
        "Anahtar / Kimlik çakışması (Aynı Öğrenci No farklı kişide)",
        "Öğrenci numarasını kaynak sistemden kontrol edip benzersiz (unique) hale getir",
        "DİKKAT: Sadece veri tablosunu inceleyenler 202408 numarasının 8. satırda Mert Öztürk'e ait olduğunu fark edebilir! Sude Aslan'a yanlışlıkla aynı Öğrenci No verilmiştir."
    ),
    15: (
        "Sorun yok (Veri temiz ve tutarlı)",
        "Herhangi bir değişiklik yapma (Kayıt doğru)",
        "Kaan Çetin kaydının tüm alanları kurallara, veri tiplerine ve tekillik (unique) kısıtlarına uygundur."
    ),
    16: (
        "Tamamen boş / kurtarılamaz gürültülü kayıt",
        "Kaydı tamamen veri setinden çıkar (Drop Row)",
        "Öğrenci anonim ve Ad, Yaş, Bölüm, Not alanlarının tamamı boş (NaN). Hiçbir bilgi taşımadığı için satır veri setinden silinmelidir (Drop Row)."
    ),
    17: (
        "Aykırı veya mantıksız sayısal değer (Outlier / Gürültü)",
        "Hatalı girilen uç/negatif sayısal değeri kaynak belgeyle düzelt",
        "110 notu 0–100 ölçeğinin üst sınırını aşmaktadır. Kaynak sınav listesinden kontrol edilerek düzeltilmelidir."
    ),
    18: (
        "Yazım, büyük-küçük harf veya kenar boşluğu hatası",
        "Gereksiz boşlukları sil (strip) ve standart baş harf düzenine (title) çevir",
        "Bölüm adının başında görünmez boşluk (' Bilişim') var. Boşluk temizlenmezse filtreleme ve gruplama hatalı çalışır."
    ),
    19: (
        "Aykırı veya mantıksız sayısal değer (Outlier / Gürültü)",
        "Hatalı girilen uç/negatif sayısal değeri kaynak belgeyle düzelt",
        "-3 yaş değeri mantıksızdır. Kaynak belgeden kontrol edilerek doğru pozitif tam sayı değeriyle güncellenmelidir."
    ),
    20: (
        "Veri tipi veya kategori kodlama uyumsuzluğu (Harf notu / Virgüllü metin / Kısaltma)",
        "Tip dönüştürme (Type Casting) veya Kategori Eşleme (Mapping) ile standartlaştır",
        "Tablodaki standart bölüm adı 'Yazılım' iken burada 'Yazılım Müh.' kısaltması kullanılmış. Kategori eşleme ile 'Yazılım' değerine dönüştürülmelidir."
    ),
    21: (
        "Tekrarlanan kayıt (Birebir kopya satır)",
        "Tekrarlanan (kopya) satırı tablodan sil (Drop Duplicates)",
        "8. satırdaki Mert Öztürk (202408) kaydının birebir kopyasıdır. Mükerrer satır veri setinden kaldırılmalıdır."
    ),
    22: (
        "Veri tipi veya kategori kodlama uyumsuzluğu (Harf notu / Virgüllü metin / Kısaltma)",
        "Tip dönüştürme (Type Casting) veya Kategori Eşleme (Mapping) ile standartlaştır",
        "Not '87,5' şeklinde virgüllü metin (string) olarak girilmiş. Noktalı sayıya çevrilip tip dönüşümü (float/int type casting) yapılmalıdır."
    ),
    23: (
        "Yazım, büyük-küçük harf veya kenar boşluğu hatası",
        "Gereksiz boşlukları sil (strip) ve standart baş harf düzenine (title) çevir",
        "Bölüm adı 'yazılım' şeklinde küçük harfle başlamış. Standart 'Yazılım' formatına dönüştürülmelidir."
    ),
    24: (
        "Sorun yok (Veri temiz ve tutarlı)",
        "Herhangi bir değişiklik yapma (Kayıt doğru)",
        "ŞAŞIRTMACA: İsim 'Mert Öztürk' olsa da Öğrenci No (202424), Yaş (20) ve Bölüm (Bilişim) tamamen farklıdır! Gerçek hayatta aynı isimli iki farklı öğrenci olabilir; numara benzersiz olduğu için kayıt temizdir."
    ),
    25: (
        "Ölçek / Birim farklılığı (0-1 oranı veya 4'lük sistem notu)",
        "Min-Max / Ölçek dönüştürme ile değeri 0–100 puan sistemine normalize et",
        "Not '3.40 / 4.00' olarak 4'lük katsayı sisteminde girilmiş. Diğer kayıtlarla aynı analizde kullanılabilmesi için 100'lük ölçeğe dönüştürülmelidir."
    ),
}


def format_turkish_title(text: str) -> str:
    """Türkçe karakter uyumlu baş harf büyütme fonksiyonu."""
    words = text.strip().split()
    formatted_words = []
    for word in words:
        if not word:
            continue
        first_char = word[0]
        if first_char == "i":
            first_upper = "İ"
        elif first_char == "ı":
            first_upper = "I"
        else:
            first_upper = first_char.upper()

        rest = ""
        for ch in word[1:]:
            if ch == "İ":
                rest += "i"
            elif ch == "I":
                rest += "ı"
            else:
                rest += ch.lower()
        formatted_words.append(first_upper + rest)
    return " ".join(formatted_words)


def clean_letters_and_spaces(text: str) -> str:
    """Bütün harfleri (Türkçe ve Unicode harfler dahil) ve boşluk karakterlerini korur,
    rakam ve noktalama/özel karakterleri temizler."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    result = []
    for ch in normalized:
        if ch.isalpha() or ch.isspace():
            result.append(" " if ch.isspace() else ch)
    return "".join(result)


def validate_full_name(text: str) -> tuple[bool, str]:
    """Tek kutucuklu Ad Soyad alanının geçerliliğini kontrol eder."""
    if not text or not text.strip():
        return False, "Lütfen **Ad Soyad** alanını boş bırakmayın."
    cleaned = clean_letters_and_spaces(text)
    if cleaned != unicodedata.normalize("NFC", text):
        return False, "**Ad Soyad** alanında yalnızca harf ve boşluk kullanılmalıdır (rakam veya özel karakter girilemez)."
    words = [w for w in cleaned.strip().split() if w]
    total_letters = sum(len(w) for w in words)
    if total_letters < 2:
        return False, "Lütfen en az 2 harften oluşan geçerli bir isim girin."
    return True, format_turkish_title(" ".join(words))


def handle_name_entry() -> None:
    """Kullanıcı ismini yazıp Enter'a bastığında çalışır:
    harf dışını temizler, geçerliyse sayfa yenilenene kadar ismi kilitler."""
    raw_val = st.session_state.get("full_name_input", "")
    cleaned_val = clean_letters_and_spaces(raw_val)
    if unicodedata.normalize("NFC", raw_val) != cleaned_val:
        st.session_state["full_name_input"] = cleaned_val
        st.session_state["non_letter_warn"] = True
    else:
        st.session_state["non_letter_warn"] = False

    is_ok, formatted_or_err = validate_full_name(cleaned_val)
    if is_ok:
        st.session_state["full_name_input"] = formatted_or_err
        st.session_state["locked_player_name"] = formatted_or_err
        st.session_state["name_locked"] = True


def verify_admin_pin() -> None:
    """Admin PIN kutucuğuna girilen değeri doğrular ve kutucuğun içini ANINDA temizler.
    Böylece tarayıcıda 'İncele' (Inspect Element) yapıldığında DOM üzerinde value='' kalır."""
    entered = st.session_state.get("admin_pin_field", "")
    st.session_state["admin_pin_field"] = ""  # DOM'da şifrenin kalmasını engeller
    if entered == ADMIN_PIN:
        st.session_state["admin_authenticated"] = True
        st.session_state["admin_pin_error"] = False
    else:
        st.session_state["admin_authenticated"] = False
        st.session_state["admin_pin_error"] = True


def format_raw_cell(val, col_name: str, for_html: bool = False) -> str:
    """Hem üstteki veri tablosu hem de alttaki kartlar için İPUCUSUZ, ham veri görünümü üretir."""
    if val is None or pd.isna(val) or (isinstance(val, str) and val == ""):
        return "—"
    if col_name == "Yaş":
        return str(int(val))
    return str(val)


def init_db():
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                percent REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            UPDATE results
            SET score = score * 2, max_score = 100
            WHERE max_score = 50
        """)


def save_result(name, score, max_score):
    percent = round(score / max_score * 100, 1)
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute(
            """INSERT INTO results
            (player_name, score, max_score, percent, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (
                name.strip(),
                score,
                max_score,
                percent,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )


def clear_all_results():
    """Veritabanındaki tüm skor kayıtlarını siler ve otomatik artan ID sayacını sıfırlar."""
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute("DELETE FROM results;")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='results';")
        conn.commit()


def delete_single_result(player_name_to_del: str, created_at_to_del: str):
    """Belirli bir kaydı siler."""
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute(
            "DELETE FROM results WHERE player_name = ? AND created_at = ?",
            (player_name_to_del, created_at_to_del)
        )
        conn.commit()


def get_leaderboard():
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        return pd.read_sql_query("""
            SELECT player_name AS 'Ad Soyad',
                   score AS Puan,
                   max_score AS 'Maksimum Puan',
                   percent AS 'Başarı (%)',
                   created_at AS Tarih
            FROM results
            ORDER BY score DESC, percent DESC, id ASC
            LIMIT 40
        """, conn)


def finalize_quiz(player_name: str):
    """Tüm sorular bittiğinde puanı hesaplar, veritabanına kaydeder ve sonuç ekranını açar."""
    total_cards = len(DATA)
    score = 0
    details = []

    for r in DATA:
        r_id = r["ID"]
        u_prob, u_act = st.session_state["user_answers"].get(
            r_id, (PLACEHOLDER_OPTION, PLACEHOLDER_OPTION)
        )
        exp_prob, exp_act, explanation = ISSUES[r_id]

        prob_ok = u_prob == exp_prob
        act_ok = u_act == exp_act
        score += (2 if prob_ok else 0) + (2 if act_ok else 0)

        prob_label = "Boş bırakıldı" if u_prob == PLACEHOLDER_OPTION else u_prob
        act_label = "Boş bırakıldı" if u_act == PLACEHOLDER_OPTION else u_act

        details.append({
            "Kayıt No": r_id,
            "Öğrenci No": format_raw_cell(r["Öğrenci No"], "Öğrenci No"),
            "Ad Soyad": format_raw_cell(r["Ad Soyad"], "Ad Soyad"),
            "Sorun Tespiti": (
                f"✅ Doğru ({prob_label})" if prob_ok
                else f"❌ Yanlış — Seçilen: {prob_label} | Doğrusu: {exp_prob}"
            ),
            "Çözüm İşlemi": (
                f"✅ Doğru ({act_label})" if act_ok
                else f"❌ Yanlış — Seçilen: {act_label} | Doğrusu: {exp_act}"
            ),
            "Detaylı Açıklama": explanation
        })

    max_score = total_cards * 4
    percent = round(score / max_score * 100, 1)

    st.session_state["last_result"] = {
        "name": player_name,
        "score": score,
        "max_score": max_score,
        "percent": percent,
        "details": details
    }

    # Aynı oturumda veritabanına mükerrer kayıt yazılmasını önle
    if not st.session_state.get("attempt_completed", False):
        save_result(player_name, score, max_score)
        st.session_state["attempt_completed"] = True

    st.session_state["show_result"] = True
    st.session_state["quiz_started"] = False
    st.session_state["inspect_dataset"] = False


def advance_to_next_question(player_name: str, allow_unselected: bool = False) -> bool:
    """Mevcut sorunun cevabını kaydeder ve bir sonraki soruya (veya sonuç ekranına) geçiş yapar.
    Sınav tamamlandıysa True, sonraki soruya geçildiyse False döner."""
    idx = st.session_state["current_index"]
    total_cards = len(DATA)
    current_row = DATA[idx]
    row_id = current_row["ID"]

    # O anki seçimleri kaydet
    chosen_problem = st.session_state.get(f"step_problem_{row_id}", PLACEHOLDER_OPTION)
    chosen_action = st.session_state.get(f"step_action_{row_id}", PLACEHOLDER_OPTION)

    if not allow_unselected and (chosen_problem == PLACEHOLDER_OPTION or chosen_action == PLACEHOLDER_OPTION):
        st.session_state["selection_warning"] = True
        return False

    st.session_state["selection_warning"] = False
    st.session_state["user_answers"][row_id] = (chosen_problem, chosen_action)

    if idx < total_cards - 1:
        st.session_state["current_index"] = idx + 1
        st.session_state["question_start_time"] = time.time()
        return False
    else:
        finalize_quiz(player_name)
        return True


def build_theme_css(theme_mode: str) -> str:
    """Seçilen temaya (dark veya light) göre mavi ve tonlarından uzak,
    masaüstü ve MOBİL ekranlara (%100 responsive) uyumlu, pop-up (dialog) ve
    uyarı kutularındaki tüm yazıları tam kontrastlı gösteren CSS üretir."""
    if theme_mode == "dark":
        v = {
            "bg_main": "radial-gradient(circle at top right, #231b16 0%, #14110f 45%, #0c0a09 100%)",
            "header_bg": "rgba(18, 15, 13, 0.90)",
            "text_primary": "#fafaf9",
            "text_secondary": "#e7e5e4",
            "text_muted": "#d6d3d1",
            "accent_amber": "#f59e0b",
            "accent_copper": "#ea580c",
            "accent_emerald": "#10b981",
            "hero_bg": "linear-gradient(135deg, #1c1917 0%, #2e1f18 55%, #171412 100%)",
            "hero_border": "#574338",
            "hero_title": "#ffffff",
            "hero_sub": "#e7e5e4",
            "section_bg": "rgba(28, 24, 21, 0.94)",
            "section_border": "#443830",
            "card_bg": "linear-gradient(145deg, #26211e, #171412)",
            "card_border": "#f59e0b",
            "input_bg": "#26211e",
            "input_border": "#786659",
            "input_text": "#ffffff",
            "modal_bg": "#181412",
            "modal_border": "#f59e0b",
            "metric_card_bg": "linear-gradient(145deg, #29231f, #1c1815)",
            "metric_card_border": "#57463b",
            "metric_label": "#fcd34d",
            "metric_value": "#ffffff",
            "primary_btn": "linear-gradient(90deg, #d97706, #ea580c)",
            "primary_btn_shadow": "rgba(234, 88, 12, 0.42)",
            "secondary_btn_bg": "linear-gradient(135deg, #2e2723, #1c1815)",
            "secondary_btn_border": "#f59e0b",
            "secondary_btn_text": "#fef3c7",
            "pill_bg": "linear-gradient(90deg, #ea580c, #10b981)",
            "pill_shadow": "rgba(234, 88, 12, 0.45)",
            "timer_box_bg": "#26211e",
            "timer_box_border": "#574c44",
            "field_box_bg": "#151210",
            "field_box_border": "#3b332e",
            "field_row_border": "#2e2723",
            "field_label": "#e7e5e4",
            "field_val_bg": "#29231f",
            "field_val_text": "#ffffff",
            "field_val_border": "#574c44",
            "inspect_bg": "linear-gradient(90deg, #2e1f18, #192920)",
            "inspect_border": "#f59e0b",
            "inspect_title": "#fde68a",
            "glow_1": "rgba(245, 158, 11, 0.75)",
            "glow_2": "rgba(16, 185, 129, 0.65)",
            "glow_border_1": "#f59e0b",
            "glow_border_2": "#10b981",
            "df_border": "#443c36",
            "alert_bg": "#2e2116",
            "alert_border": "#f59e0b",
            "alert_text": "#fef3c7",
        }
    else:
        v = {
            "bg_main": "radial-gradient(circle at top right, #fffbeb 0%, #f5f5f4 50%, #e7e5e4 100%)",
            "header_bg": "rgba(255, 251, 235, 0.90)",
            "text_primary": "#1c1917",
            "text_secondary": "#292524",
            "text_muted": "#44403c",
            "accent_amber": "#d97706",
            "accent_copper": "#c2410c",
            "accent_emerald": "#059669",
            "hero_bg": "linear-gradient(135deg, #ffffff 0%, #fef3c7 55%, #ffedd5 100%)",
            "hero_border": "#d6d3d1",
            "hero_title": "#1c1917",
            "hero_sub": "#292524",
            "section_bg": "#ffffff",
            "section_border": "#d6d3d1",
            "card_bg": "linear-gradient(145deg, #ffffff, #fafaf9)",
            "card_border": "#d97706",
            "input_bg": "#ffffff",
            "input_border": "#a8a29e",
            "input_text": "#1c1917",
            "modal_bg": "#ffffff",
            "modal_border": "#d97706",
            "metric_card_bg": "linear-gradient(145deg, #fffbeb, #fafaf9)",
            "metric_card_border": "#f59e0b",
            "metric_label": "#9a3412",
            "metric_value": "#1c1917",
            "primary_btn": "linear-gradient(90deg, #d97706, #ea580c)",
            "primary_btn_shadow": "rgba(217, 119, 6, 0.32)",
            "secondary_btn_bg": "linear-gradient(135deg, #ffffff, #f5f5f4)",
            "secondary_btn_border": "#d97706",
            "secondary_btn_text": "#9a3412",
            "pill_bg": "linear-gradient(90deg, #d97706, #059669)",
            "pill_shadow": "rgba(217, 119, 6, 0.30)",
            "timer_box_bg": "#f5f5f4",
            "timer_box_border": "#d6d3d1",
            "field_box_bg": "#fafaf9",
            "field_box_border": "#d6d3d1",
            "field_row_border": "#e7e5e4",
            "field_label": "#44403c",
            "field_val_bg": "#ffffff",
            "field_val_text": "#1c1917",
            "field_val_border": "#a8a29e",
            "inspect_bg": "linear-gradient(90deg, #fef3c7, #ecfdf5)",
            "inspect_border": "#d97706",
            "inspect_title": "#92400e",
            "glow_1": "rgba(217, 119, 6, 0.45)",
            "glow_2": "rgba(5, 150, 105, 0.40)",
            "glow_border_1": "#d97706",
            "glow_border_2": "#059669",
            "df_border": "#cbd5e1",
            "alert_bg": "#fffbeb",
            "alert_border": "#d97706",
            "alert_text": "#78350f",
        }

    return f"""
<style>
/* 1. ÜST STREAMLIT HEADER'I ŞEFFAF YAP VE YATAY TAŞMALARI ENGELLE */
html, body, .stApp {{
    overflow-x: hidden !important;
    max-width: 100vw !important;
}}
header[data-testid="stHeader"] {{
    background: transparent !important;
    border-bottom: none !important;
    pointer-events: none;
}}
header[data-testid="stHeader"] button,
header[data-testid="stHeader"] a {{
    pointer-events: auto;
    color: {v["text_primary"]} !important;
}}
div[data-testid="stDecoration"] {{
    background-image: linear-gradient(90deg, #d97706, #ea580c, #10b981) !important;
}}

/* 2. ANA ARKA PLAN VE TÜM YAZILAR */
.stApp {{
    background: {v["bg_main"]} !important;
    color: {v["text_primary"]} !important;
}}
.block-container {{
    max-width: 1450px;
    padding-top: 3.6rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}}
h1, h2, h3, h4, h5, h6,
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] span,
label[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"] span,
div[data-testid="stCaptionContainer"] p {{
    color: {v["text_primary"]} !important;
    opacity: 1 !important;
    word-break: break-word;
}}
div[data-testid="stCaptionContainer"] p {{
    color: {v["text_muted"]} !important;
    font-size: 0.92rem !important;
}}

/* 3. MODAL (POP-UP DIALOG) ARKA PLANI VE İÇİNDEKİ TÜM BAŞLIK/ETİKETLER (HER CİHAZDA KESİN KONTRAST) */
div.stDialog,
div[data-testid="stDialog"],
div[data-testid="stDialog"] > div,
div[data-testid="stDialog"] > div > div,
div[data-testid="stDialog"] > div > div > div,
div[data-testid="stDialog"] [role="dialog"],
div[role="dialog"],
div[role="dialog"] > div,
div[data-baseweb="modal"],
div[data-baseweb="modal"] [role="dialog"],
div[data-baseweb="modal"] div,
section[role="dialog"] {{
    background-color: {v["modal_bg"]} !important;
    background: {v["modal_bg"]} !important;
    color: {v["text_primary"]} !important;
}}
div[role="dialog"],
div[data-testid="stDialog"] [role="dialog"] {{
    border: 2px solid {v["modal_border"]} !important;
    border-radius: 20px !important;
    max-width: 96vw !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.65) !important;
}}
div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3,
div[role="dialog"] p,
div[role="dialog"] label,
div[role="dialog"] label p,
div[role="dialog"] div[data-testid="stMarkdownContainer"] p,
div[role="dialog"] div[data-testid="stWidgetLabel"] p,
div[data-testid="stDialog"] label p,
div[data-testid="stDialog"] p {{
    color: {v["text_primary"]} !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}}
/* Dialog kapatma (X) butonu */
div[role="dialog"] button[aria-label="Close"],
div[data-testid="stDialog"] button[aria-label="Close"] {{
    color: {v["text_primary"]} !important;
    background: rgba(217, 119, 6, 0.18) !important;
    border-radius: 8px !important;
}}

/* 4. UYARI / BİLGİ KUTULARI (st.warning, st.info, st.success, st.error) İÇİNDEKİ GÖRÜNMEYEN YAZILARI DÜZELT */
div[data-testid="stAlert"],
div[data-baseweb="notification"] {{
    background-color: {v["alert_bg"]} !important;
    border: 1.5px solid {v["alert_border"]} !important;
    border-radius: 12px !important;
    color: {v["alert_text"]} !important;
}}
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] strong,
div[data-baseweb="notification"] p,
div[data-baseweb="notification"] span {{
    color: {v["alert_text"]} !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}}

/* 5. SONUÇ KARNESİ METRİK KUTULARI */
div[data-testid="stMetric"] {{
    background: {v["metric_card_bg"]} !important;
    border: 1.5px solid {v["metric_card_border"]} !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 6px 18px -6px rgba(0, 0, 0, 0.25) !important;
}}
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] {{
    color: {v["metric_label"]} !important;
    font-weight: 800 !important;
    font-size: 0.98rem !important;
    opacity: 1 !important;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div {{
    color: {v["metric_value"]} !important;
    font-weight: 900 !important;
    font-size: 1.7rem !important;
    opacity: 1 !important;
    white-space: normal !important;
    line-height: 1.25 !important;
}}

/* 6. INPUT KUTULARI VE UZUN SEÇENEKLİ SELECTBOX (TAŞMA VE RENK KONTRASTI) */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {{
    background-color: {v["input_bg"]} !important;
    border: 1.5px solid {v["input_border"]} !important;
    color: {v["input_text"]} !important;
    border-radius: 10px !important;
    opacity: 1 !important;
    min-height: 2.95rem !important;
}}
div[data-baseweb="input"] input {{
    color: {v["input_text"]} !important;
    -webkit-text-fill-color: {v["input_text"]} !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}}
/* Mobilde selectbox'a dokununca klavyenin açılmasını ve imleç yanıp sönmesini engelle */
div[data-baseweb="select"] input,
[data-testid="stSelectbox"] input {{
    cursor: pointer !important;
    caret-color: transparent !important;
    user-select: none !important;
    -webkit-user-select: none !important;
}}
div[data-baseweb="input"] input:disabled {{
    color: {v["accent_amber"]} !important;
    -webkit-text-fill-color: {v["accent_amber"]} !important;
    opacity: 1 !important;
}}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {{
    color: {v["input_text"]} !important;
    -webkit-text-fill-color: {v["input_text"]} !important;
    font-weight: 700 !important;
    white-space: normal !important;
    line-height: 1.3 !important;
}}
div[data-baseweb="select"] svg {{
    fill: {v["input_text"]} !important;
}}
/* Açılır menü (Dropdown) listesi */
ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"] {{
    background-color: {v["modal_bg"]} !important;
    border: 1.5px solid {v["card_border"]} !important;
    max-width: 95vw !important;
}}
li[role="option"] {{
    color: {v["text_primary"]} !important;
    background-color: {v["modal_bg"]} !important;
    white-space: normal !important;
    line-height: 1.35 !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
    font-weight: 600 !important;
}}
li[role="option"] span,
li[role="option"] div {{
    color: {v["text_primary"]} !important;
}}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {{
    background-color: rgba(217, 119, 6, 0.28) !important;
    color: {v["text_primary"]} !important;
    font-weight: 800 !important;
}}

/* 7. HERO VE BÖLÜM KARTLARI */
.hero {{
    padding: 1.7rem 1.4rem;
    border: 1.5px solid {v["hero_border"]};
    border-radius: 22px;
    background: {v["hero_bg"]};
    text-align: center;
    margin-top: 0.3rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 12px 32px -12px rgba(0, 0, 0, 0.3);
}}
.hero h1 {{
    font-size: clamp(1.85rem, 5vw, 2.75rem);
    margin-bottom: .35rem;
    color: {v["hero_title"]} !important;
    font-weight: 900;
    letter-spacing: -0.5px;
}}
.hero p {{
    color: {v["hero_sub"]} !important;
    font-size: clamp(0.92rem, 2.5vw, 1.08rem);
    margin-bottom: 0.25rem;
    font-weight: 500;
}}
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {v["section_bg"]} !important;
    border: 1.5px solid {v["section_border"]} !important;
    border-radius: 18px !important;
    padding: 1.2rem !important;
    margin-bottom: 1.15rem !important;
    box-shadow: 0 8px 24px -12px rgba(0, 0, 0, 0.22) !important;
}}
div[data-testid="stDataFrame"] {{
    border: 1px solid {v["df_border"]};
    border-radius: 12px;
    overflow: hidden;
}}

/* 8. BUTONLAR */
.stButton button[kind="primary"],
.stButton button[kind="secondary"] {{
    border-radius: 10px !important;
    font-weight: 800 !important;
    min-height: 3.1rem !important;
    height: auto !important;
    padding: 0.55rem 0.9rem !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    line-height: 1.3 !important;
}}
.stButton button[kind="primary"] {{
    background: {v["primary_btn"]} !important;
    color: #ffffff !important;
    border: 0 !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}}
.stButton button[kind="primary"] p,
.stButton button[kind="primary"] span {{
    color: #ffffff !important;
    font-weight: 800 !important;
}}
.stButton button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px {v["primary_btn_shadow"]} !important;
}}
.stButton button[kind="secondary"] {{
    background: {v["secondary_btn_bg"]} !important;
    border: 1.5px solid {v["secondary_btn_border"]} !important;
    color: {v["secondary_btn_text"]} !important;
}}
.stButton button[kind="secondary"] p,
.stButton button[kind="secondary"] span {{
    color: {v["secondary_btn_text"]} !important;
    font-weight: 800 !important;
    opacity: 1 !important;
}}

div[data-testid="stProgress"] > div > div > div > div {{
    background: linear-gradient(90deg, #d97706, #10b981) !important;
}}

/* 9. SORU KARTI ANİMASYONLARI VE MOBİL UYUMLU FLEX YAPISI */
@keyframes cardFlipGlowEven {{
    0% {{
        opacity: 0;
        transform: translateY(18px) scale(0.96);
        box-shadow: 0 0 32px {v["glow_1"]};
        border-color: {v["glow_border_1"]};
    }}
    100% {{
        opacity: 1;
        transform: translateY(0) scale(1);
        box-shadow: 0 10px 24px -10px {v["primary_btn_shadow"]};
        border-color: {v["card_border"]};
    }}
}}
@keyframes cardFlipGlowOdd {{
    0% {{
        opacity: 0;
        transform: translateX(20px) scale(0.96);
        box-shadow: 0 0 32px {v["glow_2"]};
        border-color: {v["glow_border_2"]};
    }}
    100% {{
        opacity: 1;
        transform: translateX(0) scale(1);
        box-shadow: 0 10px 24px -10px {v["primary_btn_shadow"]};
        border-color: {v["card_border"]};
    }}
}}
.animated-card-even {{
    animation: cardFlipGlowEven 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    border: 2px solid {v["card_border"]};
    border-radius: 16px;
    padding: 1.15rem;
    background: {v["card_bg"]};
    margin-bottom: 0.9rem;
}}
.animated-card-odd {{
    animation: cardFlipGlowOdd 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    border: 2px solid {v["card_border"]};
    border-radius: 16px;
    padding: 1.15rem;
    background: {v["card_bg"]};
    margin-bottom: 0.9rem;
}}
.timer-box {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    background: {v["timer_box_bg"]};
    border: 1px solid {v["timer_box_border"]};
    border-radius: 12px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.8rem;
}}
.timer-header-left {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}}
.timer-title {{
    font-weight: 800;
    font-size: 1.05rem;
    color: {v["text_primary"]} !important;
}}
.new-question-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: {v["pill_bg"]};
    color: #ffffff !important;
    font-size: 0.76rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
    box-shadow: 0 0 10px {v["pill_shadow"]};
}}
.timer-badge {{
    font-weight: 800;
    font-size: 0.98rem;
    padding: 4px 11px;
    border-radius: 8px;
    white-space: nowrap;
}}
.timer-ok {{
    background: rgba(16, 185, 129, 0.22);
    color: #10b981 !important;
    border: 1.5px solid #10b981;
}}
.timer-warn {{
    background: rgba(245, 158, 11, 0.22);
    color: #f59e0b !important;
    border: 1.5px solid #f59e0b;
}}
.timer-danger {{
    background: rgba(239, 68, 68, 0.25);
    color: #ef4444 !important;
    border: 1.5px solid #ef4444;
}}
.data-field-box {{
    background: {v["field_box_bg"]};
    border: 1px solid {v["field_box_border"]};
    border-radius: 10px;
    padding: 0.75rem 0.95rem;
}}
.data-field-row {{
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    padding: 0.42rem 0;
    border-bottom: 1px dashed {v["field_row_border"]};
    font-size: 0.98rem;
}}
.data-field-row:last-child {{
    border-bottom: none;
}}
.data-label {{
    color: {v["field_label"]} !important;
    font-weight: 700;
}}
.data-value {{
    color: {v["field_val_text"]} !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 700;
    white-space: pre-wrap;
    word-break: break-word;
    background: {v["field_val_bg"]};
    padding: 3px 10px;
    border-radius: 6px;
    border: 1px solid {v["field_val_border"]};
    max-width: 100%;
}}
.inspect-banner {{
    background: {v["inspect_bg"]};
    border: 2px solid {v["inspect_border"]};
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1rem;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    box-shadow: 0 10px 25px {v["primary_btn_shadow"]};
}}
.inspect-title {{
    font-size: 1.02rem;
    font-weight: 800;
    color: {v["inspect_title"]} !important;
}}
.inspect-sub {{
    font-size: 0.9rem;
    color: {v["text_secondary"]} !important;
}}

/* Özel soru başlık kartları (Her ekranda ve her temada %100 net ve kontrastlı) */
.custom-field-label,
span.custom-field-label,
div.custom-field-label,
div[data-testid="stMarkdownContainer"] .custom-field-label,
div[data-testid="stMarkdownContainer"] span.custom-field-label,
div[data-testid="stMarkdownContainer"] div.custom-field-label,
div[role="dialog"] .custom-field-label,
div[data-testid="stDialog"] .custom-field-label {{
    color: {"#f59e0b" if theme_mode == "dark" else "#9a3412"} !important;
    -webkit-text-fill-color: {"#f59e0b" if theme_mode == "dark" else "#9a3412"} !important;
    background: {"linear-gradient(135deg, rgba(245, 158, 11, 0.20), rgba(234, 88, 12, 0.14))" if theme_mode == "dark" else "linear-gradient(135deg, #fffbeb, #fef3c7)"} !important;
    border: 1.5px solid {"#d97706" if theme_mode == "dark" else "#ea580c"} !important;
    border-radius: 10px !important;
    padding: 8px 14px !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
    display: block !important;
    margin-bottom: 0.5rem !important;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12) !important;
    line-height: 1.4 !important;
    letter-spacing: 0.2px !important;
    box-sizing: border-box !important;
}}
.custom-warning-banner {{
    background: {v["alert_bg"]} !important;
    border: 1.5px solid {v["alert_border"]} !important;
    color: {v["alert_text"]} !important;
    padding: 0.75rem 1rem !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    margin-top: 0.5rem !important;
    margin-bottom: 0.75rem !important;
}}

/* 10. MOBİL EKRANLAR İÇİN ÖZEL MEDYA SORGULARI (@media max-width: 768px) */
@media (max-width: 768px) {{
    .block-container {{
        padding-top: 2.8rem !important;
        padding-left: 0.65rem !important;
        padding-right: 0.65rem !important;
        padding-bottom: 2.5rem !important;
    }}
    .hero {{
        padding: 1.15rem 0.85rem !important;
        border-radius: 16px !important;
        margin-bottom: 0.85rem !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        padding: 0.85rem !important;
        border-radius: 14px !important;
    }}
    div[role="dialog"] {{
        width: 98vw !important;
        max-width: 98vw !important;
        margin: 0.25rem !important;
        padding: 0.5rem !important;
        border-radius: 14px !important;
    }}
    .animated-card-even,
    .animated-card-odd {{
        padding: 0.85rem !important;
        border-radius: 12px !important;
    }}
    .timer-box {{
        padding: 0.5rem 0.65rem !important;
    }}
    .timer-title {{
        font-size: 0.95rem !important;
    }}
    .new-question-pill {{
        font-size: 0.7rem !important;
        padding: 2px 8px !important;
    }}
    .timer-badge {{
        font-size: 0.88rem !important;
        padding: 3px 8px !important;
    }}
    .data-field-box {{
        padding: 0.55rem 0.7rem !important;
    }}
    .data-field-row {{
        font-size: 0.9rem !important;
        padding: 0.35rem 0 !important;
    }}
    div[data-testid="stMetric"] {{
        padding: 0.75rem 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }}
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {{
        font-size: 1.35rem !important;
    }}
}}
</style>
"""


init_db()

# Oturum durumu (Session State) başlangıç değerleri
if "quiz_started" not in st.session_state:
    st.session_state["quiz_started"] = False
if "current_index" not in st.session_state:
    st.session_state["current_index"] = 0
if "user_answers" not in st.session_state:
    st.session_state["user_answers"] = {}
if "show_result" not in st.session_state:
    st.session_state["show_result"] = False
if "question_start_time" not in st.session_state:
    st.session_state["question_start_time"] = time.time()
if "inspect_dataset" not in st.session_state:
    st.session_state["inspect_dataset"] = False
if "paused_remaining" not in st.session_state:
    st.session_state["paused_remaining"] = QUESTION_TIME_LIMIT
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"
if "name_locked" not in st.session_state:
    st.session_state["name_locked"] = False
if "locked_player_name" not in st.session_state:
    st.session_state["locked_player_name"] = ""
if "attempt_completed" not in st.session_state:
    st.session_state["attempt_completed"] = False
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
if "admin_pin_error" not in st.session_state:
    st.session_state["admin_pin_error"] = False
if "selection_warning" not in st.session_state:
    st.session_state["selection_warning"] = False

# Tema CSS'ini uygula
st.markdown(build_theme_css(st.session_state["theme_mode"]), unsafe_allow_html=True)

# Mobilde selectbox seçimlerinde sanal klavyenin açılmasını engelleyen istemci koruma betiği
components.html(
    """
    <script>
    function preventMobileKeyboards() {
        try {
            const doc = window.parent.document;
            const selects = doc.querySelectorAll('div[data-baseweb="select"] input, input[role="combobox"], [data-testid="stSelectbox"] input');
            selects.forEach(input => {
                if (input.getAttribute('inputmode') !== 'none') {
                    input.setAttribute('inputmode', 'none');
                    input.setAttribute('readonly', 'true');
                }
            });
        } catch (e) {}
    }
    preventMobileKeyboards();
    setInterval(preventMobileKeyboards, 400);
    </script>
    """,
    height=0,
    width=0,
)

# 0. Hero Banner
st.markdown("""
<div class="hero">
    <h1>🕵️ VERİ AVI</h1>
    <p>Veri temizleme ve dönüştürme görevine hazır mısın?</p>
    <p>Tabloyu incele · Çapraz hataları yakala · Her kaydı 45 saniye içinde analiz et</p>
</div>
""", unsafe_allow_html=True)

# Tema Seçim Çubuğu
with st.container(border=True):
    bar_col_title, bar_col_dark, bar_col_light = st.columns([4.8, 1.6, 1.6], vertical_alignment="center")
    with bar_col_title:
        aktif_tema_adi = (
            "🌙 Koyu Tema (Obsidyen & Kehribar)"
            if st.session_state["theme_mode"] == "dark"
            else "☀️ Açık Tema (Krem & Bakır)"
        )
        st.write(f"🎨 **Görünüm Modu:** {aktif_tema_adi}")
    with bar_col_dark:
        if st.button(
            "🌙 Koyu Tema",
            type="primary" if st.session_state["theme_mode"] == "dark" else "secondary",
            use_container_width=True,
            key="btn_set_dark_theme"
        ):
            if st.session_state["theme_mode"] != "dark":
                st.session_state["theme_mode"] = "dark"
                st.rerun()
    with bar_col_light:
        if st.button(
            "☀️ Açık Tema",
            type="primary" if st.session_state["theme_mode"] == "light" else "secondary",
            use_container_width=True,
            key="btn_set_light_theme"
        ):
            if st.session_state["theme_mode"] != "light":
                st.session_state["theme_mode"] = "light"
                st.rerun()

# 1. Oyuncu bilgileri (İsim yazılıp Enter'landığında sayfa yenilenene kadar kilitlenir)
with st.container(border=True):
    st.subheader("👤 1. Oyuncu Bilgileri")

    full_name_raw = st.text_input(
        "Ad Soyad (Yalnızca harf giriniz ve onaylamak için Enter'a basınız)",
        placeholder="Örn. Ayşe Yılmaz",
        key="full_name_input",
        disabled=(
            st.session_state["name_locked"]
            or st.session_state["quiz_started"]
            or st.session_state["attempt_completed"]
        ),
        on_change=handle_name_entry
    )

    if st.session_state["name_locked"]:
        player_name = st.session_state["locked_player_name"]
        valid_name = True
        formatted_or_error = player_name
        st.success(
            f"🔒 Katılımcı kaydı kilitlendi: **{player_name}** — "
            "Sayfa yenilenene kadar bu oturumda farklı bir isimle yeni kayıt açılamaz."
        )
    else:
        cleaned_input = clean_letters_and_spaces(full_name_raw)
        if unicodedata.normalize("NFC", full_name_raw) != cleaned_input:
            st.warning("⚠️ Bu alana yalnızca harf ve boşluk girilebilir! Rakam ve özel karakterler otomatik olarak kaldırıldı.")

        valid_name, formatted_or_error = validate_full_name(cleaned_input)

        if cleaned_input.strip():
            if valid_name:
                player_name = formatted_or_error
                st.session_state["locked_player_name"] = player_name
                st.session_state["name_locked"] = True
                st.rerun()
            else:
                player_name = ""
                st.warning(formatted_or_error)
        else:
            player_name = ""
            if st.session_state.get("non_letter_warn"):
                st.warning("⚠️ Bu alana yalnızca harf ve boşluk girilebilir! Rakam ve özel karakterler kabul edilmemektedir.")
            st.caption("Adınızı ve soyadınızı yazıp **Enter** tuşuna bastığınızda kaydınız bu oturum için sabitlenir.")

# 2. Büyük veri tablosu (Ana ekranda ortada durur, "Seti İncele" dendiğinde buraya dönülür)
with st.container(border=True):
    st.subheader("📋 2. Öğrenci Veri Tablosu — 25 Kayıt")

    # Eğer oyuncu "Seti İncele" butonuna basarak pop-up'ı geçici olarak kapattıysa bilgilendirme ve geri dönüş butonu göster
    if st.session_state["quiz_started"] and st.session_state["inspect_dataset"]:
        idx_now = st.session_state["current_index"]
        row_now = DATA[idx_now]["ID"]
        st.markdown(
            f"""
            <div class="inspect-banner">
                <div>
                    <span class="inspect-title">
                        🔍 Veri Seti İnceleme Modu (Kayıt #{row_now} üzerinde çalışıyorsun)
                    </span><br/>
                    <span class="inspect-sub">
                        Tabloyu inceledikten sonra aşağıdaki butona tıklayarak kaldığın soruya (Kayıt #{row_now}) devam edebilirsin.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            f"🔙 Seti Kapat ve Kayıt #{row_now} Sorusuna Devam Et",
            type="primary",
            use_container_width=True,
            key="resume_quiz_top_btn"
        ):
            st.session_state["inspect_dataset"] = False
            st.session_state["question_start_time"] = time.time() - (
                QUESTION_TIME_LIMIT - st.session_state.get("paused_remaining", QUESTION_TIME_LIMIT)
            )
            st.rerun()

    st.write(
        "Aşağıdaki tabloyu dikkatlice inceleyin. Bazı sorunlar **tek bir satıra bakarak anlaşılamaz**; "
        "aynı **Öğrenci Numarasının** farklı bir kişide kullanılması, **mükerrer satırlar**, "
        "**aynı isimli farklı öğrenciler** veya **farklı not ölçekleri (0-1 oranı, 4'lük sistem, harf notu)** için tabloyu bütünsel incelemeniz gerekir."
    )

    display_rows = []
    for row in DATA:
        display_rows.append({
            "ID": row["ID"],
            "Öğrenci No": format_raw_cell(row["Öğrenci No"], "Öğrenci No"),
            "Ad Soyad": format_raw_cell(row["Ad Soyad"], "Ad Soyad"),
            "Yaş": format_raw_cell(row["Yaş"], "Yaş"),
            "Bölüm": format_raw_cell(row["Bölüm"], "Bölüm"),
            "Not": format_raw_cell(row["Not"], "Not"),
        })

    display_df = pd.DataFrame(display_rows)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "ID": st.column_config.NumberColumn("Kayıt No", width="small"),
            "Öğrenci No": st.column_config.TextColumn("Öğrenci No", width="small"),
            "Ad Soyad": st.column_config.TextColumn("Ad Soyad", width="medium"),
            "Yaş": st.column_config.TextColumn("Yaş", width="small"),
            "Bölüm": st.column_config.TextColumn("Bölüm", width="medium"),
            "Not": st.column_config.TextColumn("Sınav Notu", width="small"),
        }
    )

    if st.session_state["quiz_started"] and st.session_state["inspect_dataset"]:
        idx_now = st.session_state["current_index"]
        row_now = DATA[idx_now]["ID"]
        if st.button(
            f"🔙 Seti Kapat ve Kayıt #{row_now} Sorusuna Devam Et",
            type="primary",
            use_container_width=True,
            key="resume_quiz_bottom_btn"
        ):
            st.session_state["inspect_dataset"] = False
            st.session_state["question_start_time"] = time.time() - (
                QUESTION_TIME_LIMIT - st.session_state.get("paused_remaining", QUESTION_TIME_LIMIT)
            )
            st.rerun()


# Pop-up (Modal Dialog) içinde çalışan 45 saniye süreli ve direkt kart animasyonlu soru içeriği
@st.fragment(run_every=1.0)
def render_popup_quiz_body(current_player_name: str):
    # Sınav bittiyse fragment içinde beklemeyi kesip doğrudan tüm uygulamayı yenile
    if not st.session_state.get("quiz_started", False) or st.session_state.get("show_result", False):
        st.rerun(scope="app")
        return

    total_cards = len(DATA)
    idx = st.session_state["current_index"]
    current_row = DATA[idx]
    row_id = current_row["ID"]

    # Geçen süreyi hesapla
    elapsed = int(time.time() - st.session_state["question_start_time"])
    remaining = max(0, QUESTION_TIME_LIMIT - elapsed)

    # 45 saniye dolduysa otomatik olarak sıradaki soruya (veya son soruysa sonuç/liderlik ekranına) geç
    if remaining <= 0:
        finished = advance_to_next_question(current_player_name, allow_unselected=True)
        if finished:
            st.rerun(scope="app")
        else:
            st.rerun()
        return

    # İlerleme çubuğu
    progress_ratio = (idx + 1) / total_cards
    st.progress(progress_ratio, text=f"Soru İlerlemesi: {idx + 1} / {total_cards}")

    # Süre rengi belirleme
    if remaining > 20:
        timer_cls = "timer-ok"
    elif remaining > 10:
        timer_cls = "timer-warn"
    else:
        timer_cls = "timer-danger"

    # Daha önce bu kart için seçim yapıldıysa varsayılan olarak getir (Yoksa PLACEHOLDER gelir -> rastgele tıklama 0 puan alır)
    prev_problem, prev_action = st.session_state["user_answers"].get(
        row_id, (PLACEHOLDER_OPTION, PLACEHOLDER_OPTION)
    )
    prob_index = PROBLEM_OPTIONS.index(prev_problem) if prev_problem in PROBLEM_OPTIONS else 0
    act_index = ACTION_OPTIONS.index(prev_action) if prev_action in ACTION_OPTIONS else 0

    raw_std_no = format_raw_cell(current_row["Öğrenci No"], "Öğrenci No", for_html=True)
    raw_name = format_raw_cell(current_row["Ad Soyad"], "Ad Soyad", for_html=True)
    raw_age = format_raw_cell(current_row["Yaş"], "Yaş", for_html=True)
    raw_dept = format_raw_cell(current_row["Bölüm"], "Bölüm", for_html=True)
    raw_grade = format_raw_cell(current_row["Not"], "Not", for_html=True)

    anim_class = "animated-card-even" if idx % 2 == 0 else "animated-card-odd"

    st.markdown(
        f"""
        <div class="{anim_class}" id="record-card-{row_id}-{idx}">
            <div class="timer-box">
                <div class="timer-header-left">
                    <span class="timer-title">📌 Kayıt #{row_id}</span>
                    <span class="new-question-pill">✨ Soru {idx + 1}/{total_cards}</span>
                </div>
                <span class="timer-badge {timer_cls}">⏳ {remaining} sn</span>
            </div>
            <div class="data-field-box">
                <div class="data-field-row">
                    <span class="data-label">Kayıt No:</span>
                    <span class="data-value">#{row_id}</span>
                </div>
                <div class="data-field-row">
                    <span class="data-label">Öğrenci No:</span>
                    <span class="data-value">{raw_std_no}</span>
                </div>
                <div class="data-field-row">
                    <span class="data-label">Ad Soyad:</span>
                    <span class="data-value">{raw_name}</span>
                </div>
                <div class="data-field-row">
                    <span class="data-label">Yaş:</span>
                    <span class="data-value">{raw_age}</span>
                </div>
                <div class="data-field-row">
                    <span class="data-label">Bölüm:</span>
                    <span class="data-value">{raw_dept}</span>
                </div>
                <div class="data-field-row">
                    <span class="data-label">Sınav Notu:</span>
                    <span class="data-value">{raw_grade}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        st.markdown('<div class="custom-field-label">1️⃣ Tespit edilen sorun / dönüşüm ihtiyacı</div>', unsafe_allow_html=True)
        chosen_problem = st.selectbox(
            "1️⃣ Tespit edilen sorun / dönüşüm ihtiyacı",
            PROBLEM_OPTIONS,
            index=prob_index,
            key=f"step_problem_{row_id}",
            filter_mode=None,
            label_visibility="collapsed"
        )
    with c_sel2:
        st.markdown('<div class="custom-field-label">2️⃣ Uygulanacak temizleme / dönüştürme işlemi</div>', unsafe_allow_html=True)
        chosen_action = st.selectbox(
            "2️⃣ Uygulanacak temizleme / dönüştürme işlemi",
            ACTION_OPTIONS,
            index=act_index,
            key=f"step_action_{row_id}",
            filter_mode=None,
            label_visibility="collapsed"
        )

    # Seçimi anlık olarak oturumda sakla
    st.session_state["user_answers"][row_id] = (chosen_problem, chosen_action)

    if st.session_state.get("selection_warning"):
        st.markdown(
            '<div class="custom-warning-banner">'
            '⚠️ Sonraki soruya geçmeden önce lütfen hem <strong>Sorun Türünü</strong> hem de <strong>Uygulanacak İşlemi</strong> seçin!'
            '</div>',
            unsafe_allow_html=True
        )

    # Sol/Orta: İleri/Bitir butonu | Sağ Alt: Seti İncele butonu
    btn_col_next, btn_col_inspect = st.columns([2.1, 1.1])

    with btn_col_next:
        if idx < total_cards - 1:
            if st.button(
                "İleri (Sonraki Kayıt) ➡️",
                type="primary",
                use_container_width=True,
                key=f"next_btn_{row_id}"
            ):
                advance_to_next_question(current_player_name, allow_unselected=False)
                st.rerun()
        else:
            if st.button(
                "🏁 Cevapları Tamamla ve Puanımı Hesapla",
                type="primary",
                use_container_width=True,
                key=f"finish_btn_{row_id}"
            ):
                finished = advance_to_next_question(current_player_name, allow_unselected=False)
                if finished:
                    st.rerun(scope="app")
                else:
                    st.rerun()

    with btn_col_inspect:
        if st.button(
            "📋 Seti İncele",
            type="secondary",
            use_container_width=True,
            key=f"inspect_btn_{row_id}"
        ):
            # Kalan süreyi dondurup ana ekrandaki veri setini aç
            st.session_state["selection_warning"] = False
            st.session_state["paused_remaining"] = remaining
            st.session_state["inspect_dataset"] = True
            st.rerun(scope="app")


@st.dialog("🕵️ Veri Avı — Kayıt Analizi", width="large")
def open_quiz_modal(current_player_name: str):
    render_popup_quiz_body(current_player_name)


# 3. Sorun Tespiti ve Çözüm Seçimi Bölümü
with st.container(border=True):
    st.subheader("🔎 3. Sorun Tespiti ve Çözüm Seçimi")

    if not st.session_state["quiz_started"] and not st.session_state["show_result"]:
        st.write(
            "Yukarıdaki veri tablosunu incelediysen **Veri Avına Başla** butonuna tıkladığında sorular **ekranda pop-up pencere** olarak açılır. "
            "Her soru için **45 saniye** süren vardır; mükerrer kayıtları veya Öğrenci No çakışmalarını kontrol etmek için sağ alttaki **📋 Seti İncele** "
            "butonuna basarak ana ekrandaki veri tablosuna bakabilir ve kaldığın yerden devam edebilirsin."
        )
        if st.button("🚀 Veri Avına Başla", type="primary", use_container_width=True):
            if not valid_name:
                st.error(formatted_or_error)
            else:
                st.session_state["name_locked"] = True
                st.session_state["locked_player_name"] = player_name
                st.session_state["quiz_started"] = True
                st.session_state["inspect_dataset"] = False
                st.session_state["selection_warning"] = False
                st.session_state["current_index"] = 0
                st.session_state["user_answers"] = {}
                st.session_state["show_result"] = False
                st.session_state["question_start_time"] = time.time()
                st.session_state["paused_remaining"] = QUESTION_TIME_LIMIT
                st.rerun()

    elif st.session_state["quiz_started"] and not st.session_state["show_result"]:
        idx_now = st.session_state["current_index"]
        row_now = DATA[idx_now]["ID"]
        if st.session_state["inspect_dataset"]:
            st.info(
                f"📌 Şu anda **Kayıt #{row_now}** sorusu için veri setini inceliyorsun. "
                "Yukarıdaki tablodan kontrolünü yaptıktan sonra aşağıdaki butona basarak soru penceresini tekrar açabilirsin."
            )
            if st.button(
                f"🔎 Kayıt #{row_now} Soru Penceresini Tekrar Aç",
                type="primary",
                use_container_width=True,
                key="reopen_modal_section_btn"
            ):
                st.session_state["inspect_dataset"] = False
                st.session_state["question_start_time"] = time.time() - (
                    QUESTION_TIME_LIMIT - st.session_state.get("paused_remaining", QUESTION_TIME_LIMIT)
                )
                st.rerun()
        else:
            st.caption(f"Soru penceresi açık (Kayıt #{row_now}). Eğer pencereyi kapattıysan aşağıdan tekrar açabilirsin:")
            if st.button(
                f"🔎 Kayıt #{row_now} Soru Penceresini Göster",
                type="primary",
                use_container_width=True,
                key="show_modal_fallback_btn"
            ):
                st.rerun()
            open_quiz_modal(player_name)

    # 4. Sonuç Karnesi (Sayfa yenilenene kadar tekrar kayıt veya yeni deneme başlatılamaz)
    if st.session_state.get("show_result"):
        result = st.session_state["last_result"]

        st.subheader(f"🏁 Sonuç Karnesi: {result['name']}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Puan", f"{result['score']} / {result['max_score']}")
        m2.metric("Başarı Oranı", f"%{result['percent']}")
        m3.metric(
            "Seviye",
            "🌟 Uzman Veri Avcısı!" if result["percent"] >= 88
            else ("👍 İyi İş Çıkardın!" if result["percent"] >= 60 else "🔍 Tekrar İncelemelisin")
        )

        st.progress(result["percent"] / 100)
        st.dataframe(
            pd.DataFrame(result["details"]),
            use_container_width=True,
            hide_index=True
        )

        if result["percent"] >= 88:
            st.success("Tebrikler! Veri temizleme, dönüştürme ve çapraz tablo doğrulama görevlerini harika bir şekilde analiz ettin.")
        elif result["percent"] >= 60:
            st.info("Güzel bir performans! Hatalı yaptığın kayıtların yanındaki detaylı açıklamaları inceleyerek eksiklerini tamamlayabilirsin.")
        else:
            st.warning("Tablodaki detaylı açıklamaları inceleyip veri sorunlarını tekrar gözden geçirerek yeniden deneyebilirsin.")

        st.info("🔒 Bu oturum için sınav hakkınızı tamamladınız. Liderlik tablosundaki sıranızı aşağıdan görebilirsiniz.")

# 5. Liderlik tablosu ve Veritabanı Yönetimi
with st.container(border=True):
    st.subheader("🏆 4. Liderlik Tablosu")
    st.write("Sınıftaki en yüksek puan alan ilk 40 katılımcı aşağıda listelenir.")

    leaderboard = get_leaderboard()

    if leaderboard.empty:
        st.caption("Henüz kayıtlı bir sonuç yok. İlk puanı kaydeden sen ol!")
    else:
        display_lb = leaderboard.copy()
        display_lb["Başarı (%)"] = display_lb["Başarı (%)"].map(
            lambda x: f"%{x:.1f}"
        )
        st.dataframe(
            display_lb,
            use_container_width=True,
            hide_index=True,
            height=420
        )

    # Admin Veritabanı Temizleme Paneli (İncele / Inspect Element Korumalı)
    with st.expander("🛠️ Admin Paneli — Veritabanı (Skor) Kayıtlarını Yönet"):
        if not st.session_state["admin_authenticated"]:
            st.caption("Veritabanı işlemlerine erişmek için admin şifresini girip **Enter** tuşuna basın.")
            st.text_input(
                "Admin Şifresi",
                type="password",
                placeholder="Şifreyi girip Enter'a basınız",
                key="admin_pin_field",
                on_change=verify_admin_pin
            )
            if st.session_state.get("admin_pin_error"):
                st.error("❌ Hatalı admin şifresi!")
        else:
            top_adm1, top_adm2 = st.columns([3, 1], vertical_alignment="center")
            with top_adm1:
                st.success("🔓 Admin oturumu açık (Şifre kutusu güvenlik için gizlendi ve temizlendi).")
            with top_adm2:
                if st.button("🔒 Paneli Kilitle", type="secondary", use_container_width=True):
                    st.session_state["admin_authenticated"] = False
                    st.rerun()

            if st.button("🗑️ Tüm Liderlik Tablosunu Sıfırla", type="primary", use_container_width=True):
                clear_all_results()
                st.success("✅ Veritabanındaki tüm skor kayıtları başarıyla silindi!")
                time.sleep(0.5)
                st.rerun()

            if not leaderboard.empty:
                st.write("---")
                st.write("**Tekil Kayıt Sil (İsteğe Bağlı):**")
                del_col1, del_col2 = st.columns([3, 1], vertical_alignment="bottom")
                options_list = [
                    f"{row['Ad Soyad']} — {row['Puan']} Puan ({row['Tarih']})"
                    for _, row in leaderboard.iterrows()
                ]
                with del_col1:
                    selected_rec = st.selectbox("Silinecek Kaydı Seçin", options_list, key="single_del_select", filter_mode=None)
                with del_col2:
                    if st.button("❌ Seçili Kaydı Sil", type="secondary", use_container_width=True):
                        sel_idx = options_list.index(selected_rec)
                        target_row = leaderboard.iloc[sel_idx]
                        delete_single_result(target_row["Ad Soyad"], target_row["Tarih"])
                        st.success(f"✅ '{target_row['Ad Soyad']}' kaydı silindi!")
                        time.sleep(0.4)
                        st.rerun()

st.caption(
    "Veri Avı · Veri Madenciliği ve Veri Kalitesi eğitimi için interaktif uygulama. "
    "Sonuçlar yerel veri_avi.db veritabanında saklanır."
)