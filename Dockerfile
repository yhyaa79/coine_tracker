# Dockerfile
FROM python:3.11-slim

# جلوگیری از بافر شدن لاگ‌ها و نمایش realtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# نصب وابستگی‌های سیستم برای TensorFlow CPU و mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ساخت کاربر غیرروت برای امنیت
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# اول requirements رو کپی کن تا cache بشه
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نصب TensorFlow CPU به صورت جداگانه (حجم کمتر و سریع‌تر)
RUN pip install --no-cache-dir tensorflow-cpu

# کپی کردن کد پروژه
COPY . .

# تغییر مالکیت فایل‌ها به کاربر غیرروت
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 4002

# استفاده از Gunicorn برای تولید (بهتر از app.run)
CMD ["gunicorn", "--bind", "0.0.0.0:4002", "--workers", "3", "--timeout", "120", "app:app"]