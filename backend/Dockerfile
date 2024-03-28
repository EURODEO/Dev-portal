# Use an official Python runtime as a parent image
FROM python:3.12.2-alpine as builder

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /tmp

# Install Poetry
# https://python-poetry.org/docs/cli/#export
RUN pip install poetry poetry-plugin-export
COPY ./pyproject.toml ./poetry.lock* ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Multi-stage build: create a slim image
FROM python:3.12.2-alpine

# Create a non-root user
RUN adduser -D appuser && mkdir -p /code/app && chown -R appuser /code

# Copy only Poetry generated requirements.txt
COPY --from=builder /tmp/requirements.txt /code/requirements.txt

# Set work directory
WORKDIR /code

# Copy a default config file. Override this by mounting a config.yaml
COPY ./config.default.yaml ./config.default.yaml

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# Copy only necessary files
COPY ./app ./app

# Switch to non-root user
USER appuser

# Expose the application's port
EXPOSE 8082

# Run the application
# Might need to include --proxy-headers if behind a load balancer like nginx etc
CMD ["python", "-m", "app.main"]
