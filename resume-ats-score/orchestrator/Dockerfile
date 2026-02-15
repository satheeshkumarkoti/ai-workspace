FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp_creds.json

# Expose port (if needed for web interface)
EXPOSE 8000

# Run the application
CMD ["uv", "run", "python", "run.py"]