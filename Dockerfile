FROM python:3.11-slim as base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY . .

EXPOSE 8000

ENTRYPOINT ["uv", "run", "main.py"]
