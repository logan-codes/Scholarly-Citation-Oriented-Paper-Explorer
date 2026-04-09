FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["uv","run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
