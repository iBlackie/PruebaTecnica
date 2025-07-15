FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY config.json ./
RUN mkdir -p /var/log

EXPOSE 8080

CMD ["python", "Quartux.py"]