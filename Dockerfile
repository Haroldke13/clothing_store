# syntax=docker/dockerfile:1
###############################################################################
# clothing_store — Flask + MongoDB inventory / cart / POS
#
# Build:  docker build -t clothing-store:latest .
# Run:    see DEPLOY.md
#
# NOTE: this image builds and starts cleanly, but the app will connect to the
# MongoDB URI hardcoded in app/db.py until that one line is env-ified.
# DEPLOY.md section 1 has the details. Do not point DNS at it before then.
###############################################################################

FROM python:3.12.3-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r requirements.txt

FROM python:3.12.3-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=5758

COPY --from=builder /opt/venv /opt/venv

RUN useradd --system --create-home --uid 10002 --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --chown=root:root . /app

# Two directories the app writes to at runtime, both resolved relative to the
# working directory by the application code:
#   flask_session_data/    -> Flask-Session filesystem backend (app/__init__.py)
#   app/static/images/     -> product image uploads (app/routes.py)
# Mount both as volumes in production or uploads vanish on every redeploy.
RUN mkdir -p /app/flask_session_data /app/app/static/images \
 && chown -R appuser:appuser /app/flask_session_data /app/app/static/images
VOLUME ["/app/flask_session_data", "/app/app/static/images"]

USER appuser

EXPOSE 5758

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5758/healthz', timeout=4).status == 200 else 1)"

# I/O-bound (MongoDB round trips), so threads are cheap and workers are not.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5758", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "deploy_wsgi:app"]
