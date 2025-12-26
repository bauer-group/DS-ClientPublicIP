FROM bauergroup/python3-light:latest

# Metadata
LABEL vendor="BAUER GROUP"
LABEL maintainer="Karl Bauer <karl.bauer@bauer-group.com>"

# Opencontainers Metadata
LABEL org.opencontainers.image.title="ClientPublicIP"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="BAUER GROUP"
LABEL org.opencontainers.image.authors="Karl Bauer <karl.bauer@bauer-group.com>"
LABEL org.opencontainers.image.source="https://github.com/bauer-group/DS-ClientPublicIP"
LABEL org.opencontainers.image.url="https://github.com/bauer-group/DS-ClientPublicIP"
LABEL org.opencontainers.image.documentation="https://github.com/bauer-group/DS-ClientPublicIP#readme"
LABEL org.opencontainers.image.description="Lightweight service to detect and display public IPv4/IPv6 addresses"
LABEL org.opencontainers.image.version="0.4.0"

# === System ===
# Set Timezone
ENV TIME_ZONE=Etc/UTC

# Disable Interactive Shell for Build
ARG DEBIAN_FRONTEND=noninteractive

# Change User
USER root

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set Up Environment
RUN set -ex && \
    localedef -i de_DE -c -f UTF-8 -A /usr/share/locale/locale.alias de_DE.UTF-8

# Set Language
ENV LANG=de_DE.utf8

# === Application ===
# Setup Application
WORKDIR /app

# Remove Demo main.py and Create User
RUN set -ex \
    && rm -f main.py \
    && useradd -m app \
    && chown -R app:app /app

# Webserver Port
ENV SERVER_PORT=8080
EXPOSE ${SERVER_PORT}/tcp

### Setup ##

# Copy Files
ADD requirements.txt /app/
ADD app.py /app/
ADD templates/ /app/templates/

# Create GeoIP data directory
RUN set -ex \
    && mkdir -p /app/data

# Fix Ownership
RUN set -ex \
    && chown -R app:app /app

# Change User
USER app

# Configure Environment
ENV FLASK_APP=app

# Application Settings
ENV SERVICE_HOSTNAME=ip.bauer-group.com
ENV RATE_LIMIT=480/minute
ENV GEOIP_DB_PATH=/app/data/GeoLite2-Country.mmdb

# Prepare Environment & Install required Packages (Design Time)
RUN set -ex \
    && /usr/local/bin/docker-setup-requirements.sh

### Runtime ###

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:${SERVER_PORT}/raw || exit 1

# Entrypoint
CMD ["/usr/bin/tini", "--", "/app/app.sh"]
