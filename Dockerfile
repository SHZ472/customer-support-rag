FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

COPY course_cache.py /app/
COPY app /app/app
COPY data /app/data
RUN mkdir -p /app/.cache/huggingface && chown -R 10001:10001 /app/.cache
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
