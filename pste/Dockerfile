# Menggunakan image Python resmi yang ringan
FROM python:3.10-slim

# Mencegah Python menulis file .pyc ke disk (equivalen dengan python -B)
ENV PYTHONDONTWRITEBYTECODE=1

# Mencegah Python melakukan buffer pada stdout dan stderr
ENV PYTHONUNBUFFERED=1
# Menentukan direktori kerja di dalam container
WORKDIR /app

# Menyalin file requirements.txt ke dalam container
COPY requirements.txt /app/

# Install system dependencies (Sesuaikan dengan kebutuhan database Anda)
# Contoh di bawah ini menyertakan build-essential dan libpq-dev untuk psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Menginstal dependencies Python
RUN pip install --upgrade pip && pip install -v --no-cache-dir -r requirements.txt
# Mengekspos port 8000 agar bisa diakses dari luar container
EXPOSE 8000

# Perintah default untuk menjalankan server (bisa ditimpa oleh docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]