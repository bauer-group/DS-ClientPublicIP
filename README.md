# ClientPublicIP

A lightweight, production-ready microservice for public IP address detection. Returns client IPv4 and IPv6 addresses via web interface, JSON API, or plain text.

## Features

- **Multi-format responses**: Web UI, JSON API, and plain text endpoints
- **Dual-stack support**: Separate IPv4 and IPv6 detection via DNS-based routing
- **Rate limiting**: Configurable request throttling with in-memory storage
- **Production-ready**: Gunicorn WSGI server with Docker healthchecks
- **Traefik integration**: Pre-configured with TLS and CORS middleware
- **Minimal footprint**: Lightweight Python base image

## Quick Start

```bash
# Clone and configure
cp .env.example .env

# Start with Docker Compose
docker compose up -d
```

## API Endpoints

| Endpoint | Format | Example Response |
|----------|--------|------------------|
| `/` | HTML | Interactive web interface |
| `/json` | JSON | `{"IP": "203.0.113.42"}` |
| `/raw` | Text | `203.0.113.42` |

### DNS-based IP Version Selection

| Subdomain | Description |
|-----------|-------------|
| `ip.example.com` | Returns IP based on client connection |
| `v4.ip.example.com` | Forces IPv4 resolution (A record only) |
| `v6.ip.example.com` | Forces IPv6 resolution (AAAA record only) |

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_HOSTNAME` | `ip.cloudhotspot.de` | Public hostname for the service |
| `RATE_LIMIT` | `480/minute` | Request rate limit per client |
| `TIME_ZONE` | `Etc/UTC` | Container timezone |
| `PROXY_NETWORK` | `EDGEPROXY` | Traefik network name |
| `STACK_NAME` | `ip_cloudhotspot_de` | Docker stack identifier |

## Project Structure

```
ClientPublicIP/
├── src/                    # Application source
│   ├── app.py              # Flask application
│   ├── app.sh              # Gunicorn entrypoint
│   ├── Dockerfile          # Container definition
│   ├── requirements.txt    # Python dependencies
│   └── templates/
│       └── index.html      # Web interface
├── docker-compose.yml      # Deployment configuration
├── .env.example            # Environment template
├── .dockerignore           # Build exclusions
└── .github/                # CI/CD workflows
```

## Deployment

### Prerequisites

- Docker and Docker Compose
- Traefik reverse proxy (for production)
- DNS records pointing to your server:
  - `ip.example.com` → A + AAAA records
  - `v4.ip.example.com` → A record only
  - `v6.ip.example.com` → AAAA record only

### Production Deployment

```bash
# Configure environment
cp .env.example .env
vim .env  # Adjust SERVICE_HOSTNAME and other settings

# Deploy stack
docker compose up -d

# View logs
docker compose logs -f
```

### Build from Source

```bash
docker compose build
docker compose up -d
```

## Development

### Local Testing

```bash
cd src
pip install -r requirements.txt
python app.py
```

Access at `http://localhost:8080`

### API Examples

```bash
# JSON response
curl -s https://ip.example.com/json | jq
# {"IP": "203.0.113.42"}

# Plain text
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
- **Rate Limiting**: Flask-Limiter with memory storage
- **Container**: Non-root user, Tini init system
- **Health Check**: HTTP probe on `/raw` endpoint

## License

MIT
