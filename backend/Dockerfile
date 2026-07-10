FROM python:3.11-slim

WORKDIR /app

COPY backend /app/backend
RUN sed -i 's/\r$//' /app/backend/entrypoint.sh && chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend
ENV PYTHONPATH=/app

ENTRYPOINT ["sh", "./entrypoint.sh"]
