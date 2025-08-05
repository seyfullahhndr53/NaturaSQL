# 🌿 NaturaSQL

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

Doğal dilden SQL'e dönüştürme uygulaması. PyQt6 ve Ollama AI ile geliştirildi.

## ✨ Özellikler

- 🗃️ **SQLite ve JSON** dosya desteği (tekil ve çoklu)
- 🤖 **Ollama AI** entegrasyonu (offline)
- 🔒 **SQL Injection** koruması
- 🎨 **Modern arayüz** (Dark/Light tema)
- 🌍 **Türkçe/İngilizce** dil desteği
- 📊 **Excel/JSON export** desteği
- 🎭 **Modern animasyonlar** ve loading göstergeleri
- 📝 **Sorgu geçmişi** sistemi (geliştiriliyor)
- ⚡ **Performans izleme** (geliştiriliyor)

## 🚀 Kurulum

1. **Sanal ortam oluşturun ve aktif edin:**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   

2. **Gereksinimleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ollama'yı kurun ve modeli indirin:**
   ```bash
   ollama pull mistral
   ```

4. **Uygulamayı çalıştırın:**
   ```bash
   python main.py
   ```

## 📖 Kullanım

1. "Veri Yükle" ile dosyanızı seçin (SQLite/JSON - tekil veya çoklu)
2. Sol paneldeki metin kutusuna sorunuzu yazın (Türkçe/İngilizce)
3. "Sorguyu Çalıştır" butonuna basın
4. AI otomatik SQL oluşturur ve çalıştırır
5. Sonuçları sağ paneldeki tabloda görüntüleyin
6. "Araçlar" menüsünden Excel (.xlsx) veya JSON formatında export edin

## 🔒 Güvenlik

- Sadece SELECT sorguları çalışır
- SQL injection koruması
- Tehlikeli komutlar engellenir

## 👥 Geliştiriciler

Bu proje aşağıdaki kişiler tarafından geliştirilmiştir:

- **Seyfullah Hanedar** - Proje Yöneticisi
- **Claude (Anthropic)** - AI Geliştirici
- **Gemini (Google)** - AI Geliştirici

## 📝 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🔧 Teknik Detaylar

- **PyQt6** - Modern GUI framework
- **Ollama** - Local AI model çalıştırma  
- **Pandas** - Excel export işlemleri
- **openpyxl** - Excel dosya desteği
- **Python 3.8+** - Ana programlama dili

---