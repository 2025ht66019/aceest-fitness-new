# Multi-stage lightweight production image for ACEest Fitness Flask app

FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off \
    POETRY_VIRTUALENVS_CREATE=false

# Create non-root user
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app

# No OS package installs: rely on manylinux wheel bundled libs for matplotlib.
# Removing apt-get eliminates flaky network mirror failures on arm64 builders.

# Install Python deps
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && find /opt/venv -name "__pycache__" -type d -exec rm -rf {} +
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY data.json ./

# Set a writable HOME and Matplotlib config/cache dir to avoid runtime warnings.
ENV HOME=/app \
    MPLCONFIGDIR=/app/.config/matplotlib
RUN mkdir -p /app/.config/matplotlib \
    && chown -R app:app /app \
    && chmod -R u+rw /app

# Expose port (matches k8s service 5000)
EXPOSE 5000

# Switch to non-root
USER app

# Healthcheck via Python stdlib (no curl dependency). One-liner keeps Docker syntax valid.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import urllib.request,sys;\nimport contextlib;\nurl='http://localhost:5000/';\ntry:\n    with contextlib.closing(urllib.request.urlopen(url,timeout=2)) as r: sys.exit(0 if 200 <= r.status < 400 else 1)\nexcept Exception: sys.exit(1)"

# Use gunicorn for production serving (more robust than flask dev server)
# Matplotlib charts are generated on demand; no worker class customization needed yet.
CMD ["gunicorn", "--preload", "app:create_app()", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
