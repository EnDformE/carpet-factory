FROM python:3.11-alpine

WORKDIR /app

RUN pip install --no-cache-dir flask psycopg2-binary

COPY main.py .

CMD ["python", "main.py"]
