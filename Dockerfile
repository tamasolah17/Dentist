# 1. Base image (Python installed)
FROM python:3.11-slim

# 2. Set working directory inside container
WORKDIR /app2

# 3. Copy dependency list first (for caching)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip uninstall -y jwt PyJWT || true
RUN pip install --no-cache-dir PyJWT


# 5. Copy all project files
COPY . .

# 6. Expose Flask port
EXPOSE 5000

# 7. Start the webhook server (NOT Invoice.py)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app2"]