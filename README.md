# Adres Ayrıştırma (Address Parsing) Hackathon Projesi

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Status](https://img.shields.io/badge/Status-Geliştirme%20Aşamasında-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Bu proje, bir hackathon kapsamında geliştirilmiş olup, standart olmayan, serbest metin formatındaki Türkçe adres verilerini ayrıştırarak il, ilçe, mahalle gibi yapısal bileşenlere dönüştürmeyi hedeflemektedir.

---

## 📜 İçindekiler
- [Projenin Amacı ve Hedefi](#-projenin-amacı-ve-hedefi)
- [Kullanılan Teknolojiler](#-kullanılan-teknolojiler)
- [Karşılaşılan Zorluklar ve Öğrenilenler](#-karşılaşılan-zorluklar-ve-öğrenilenler)
- [Projenin Mevcut Durumu ve Gelecek Adımlar](#-projenin-mevcut-durumu-ve-gelecek-adımlar)
- [Kurulum ve Çalıştırma](#-kurulum-ve-çalıştırma)
- [Katkıda Bulunanlar](#-katkıda-bulunanlar)
- [Lisans](#-lisans)

---

## 🎯 Projenin Amacı ve Hedefi

Türkiye'deki adres verileri genellikle standart bir formattan yoksundur ve kullanıcılar tarafından serbest metin olarak girilir. Bu durum, adres verilerini analiz etmeyi, coğrafi bilgi sistemlerinde kullanmayı veya veritabanlarında tutarlı bir şekilde saklamayı zorlaştırır.

Bu projenin temel hedefi, aşağıdaki gibi dağınık bir adres metnini:
`"Örnek mah. Atatürk cad. no:12/3 daire:5 Şişli/İstanbul"`
yapısal hale getirerek şu bileşenlere ayırmaktır:
- **İl:** İstanbul
- **İlçe:** Şişli
- **Mahalle:** Örnek Mahallesi
- **Cadde/Sokak:** Atatürk Caddesi
- **Bina No:** 12/3
- **Daire No:** 5

---

## 💻 Kullanılan Teknolojiler
* **Python 3.9+**
* **Pandas:** Veri manipülasyonu ve analizi için.
* **NumPy:** Sayısal işlemler için.
* **re (Regular Expressions):** Metin içindeki desenleri bulma ve ayrıştırma için.
* **Jupyter Notebook:** Keşifsel veri analizi ve geliştirme süreci için.
* **[Varsa diğer kütüphaneler, örn: Scikit-learn, Matplotlib, vb.]**

---

## 🧗 Karşılaşılan Zorluklar ve Öğrenilenler

Bu proje, özellikle hackathon'un kısıtlı süresi içinde, metin işleme konusundaki birçok zorluğu deneyimlemek için harika bir fırsat sundu.

* **Türkçe Adres Yapısının Karmaşıklığı:** Türkçe adreslerdeki kısaltmalar (mah., cad., sk.), zorunlu olmayan alanlar ve bileşenlerin yer değiştirebilmesi, kural tabanlı (rule-based) bir sistem oluşturmayı zorlaştırdı.
* **Veri Kalitesi ve Temizleme:** Çalışılan veri setindeki yazım hataları, tutarsızlıklar ve eksik bilgiler, projenin önemli bir zamanının veri ön işleme adımlarına ayrılmasını gerektirdi. Bu süreç, bir veri bilimi projesinde harcanan zamanın büyük bir kısmının neden veri ön işleme olduğunu somut bir şekilde göstermiştir.
* **Hackathon Zaman Kısıtlaması:** Kısıtlı sürede, hedeflenen tüm özellikleri (örneğin makine öğrenmesi modeli entegrasyonu) tamamlamak mümkün olmadı. Bu deneyim, proje yönetimi ve kısıtlı sürede ulaşılabilir hedefler (MVP - Minimum Viable Product) belirlemenin önemini pekiştirdi.

---

## 🚀 Projenin Mevcut Durumu ve Gelecek Adımlar

**Mevcut Durum:**
Proje şu anki haliyle, adres metinlerindeki temel yazım hatalarını düzeltme, büyük/küçük harf standardizasyonu gibi temel temizlik adımlarını gerçekleştirmektedir. Ayrıca, il ve ilçe isimlerini bir referans listesiyle eşleştirerek adresin bu bileşenlerini başarıyla çıkarmaktadır.

**Gelecek Adımlar:**
Projeye devam edilmesi durumunda planlanan adımlar şunlardır:
* [ ] **Regex Kurallarını Geliştirme:** Mahalle, cadde, sokak ve numara bilgilerini daha yüksek doğrulukla çıkarmak için kapsamlı Regex desenleri oluşturmak.
* [ ] **Makine Öğrenmesi Yaklaşımı:** Özellikle karmaşık ve standart dışı adresler için Named Entity Recognition (NER) modellerini araştırmak ve eğitmek.
* [ ] **API Servisi:** Geliştirilen ayrıştırıcıyı bir Flask/FastAPI servisi üzerinden kullanılabilir hale getirmek.

---

## 🛠️ Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyebilirsiniz:

1.  **Depoyu klonlayın:**
    ```bash
    git clone [https://github.com/irem-kaya/address-hackathon.git](https://github.com/irem-kaya/address-hackathon.git)
    cd address-hackathon
    ```

2.  **Sanal ortam oluşturun ve aktif edin:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows için: venv\Scripts\activate
    ```

3.  **Gerekli kütüphaneleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Not: Henüz bir `requirements.txt` dosyanız yoksa, `pip freeze > requirements.txt` komutuyla oluşturabilirsiniz.)*

4.  **Jupyter Notebook'u çalıştırın:**
    ```bash
    jupyter notebook
    ```

---

## 👥 Katkıda Bulunanlar

* **[İrem Kaya](https://github.com/irem-kaya)** - Proje Geliştiricisi

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE.md) ile lisanslanmıştır.
