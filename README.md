# Adres Ayrıştırma (Address Parsing) Hackathon Projesi

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![Status](https://img.shields.io/badge/Status-Geliştirme%20Aşamasında-yellow.svg)
![CI](https://github.com/irem-kaya/address-hackathon/actions/workflows/ci.yml/badge.svg)
![Container](https://img.shields.io/badge/container-GHCR-blue)

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

Bu projede, adres ayrıştırma problemini çözmek için farklı yaklaşımlar denenmiş ve en iyi sonuçları veren yöntemlerin birleşimi hedeflenmiştir. Kullanılan temel teknolojiler ve denenen yaklaşımlar aşağıda sıralanmıştır:

* **Python 3.9+:** Projenin ana programlama dilidir.
* **Pandas & NumPy:** Büyük veri setlerinin temizlenmesi, manipülasyonu ve analizi için temel kütüphaneler olarak kullanılmıştır.
* **Scikit-learn:** Makine öğrenmesi algoritmaları ve değerlendirme metrikleri için kullanılmıştır. Özellikle **BERT** modelinin çıktılarının sınıflandırılması ve model performansının ölçülmesi aşamalarında önemli rol oynamıştır.
* **Matplotlib & Seaborn:** Veri setinin ve model sonuçlarının görselleştirilmesi için kullanılmıştır. Özellikle modelin doğru ve yanlış tahminlerinin analizinde, veri dağılımlarını anlamada ve sonuçları raporlamada faydalı olmuştur.
* **Doğal Dil İşleme (NLP) Yaklaşımları:**
    * **Regex (Regular Expressions):** Basit ve belirgin kalıpları (örneğin, "no:", "apt:", "mah.") ayrıştırmak için ilk aşama olarak kullanılmıştır. Farklı kalıpların bir araya getirildiği bir **Regex Ensemble** yapısı denenmiştir.
    * **BERT Modelleri:** Daha karmaşık ve kalıp dışı adres metinlerini anlamak ve ayrıştırmak için çeşitli **BERT (Bidirectional Encoder Representations from Transformers)** modelleriyle denemeler yapılmıştır. Türkçe adres verileri üzerinde en iyi performansı verecek model arayışı, projenin kritik bir parçasını olmuştur. Bu modellerin eğitimi ve ince ayar (fine-tuning) süreçleri, projenin derinlemesine bir NLP çalışması olduğunu göstermektedir.

---
## 🚧 Karşılaşılan Zorluklar ve Öğrenilenler

* **Türkçe Adreslerin Standart Olmaması:** En büyük zorluk, "mahallesi" yerine "mah.", "apartmanı" yerine "apt." gibi kısaltmaların ve yazım hatalarının yaygın olmasıdır.
* **NLP Modelleri İçin Uygun Veri Seti Bulma:** Türkçe adresler için etiketlenmiş, kaliteli bir veri seti bulmak zorlayıcı olmuştur.
* **Regex ve NLP Entegrasyonu:** Farklı yaklaşımların (Regex ve BERT) bir arada kullanılarak daha sağlam (robust) bir çözüm oluşturulması teknik bir meydan okuma olmuştur.

---
## 📈 Projenin Mevcut Durumu ve Gelecek Adımlar

Proje şu anda temel adres bileşenlerini ayrıştırabilen bir prototip aşamasındadır. Gelecek adımlar şunları içerecektir:
* [ ] Daha büyük ve çeşitli adres verileriyle modelin performansını artırmak.
* [ ] Kullanıcı dostu bir API veya arayüz oluşturarak projenin pratik kullanımını sağlamak.
* [ ] Coğrafi koordinat verilerini (latitude, longitude) entegre ederek adresleri harita üzerinde görselleştirmek.

---
## 🚀 Kurulum ve Çalıştırma

1.  Bu depoyu klonlayın:
    `git clone [repo_adresiniz]`
2.  Gerekli kütüphaneleri yükleyin:
    `pip install -r requirements.txt`
3.  Projeyi çalıştırmak için:
    `python [ana_dosya_adınız].py`

---
## 🤝 Katkıda Bulunanlar

* [İrem Nur Kaya](https://github.com/irem-kaya)
* [Büşra Gümüşay](https://github.com/busragmsy)

