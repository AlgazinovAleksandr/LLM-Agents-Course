FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/app/.cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=2

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-deps torch==2.14.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/storage /home/app/.cache/huggingface \
    && chown -R app:app /app /home/app
COPY --chown=app:app . .
USER app

EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
