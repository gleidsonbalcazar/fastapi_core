FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["/bin/bash", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload"]
