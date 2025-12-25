from flask import Flask, request, Response, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import sys

app = Flask(__name__)

# Environment Variables
SERVICE_HOSTNAME = os.environ.get('SERVICE_HOSTNAME', 'ip.cloudhotspot.de')
RATE_LIMIT = os.environ.get('RATE_LIMIT', '480/minute')
SERVER_PORT = os.environ.get('SERVER_PORT', '8080')

# Configure the rate limiter
rate_limiter = Limiter(
    get_remote_address,
    app=app,       
    default_limits=[RATE_LIMIT],
    storage_uri="memory://",
)

# Disable logging for all requests, only warnings or errors
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

@app.route('/')
@rate_limiter.limit(RATE_LIMIT)
def index():
    return render_template('index.html', SERVICE_HOSTNAME=SERVICE_HOSTNAME)

@app.route('/json')
@rate_limiter.limit(RATE_LIMIT)
def get_client_ip_json():
    return jsonify(IP=str(get_client_ip()))

@app.route('/raw')
@rate_limiter.limit(RATE_LIMIT)
def get_client_ip_raw():
    return Response(f'{get_client_ip()}', mimetype='text/plain')

def get_client_ip():
    if 'X-Forwarded-For' in request.headers:
        client_ips = request.headers.getlist('X-Forwarded-For')[0].split(',')
        return client_ips[0].strip()
    else:
        return request.remote_addr

# Entry Point
def isRunningWithASGIServer():
    return "gunicorn" in sys.modules

if __name__ == '__main__':
    if not isRunningWithASGIServer():
        app.run(host='0.0.0.0', port=SERVER_PORT)

