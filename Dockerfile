FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/vite.config.js frontend/painel.css ./
COPY frontend/src/ ./src/
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/app.py ./backend/
COPY backend/services/ ./backend/services/
COPY data/ ./data/
COPY frontend/vendor/ ./frontend/vendor/
COPY --from=frontend /build/dist/ ./frontend/dist/
USER 65534:65534
EXPOSE 8000 8001
CMD ["python", "backend/app.py", "--host", "0.0.0.0"]
