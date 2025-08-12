# Address Matching Pipeline – Mimari Rehber

Bu belge, adres eşleştirme/çözümleme projesinin dosya ve klasör yapısını, her parçanın **ne işe yaradığını** ve **neden gerekli** olduğunu açıklar. Amaç: Kaggle ve lokal ortamda **aynı kod tabanı** ile tekrar üretilebilir, modüler bir pipeline sağlamak.

## Dizin Ağacı (Özet)

```
address-hackathon/
├─ addresskit/
│  ├─ __init__.py
│  ├─ match.py                     # Eşleştirme CLI (INDEX/FUZZY), bloklama, unmatched çıktıları
│  ├─ preprocessing/
│  │  ├─ __init__.py
│  │  ├─ clean_text.py             # Metin normalizasyonu (normalize_text, TR-safe lower, cfg)
│  │  └─ run_normalize.py          # CLI: CSV in → CSV out (address_norm ekler)
│  ├─ matching/
│  │  ├─ __init__.py
│  │  ├─ blocking.py               # O(n²) patlamayı önlemek için il/ilçe (veya benzeri) bloklama
│  │  ├─ string_similarity.py      # (Ops.) Jaccard/Levenshtein/embedding benzerlikleri
│  │  └─ geo_distance.py           # (Ops.) Haversine (lat/lon ile coğrafi inceltme)
│  ├─ scoring/
│  │  ├─ __init__.py
│  │  └─ confidence.py             # (Ops.) text+geo skorlarından tek “confidence” üretimi
│  ├─ submission/
│  │  ├─ __init__.py
│  │  └─ build_submission.py       # (Ops.) Kaggle submission formatlayıcı
│  └─ utils/
│     ├─ __init__.py
│     ├─ io.py                     # Kaggle/lokal path yönetimi (tek noktadan)
│     └─ seeds.py                  # Deterministiklik (random/np seeds)
│
├─ configs/
│  ├─ normalize.yaml               # Normalizasyon kuralları (replace/regex/abbr/stopwords)
│  ├─ match.yaml                   # Eşleştirme ayarları (scorer/threshold/topk/block_by)
│  ├─ submission.yaml              # (Ops.) submission kolon ve sırası
│  └─ pipeline.yaml                # (Ops.) akış parametreleri (adım aç/kapa)
│
├─ data/
│  ├─ raw/                         # Giriş: orijinal CSV’ler (örn. left.csv, right.csv, train.csv)
│  ├─ interim/                     # Ara: normalize edilmiş CSV’ler (*_norm.csv)
│  ├─ processed/                   # Çıkış: match.csv, unmatched_*.csv, submission.csv
│  └─ external/                    # Sözlükler, posta kodu lookup gibi offline yardımcı veriler
│
├─ notebooks/
│  └─ 01_run_pipeline.ipynb        # Uçtan uca demo (okuma→normalize→match→çıktı)
│
├─ scripts/
│  └─ run_pipeline.py              # Notebook’suz aynı akış için giriş noktası (CLI/CI/CD)
│
├─ pyproject.toml / requirements.txt
├─ README.md
└─ README-ARCHITECTURE.md          # (bu dosya)
```

---

## Bileşenler ve “Neden?” Açıklamaları

### `addresskit/utils/io.py`

* **Ne yapar?** Kaggle’da `/kaggle/input`–`/kaggle/working`, lokalde `data/*` yollarını **otomatik** seçer.
* **Neden?** Kodunuzu ortamdan bağımsız kılar; dosya yolları için `if/else` yazmazsınız.

### `addresskit/utils/seeds.py`

* **Ne yapar?** `random` ve `numpy` için seed set eder.
* **Neden?** Skorlarınız tekrar üretilebilir olsun; özellikle farklı çalıştırmalarda küçük sapmaları azaltır.

### `addresskit/preprocessing/clean_text.py`

* **Ne yapar?** `normalize_text()` ile metni TR-güvenli lower, kısaltma açma, regex temizliği, noktalama, stopword, boşluk düzeltme vb. uygular.
* **Neden?** Adreslerin serbest metin varyasyonlarını ortak bir standarda indirerek eşleştirmeyi **kolaylaştırır ve hızlandırır**.

### `addresskit/preprocessing/run_normalize.py`

* **Ne yapar?** CLI ile CSV okur, `address_norm` alanını ekleyerek yazar.
* **Neden?** Notebook olmadan da “komutla” toplu normalizasyon yapmanı sağlar; CI/CD’de kullanışlıdır.

### `addresskit/match.py`

* **Ne yapar?** İki CSV’yi (sol/sağ) karşılaştırıp eşleşmelerin listesini üretir:

  * **MODE:** `index` (hızlı test) veya `fuzzy` (RapidFuzz)
  * **Bloklama:** `block_by` ile (örn. `["province","district"]`) O(n²) patlamayı azaltır
  * **Parametreler:** `scorer`, `threshold`, `topk`, `keep_best_per_right`
  * **Çıktılar:** `match.csv`, `unmatched_left.csv`, `unmatched_right.csv`
* **Neden?** Eşleştirme stratejisini **konfigürasyonla** yönetebilmek ve büyük veri üzerinde **ölçeklenebilir** olmak için.

### `addresskit/matching/*` (opsiyonel genişletmeler)

* `blocking.py`: Bloklama anahtarları (il/ilçe/posta kodu/mahalle…); hız ve doğruluk arasında denge.
* `string_similarity.py`: Alternatif metin benzerlikleri, TF-IDF/embedding tabanlı skorlar.
* `geo_distance.py`: Haversine ile coğrafi yakınlık → metin eşleşmesini coğrafyayla **incelet**.

### `addresskit/scoring/confidence.py` (ops.)

* **Ne yapar?** Text benzerliği + coğrafi yakınlığı tek bir **confidence** puanına indirger.
* **Neden?** Jüri/iş tarafı için karar eşiği belirleme ve **açıklanabilirlik**.

### `addresskit/submission/build_submission.py` (ops.)

* **Ne yapar?** Yarışmanın beklediği `submission.csv` kolon ve sırasını üretir (config’den okur).
* **Neden?** Kaggle aşamasında **format hatalarını** tek noktadan engeller.

### `configs/*.yaml`

* `normalize.yaml`: Temizlik kuralları. Varyasyonları buradan yönet (örn. `cd.`→`cadde`).
* `match.yaml`: Eşleştirme davranışı. `threshold`, `block_by`, `scorer`, `topk` gibi ayarlar.
* `submission.yaml`: Çıktı kolon adları/sırası. Yarışma formatı değişse bile kodu **değiştirmeden** uyum sağlarsın.
* **Neden?** Parametreleri koda gömmek yerine **config** ile yönetmek deneme–yanılmayı hızlandırır.

### `data/` (veri yaşam döngüsü)

* `raw/` → **giriş** (değiştirilmez)
* `interim/` → **ara** (normalize vb. çıktılar; kontrol ve debug için tutulur)
* `processed/` → **final** (match/submission; raporlama ve teslim için kullanılır)
* `external/` → **offline yardımcı** (kısaltma sözlükleri, posta kodu lookup). Kaggle’da **internet yok** varsayımıyla tasarlanır.

### `notebooks/01_run_pipeline.ipynb`

* **Ne yapar?** Uçtan uca örnek: oku → normalize → match → çıktı.
* **Neden?** Hızlı deneme/inceleme; takım içi **paylaşılabilir** bir yürütme ortamı.

### `scripts/run_pipeline.py`

* **Ne yapar?** Notebook’suz aynı akış; CI/CD ve otomasyon için tek komut.
* **Neden?** Yarışma sürecinde script tabanlı çalışmak daha güvenilir ve tekrar üretilebilir.

---

## Çalıştırma Akışı (Kısa Rehber)

1. **Veriyi yerleştir**
   `data/raw/left.csv`, `data/raw/right.csv` (ID ve adres kolonları olsun; `address_raw` yeterli)

2. **Normalize et**

```bash
python -m addresskit.preprocessing.run_normalize \
  --input data/raw/left.csv \
  --output data/interim/left_norm.csv \
  --config configs/normalize.yaml

python -m addresskit.preprocessing.run_normalize \
  --input data/raw/right.csv \
  --output data/interim/right_norm.csv \
  --config configs/normalize.yaml
```

3. **Eşleştir**

```bash
python -m addresskit.match \
  --left data/interim/left_norm.csv \
  --right data/interim/right_norm.csv \
  --out data/processed/match.csv \
  --config configs/match.yaml
```

Çıktılar:

* `data/processed/match.csv`
* `data/processed/unmatched_left.csv`
* `data/processed/unmatched_right.csv`

4. **(Ops.) Submission üret**

```bash
python -c "from addresskit.submission.build_submission import build_submission; import pandas as pd; import yaml; df=pd.read_csv('data/processed/match.csv'); print('submission hazirlik ornegi')"
```

---

## Kaggle vs Lokal – Önemli Notlar

* **Yol yönetimi** `addresskit/utils/io.py` ile otomatik. Notebook’ta `/kaggle/input` ve `/kaggle/working` kullanılacak.
* **İnternet yok** kabulüyle tasarla: Dış API (geocoding) çağrılarını opsiyonel/kapalı tut.
* **Kaynak sınırları**: O(n²) maliyetli eşleştirmeyi **bloklama** ile daralt. Gerekirse `rapidfuzz.process.cdist` ile vektörize et.

---

## En İyi Pratikler (Kritik)

* **Deterministiklik:** `set_seeds(42)` çağır; notebook/script başına bir kez.
* **Config-tabanlılık:** eşikler, skorlayıcılar, bloklama kolonları **config’ten** gelsin.
* **Açıklanabilirlik:** `match.csv` içine `left_text/right_text/score` yaz; gerektiğinde demo/sunumda göster.
* **Veri bölümleri:** `raw → interim → processed` hattını bozma; ara dosyalar debug için hayat kurtarır.
* **Büyük veri:** Bloklama (province/district), gerekirse mahalle/posta kodu; yoksa n-gram/trigram bloklama düşün.

---

## Bağımlılıklar

* Python 3.9+
* `pandas`, `pyyaml`, `rapidfuzz`, (opsiyonel: `numpy`)
* (GPU gerekmez)

`requirements.txt` örneği:

```
pandas>=2.0.0
pyyaml>=6.0
rapidfuzz>=3.0.0
numpy>=1.24
```

---

## SSS (Kısa)

* **Adres kolonu adı farklıysa?** `run_normalize.py` otomatik bulur (öncelik `address_norm` → `address` → ilk string kolon).
* **Threshold 0–1 mi 0–100 mü?** İkisi de olur; 0–1 gelirse yüzdeye çevrilir.
* **Aynı sağ kayda çok eşleşme gelirse?** `keep_best_per_right: true` ile en iyi tek eş bırakılır.
* **Coğrafi filtre istersem?** `matching/geo_distance.py`’ı ekleyip `match.py` sonrası inceltme adımıyla kullan.

