FROM python:3.12-slim

#cartella di lavoro
WORKDIR /app

#dipendenze di sistema minime
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

#file dei requisiti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

#porta 5000 standard Flask
EXPOSE 5000

#avvio server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "server:app"]