# RAT Scraper in a container: Chromium + virtual display (Xvfb) + browser-based viewer (noVNC).
# Build context must be the extension folder (parent of this directory):
#   docker build -f deploy/Dockerfile -t rat-scraper .
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium xvfb x11vnc novnc websockify fluxbox \
      fonts-liberation fonts-noto-color-emoji ca-certificates openssl tini \
    && rm -rf /var/lib/apt/lists/*

# The extension lives at a fixed path, so its extension id is stable (computed in start.sh).
COPY . /opt/rat-extension
RUN rm -rf /opt/rat-extension/deploy
COPY deploy/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh \
    && useradd -m -u 1000 rat && mkdir -p /data/profile && chown -R rat:rat /data

USER rat
ENV DISPLAY=:99 SCREEN=1366x850x24 VNC_PASSWORD=
VOLUME /data
EXPOSE 6080
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/start.sh"]
