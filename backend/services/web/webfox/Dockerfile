# ===============================
# webfox/Dockerfile
# ===============================
FROM debian:stable-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    firefox-esr \
    python3 python3-pip \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages fastapi uvicorn selenium readability-lxml lxml html5lib pillow

# GeckoDriver (match Debian ESR)
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/* \
    && GECKO_VER=$(wget -qO- https://api.github.com/repos/mozilla/geckodriver/releases/latest | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p') \
    && wget -q https://github.com/mozilla/geckodriver/releases/download/${GECKO_VER}/geckodriver-${GECKO_VER}-linux64.tar.gz -O /tmp/gd.tar.gz \
    && tar -xzf /tmp/gd.tar.gz -C /usr/local/bin \
    && rm -f /tmp/gd.tar.gz

WORKDIR /app
COPY app.py /app/app.py
EXPOSE 8070
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8070"]
