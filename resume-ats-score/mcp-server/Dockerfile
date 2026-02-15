FROM python:3.13-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

RUN mkdir -p /data

VOLUME ["/data"]

EXPOSE 8000

CMD ["uv", "run", "python", "server.py"]