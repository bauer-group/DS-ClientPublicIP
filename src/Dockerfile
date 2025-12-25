FROM bauergroup/python3-light:latest

LABEL vendor="BAUER GROUP"
LABEL maintainer="Karl Bauer <karl.bauer@bauer-group.com>"

ENV TIME_ZONE=Etc/UTC

# === System ===
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

# Prepare Environment & Install required Packages (Design Time)
RUN set -ex \
    && /usr/local/bin/docker-setup-requirements.sh

### Runtime ###

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:${SERVER_PORT}/raw || exit 1

# Entrypoint
CMD ["/usr/bin/tini", "--", "/app/app.sh"]
