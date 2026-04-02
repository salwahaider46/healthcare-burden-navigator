FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY load_fhir_bundle.py .

ENTRYPOINT ["python", "/app/load_fhir_bundle.py"]
