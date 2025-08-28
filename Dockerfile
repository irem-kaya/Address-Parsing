FROM python:3.10-slim
WORKDIR /app

# Bağımlılıkları kur
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . /app

# Şimdilik basit bir komut; sonra projene göre değiştirirsin
CMD ["python", "-c", "print('address-hackathon image OK')"]
