FROM python:3.11-slim

# Chrome is a hard runtime requirement: every UI test drives a real browser.
# Without it the image builds fine and then fails at the first launch_url.
# chromium-driver is installed too so webdriver-manager has nothing to
# download at runtime -- important for air-gapped client sites.
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Point Selenium at the distro's Chrome rather than letting webdriver-manager
# fetch one over the network.
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# No display in a container, so headless is mandatory.
ENV HEADLESS=true \
    ENVIRONMENT=production \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first: this layer is cached unless requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir --no-deps -e .

# Run as a non-root user. Chrome refuses to start as root without
# --no-sandbox, and running a browser that renders untrusted pages as root is
# a poor idea regardless.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "src/ai_test_engine/app_multiagent.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
