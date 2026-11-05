FROM python:3.10-slim

# Set environment variables for better logging in Docker
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy the TF-IDF vectorizer
COPY models/tfidf_vectorizer_only.pkl models/

# Copy the rest of the application
COPY . .

# Use exec form and add logging flags for uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info", "--access-log"]
