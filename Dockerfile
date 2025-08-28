# Dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# (pip'i güncelle)
RUN pip install --upgrade pip

# Bağımlılıklar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama
COPY . .
# Projene göre giriş komutunu güncelle
CMD ["python", "-c", "print('address-hackathon image OK')"]
# Örn: CMD ["python","-m","addresskit.cli.parse","--help"]
