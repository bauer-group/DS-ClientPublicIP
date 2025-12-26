# ClientPublicIP

A lightweight, production-ready microservice for public IP address detection with GeoIP country lookup. Returns client IPv4 and IPv6 addresses via web interface, JSON API, or plain text.

## Features

- **Multi-format responses**: Web UI, JSON API, and plain text endpoints
- **Dual-stack support**: Separate IPv4 and IPv6 detection via DNS-based routing
- **GeoIP country detection**: Automatic country lookup using MaxMind GeoLite2 database
- **Rate limiting**: Configurable request throttling with in-memory storage
- **Production-ready**: Gunicorn WSGI server with Docker healthchecks
- **Multiple deployment options**: Coolify, Traefik, or standalone
- **Automatic GeoIP updates**: Weekly database updates via MaxMind geoipupdate
- **Minimal footprint**: Lightweight Python base image

## Quick Start

```bash
# Clone and configure
cp .env.example .env
vim .env  # Add MaxMind credentials and configure hostname

# Start with Docker Compose (Coolify/Standalone)
docker compose up -d

# Or with Traefik
docker compose -f docker-compose.traefik.yml up -d
```

## API Endpoints

| Endpoint | Format | Example Response |
|----------|--------|------------------|
| `/` | HTML | Interactive web interface with country flags |
| `/json` | JSON | `{"IP": "203.0.113.42", "COUNTRY": {"CODE": "DE", "NAME": "Germany"}}` |
| `/raw` | Text | `203.0.113.42` |

### JSON Response Format

```json
{
  "IP": "203.0.113.42",
  "COUNTRY": {
    "CODE": "DE",
    "NAME": "Germany"
  }
}
```

> **Note**: The `COUNTRY` field is only included when the GeoIP database is available. Without MaxMind credentials, the service works normally but without country detection.

### DNS-based IP Version Selection

| Subdomain | Description |
|-----------|-------------|
| `ip.example.com` | Returns IP based on client connection |
| `v4.ip.example.com` | Forces IPv4 resolution (A record only) |
| `v6.ip.example.com` | Forces IPv6 resolution (AAAA record only) |

## Configuration

Environment variables (see `.env.example`):

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `STACK_NAME` | - | Docker stack identifier (required) |
| `SERVICE_HOSTNAME` | `ip.bauer-group.com` | Public hostname for the service |
| `RATE_LIMIT` | `480/minute` | Request rate limit per client |
| `TIME_ZONE` | `UTC` | Container timezone |

### MaxMind GeoIP Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAXMIND_ACCOUNT_ID` | - | MaxMind account ID ([register here](https://www.maxmind.com/en/geolite2/signup)) |
| `MAXMIND_LICENSE_KEY` | - | MaxMind license key |
| `GEOIP_UPDATE_FREQUENCY` | `168` | Update check interval in hours (168 = weekly, 0 = once) |

### Traefik Settings (only for docker-compose.traefik.yml)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXY_NETWORK` | `EDGEPROXY` | Traefik network name |

## Deployment Options

### Option 1: Coolify / Standalone

Uses `docker-compose.yml` with direct port mapping:

```bash
docker compose up -d
```

Access via `http://localhost:8080` or configure your reverse proxy.

### Option 2: Traefik Reverse Proxy

Uses `docker-compose.traefik.yml` with Traefik labels:

```bash
docker compose -f docker-compose.traefik.yml up -d
```

Includes automatic TLS via Let's Encrypt and CORS headers.

### Option 3: Development

Uses `docker-compose.development.yml` with hot-reload:

```bash
docker compose -f docker-compose.development.yml up -d
```

- Source code mounted as volumes for live editing
- Higher rate limits (960/minute)
- Flask debug mode enabled
- GeoIP downloads once (not recurring)

## Project Structure

```
ClientPublicIP/
├── src/                              # Application source
│   ├── app.py                        # Flask application (OOP class-based)
│   ├── app.sh                        # Gunicorn entrypoint
│   ├── Dockerfile                    # Container definition
│   ├── requirements.txt              # Python dependencies
│   └── templates/
│       └── index.html                # Web interface with country flags
├── docker-compose.yml                # Coolify/Standalone deployment
├── docker-compose.traefik.yml        # Traefik deployment
├── docker-compose.development.yml    # Development environment
├── .env.example                      # Environment template
├── .dockerignore                     # Build exclusions
└── .github/                          # CI/CD workflows
```

## Prerequisites

- Docker and Docker Compose v2
- MaxMind account for GeoIP (optional but recommended)
- DNS records pointing to your server:
  - `ip.example.com` → A + AAAA records
  - `v4.ip.example.com` → A record only
  - `v6.ip.example.com` → AAAA record only

## GeoIP Setup

1. Register at [MaxMind GeoLite2](https://www.maxmind.com/en/geolite2/signup)
2. Generate a license key in your MaxMind account
3. Add credentials to `.env`:

```bash
MAXMIND_ACCOUNT_ID=123456
MAXMIND_LICENSE_KEY=your_license_key
```

The GeoIP database is stored in a shared Docker volume and automatically updated weekly.

## Development

### Local Testing (without Docker)

```bash
cd src
pip install -r requirements.txt
python app.py
```

Access at `http://localhost:8080`

### API Examples

```bash
# JSON response with country
curl -s https://ip.example.com/json | jq
# {
#   "IP": "203.0.113.42",
#   "COUNTRY": {
#     "CODE": "DE",
#     "NAME": "Germany"
#   }
# }

# Plain text (IP only)
curl -s https://ip.example.com/raw
# 203.0.113.42

# Force IPv4
curl -4 https://v4.ip.example.com/raw

# Force IPv6
curl -6 https://v6.ip.example.com/raw
```

## Technical Details

- **Framework**: Flask 3.1
- **WSGI Server**: Gunicorn 23.0
- **GeoIP**: geoip2 5.2 with MaxMind GeoLite2-Country
- **Rate Limiting**: Flask-Limiter with memory storage
- **CORS**: Flask-CORS with dynamic origin support
- **Container**: Non-root user, Tini init system
- **Health Check**: HTTP probe on `/raw` endpoint
- **Architecture**: Class-based OOP design (`ClientPublicIPApp`)

## License

MIT
