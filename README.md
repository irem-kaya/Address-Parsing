# address-hackathon
[CI](https://github.com/irem-kaya/address-hackathon/actions/workflows/ci.yml/badge.svg)

Adres verisi için **normalize**, **eşleştirme** (matching) ve **değerlendirme** pipeline’ı.  
Bu repo; EDA not defterleri, baseline modelleri, parametrik deneyler ve test altyapısını içerir.

---

## 📂 Proje Yapısı


> **Not:** GitHub boş klasörleri göstermediği için `data/`, `configs/`, `addresskit/` gibi klasörler `.gitkeep` ile saklanmıştır.

---

## ⚙️ Kurulum

```bash
# 1) Sanal ortam (önerilir)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 2) Bağımlılıklar
pip install -r requirements.txt
# Geliştirme araçları (pytest, pre-commit vb.)
pip install -r requirements-dev.txt
# Normalizasyon örneği
python -m addresskit.normalize \
  --input data/raw/train.csv \
  --output data/processed/train_norm.csv \
  --config configs/normalize.yaml

# Eşleştirme (matching) örneği
python -m addresskit.match \
  --left data/processed/a.csv \
  --right data/processed/b.csv \
  --out data/preds.csv \
  --config configs/match.yaml
