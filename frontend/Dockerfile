FROM node:20-slim

WORKDIR /app

COPY . .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["sh", "./entrypoint.sh"]
