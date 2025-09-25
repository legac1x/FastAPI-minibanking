FROM python:3.12-alpine
RUN addgroup -S groupfastapi && adduser -S user -G groupfastapi
RUN pip install --upgrade pip
WORKDIR /minibanking
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user:groupfastapi . .
USER user