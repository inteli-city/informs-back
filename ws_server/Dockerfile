# Imagem do ws_server pra deploy no Railway.
#
# Build context: o conteúdo da pasta ws_server/. Configura no Railway:
#   Settings → Service → Source → Root Directory: ws_server
#
# Railway define a env PORT — uvicorn já honra com a flag --port.
# Demais env vars (STAGE, AWS_*, COGNITO_*, LOCATION_TABLE, PROFILE_TABLE)
# vêm do Service Variables do Railway, configuradas por environment.

FROM python:3.11-slim

# uv: installer/resolver de Python deps. Bem mais rápido que pip pra
# imagens pequenas e respeita o uv.lock que já temos no repo.
COPY --from=ghcr.io/astral-sh/uv:0.5.7 /uv /uvx /bin/

WORKDIR /app

# Copia manifestos primeiro pra cachear a layer de deps quando só o
# código muda (Docker rebuild só refaz a partir daqui se um dos 2 mudar).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Código da app.
COPY __init__.py auth.py config.py location_repo.py main.py messages.py presence.py ./

# Runtime: Railway injeta $PORT (default 8080 se não setada).
# --proxy-headers: respeita X-Forwarded-* do edge do Railway.
# Sem --reload: prod.
ENV PORT=8080
EXPOSE 8080
CMD uv run --frozen --no-dev uvicorn main:app \
    --host 0.0.0.0 --port $PORT --proxy-headers
