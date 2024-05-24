FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

COPY .env .env

# Run main.py when the container launches
CMD ["python", "main.py"]
