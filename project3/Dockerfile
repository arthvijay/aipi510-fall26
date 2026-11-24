FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements-api.txt requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt
COPY pyproject.toml .
COPY src src
RUN pip install --no-cache-dir --no-deps .

FROM base AS api
COPY config.yaml config.yaml
COPY examples examples
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
ENV RIDECAST_MODEL_SOURCE=local PORT=8080
EXPOSE 8080
ENTRYPOINT ["python", "-m", "ridecast"]
CMD ["serve", "--config", "config.yaml"]

FROM python:3.11-slim AS project
WORKDIR /app
COPY requirements.txt .
COPY pyproject.toml .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser && mkdir -p workdir && chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["python", "-m", "ridecast"]
CMD ["serve", "--config", "config.yaml"]
