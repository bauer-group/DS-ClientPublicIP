from flask import Flask, request, Response, jsonify, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import geoip2.database
import geoip2.errors
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import threading
import logging
import os
import sys


class GeoIPFileHandler(FileSystemEventHandler):
    """Watches for GeoIP database file changes and triggers reload."""

    def __init__(self, app: 'ClientPublicIPApp') -> None:
        self.app = app

    def on_modified(self, event) -> None:
        if not event.is_directory and event.src_path.endswith('.mmdb'):
            self.app.flask_app.logger.info(f"GeoIP database modified: {event.src_path}")
            self.app._reload_geoip()

    def on_created(self, event) -> None:
        if not event.is_directory and event.src_path.endswith('.mmdb'):
            self.app.flask_app.logger.info(f"GeoIP database created: {event.src_path}")
            self.app._reload_geoip()


class ClientPublicIPApp:
    """Main application class for ClientPublicIP service."""

    def __init__(self) -> None:
        self.flask_app = Flask(__name__)
        self.geoip_reader: geoip2.database.Reader | None = None
        self._geoip_lock = threading.Lock()
        self._observer: PollingObserver | None = None

        self._load_config()
        self._configure_logging()
        self._configure_cors()
        self._configure_rate_limiter()
        self._init_geoip()
        self._start_geoip_watcher()
        self._register_routes()

    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        self.service_hostname = os.environ.get('SERVICE_HOSTNAME', 'ip.cloudhotspot.de')
        self.rate_limit = os.environ.get('RATE_LIMIT', '480/minute')
        self.server_port = int(os.environ.get('SERVER_PORT', '8080'))
        self.geoip_db_path = Path(os.environ.get('GEOIP_DB_PATH', '/app/data/GeoLite2-Country.mmdb'))

    def _configure_logging(self) -> None:
        """Configure logging to suppress request logs."""
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

    def _configure_cors(self) -> None:
        """Configure CORS for cross-subdomain requests."""
        CORS(self.flask_app, origins=[
            f"https://{self.service_hostname}",
            f"https://v4.{self.service_hostname}",
            f"https://v6.{self.service_hostname}",
            f"http://{self.service_hostname}",
            f"http://v4.{self.service_hostname}",
            f"http://v6.{self.service_hostname}"
        ])

    def _configure_rate_limiter(self) -> None:
        """Configure the rate limiter."""
        self.rate_limiter = Limiter(
            get_remote_address,
            app=self.flask_app,
            default_limits=[self.rate_limit],
            storage_uri="memory://",
        )

    def _init_geoip(self) -> None:
        """Initialize the GeoIP database reader."""
        with self._geoip_lock:
            if self.geoip_db_path.exists():
                try:
                    self.geoip_reader = geoip2.database.Reader(str(self.geoip_db_path))
                    self.flask_app.logger.info(f"GeoIP database loaded: {self.geoip_db_path}")
                except Exception as e:
                    self.flask_app.logger.error(f"Failed to load GeoIP database: {e}")
            else:
                self.flask_app.logger.warning(f"GeoIP database not found: {self.geoip_db_path}")

    def _reload_geoip(self) -> None:
        """Reload the GeoIP database (thread-safe)."""
        with self._geoip_lock:
            old_reader = self.geoip_reader
            try:
                if self.geoip_db_path.exists():
                    self.geoip_reader = geoip2.database.Reader(str(self.geoip_db_path))
                    self.flask_app.logger.info(f"GeoIP database reloaded: {self.geoip_db_path}")
                    if old_reader:
                        old_reader.close()
            except Exception as e:
                self.flask_app.logger.error(f"Failed to reload GeoIP database: {e}")

    def _start_geoip_watcher(self) -> None:
        """Start watching the GeoIP database directory for changes.

        Uses polling-based observer for Docker volume compatibility.
        Works correctly with Gunicorn workers (each worker has its own watcher).
        """
        watch_dir = self.geoip_db_path.parent
        if not watch_dir.exists():
            self.flask_app.logger.warning(f"GeoIP watch directory not found: {watch_dir}")
            return

        try:
            # Use PollingObserver for Docker volume compatibility
            # (inotify doesn't work across container boundaries)
            # Check every 5 minutes - DB updates are rare (weekly by default)
            observer = PollingObserver(timeout=300)
            handler = GeoIPFileHandler(self)
            observer.schedule(handler, str(watch_dir), recursive=False)
            observer.daemon = True  # Thread will exit when main thread exits
            observer.start()
            self._observer = observer
            self.flask_app.logger.info(f"GeoIP file watcher started on: {watch_dir}")
        except Exception as e:
            self.flask_app.logger.error(f"Failed to start GeoIP watcher: {e}")

    def _get_country_info(self, ip_address: str) -> dict[str, str] | None:
        """Look up country information for an IP address."""
        if not self.geoip_reader:
            return None
        try:
            response = self.geoip_reader.country(ip_address)
            return {
                "CODE": response.country.iso_code,
                "NAME": response.country.name
            }
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return None
        except Exception:
            return None

    def _get_client_ip(self) -> str:
        """Extract the client IP from the request."""
        if 'X-Forwarded-For' in request.headers:
            client_ips = request.headers.getlist('X-Forwarded-For')[0].split(',')
            return client_ips[0].strip()
        return request.remote_addr or ''

    def _register_routes(self) -> None:
        """Register all Flask routes."""

        @self.flask_app.route('/')
        @self.rate_limiter.limit(self.rate_limit)
        def index() -> str:
            return render_template('index.html', SERVICE_HOSTNAME=self.service_hostname)

        @self.flask_app.route('/json')
        @self.rate_limiter.limit(self.rate_limit)
        def get_client_ip_json() -> Response:
            ip = self._get_client_ip()
            country = self._get_country_info(ip)
            response_data: dict[str, str | dict[str, str]] = {"IP": str(ip)}
            if country:
                response_data["COUNTRY"] = country
            return jsonify(response_data)

        @self.flask_app.route('/raw')
        @self.rate_limiter.limit(self.rate_limit)
        def get_client_ip_raw() -> Response:
            return Response(self._get_client_ip(), mimetype='text/plain')

        @self.flask_app.route('/offline')
        def offline() -> str:
            return render_template('offline.html')

        @self.flask_app.route('/sw.js')
        def service_worker() -> Response:
            return send_from_directory('static', 'sw.js', mimetype='application/javascript')

    def run(self) -> None:
        """Run the Flask development server."""
        self.flask_app.run(host='0.0.0.0', port=self.server_port)


def is_running_with_wsgi_server() -> bool:
    """Check if running under a WSGI server like Gunicorn."""
    return "gunicorn" in sys.modules

# Create application instance
application = ClientPublicIPApp()
app = application.flask_app

if __name__ == '__main__':
    if not is_running_with_wsgi_server():
        application.run()
