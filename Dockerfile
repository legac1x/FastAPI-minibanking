FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN groupadd -r groupfastapi && useradd -r -g groupfastapi user
RUN pip install --upgrade pip
WORKDIR /minibanking
RUN mkdir -p /minibanking/logs
RUN chown -R user:groupfastapi /minibanking/logs
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --chown=user:groupfastapi . .
USER user
EXPOSE 8000
CMD gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000