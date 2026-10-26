# Veri Avı — Streamlit başlangıç projesi

## Kurulum
1. Bilgisayarında Python 3.10 veya üzeri kurulu olsun.
2. Bu klasörü aç ve terminal/Komut İstemi'nde klasöre gir.
3. Sanal ortam (isteğe bağlı ama önerilir):
   - Windows: `py -m venv .venv`
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
4. Paketleri kur:
   `python -m pip install -r requirements.txt`
5. Uygulamayı başlat:
   `python -m streamlit run app.py`

Tarayıcıda Streamlit'in verdiği yerel adres açılır (genellikle http://localhost:8501).

## İçerik
- Öğrenci ad-soyad girişi
- 10 soruluk veri temizleme ve dönüştürme testi
- Otomatik puan ve başarı yüzdesi
- SQLite üzerinde sonuç saklama
- Skor tablosu
- Hatalı örnek veri seti ve öğretmen cevapları

## Sınıfla paylaşma
Yerel çalıştırma yalnızca kendi bilgisayarında erişim sağlar. Sınıfın farklı cihazlardan bağlanması için uygulamayı Streamlit Community Cloud gibi bir barındırma hizmetine dağıtıp veritabanı saklama yöntemini çok kullanıcılı kullanım için gözden geçirmek gerekir. Yerel SQLite dosyası her barındırma ortamında kalıcı veri deposu olarak garanti edilmez.

## Not
Bu bir başlangıç prototipidir. Ad ve soyad verileri kaydedildiği için gerçek kullanımda gizlilik ve erişim izinlerini göz önünde bulundurun.
