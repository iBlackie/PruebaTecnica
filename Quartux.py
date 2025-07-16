import os
import json
import time
import threading
import signal
import logging
import pymysql
import signal
from flask import Flask, jsonify, request
from datetime import datetime
from werkzeug.serving import make_server

conn=None
rest_server = None
rest_server_thread = None
current_rest_port = None

# Configuración inicial
CONFIG_FILE = 'config.json'
LOG_FILE = '/var/log/monitor_service.log'
config_lock = threading.Lock()
current_config = {}
last_status = {
    'last_check': None,
    'rows_processed': 0,
    'alerts': 0
}

#Logger JSON
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage()
        }
        return json.dumps(log_record)

logger = logging.getLogger('monitor_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

#Función para cargar configuración
def load_config():
    global current_config
    with config_lock:
        with open(CONFIG_FILE) as f:
            current_config = json.load(f)
        logger.info('Configuration reloaded')

#Monitor de MySQL
def monitor_loop():
    global last_status, conn
    old_cfg = {}

    while True:
        with config_lock:
            cfg = current_config.copy()

        # Si cambia la configuración de MySQL, forzar reconexión
        if conn and any(
            old_cfg.get(k) != cfg.get(k)
            for k in ['mysql_host', 'mysql_user', 'mysql_password', 'mysql_db']):
            logger.info('MySQL config changed. Closing connection...')
            conn.close()
            conn = None

        if not conn:
            try:
                conn = pymysql.connect(
                    host=cfg['mysql_host'],
                    user=cfg['mysql_user'],
                    password=cfg['mysql_password'],
                    database=cfg['mysql_db']
                )
                logger.info('Connected to MySQL')
                old_cfg = cfg 
            except Exception as e:
                logger.warning(f'MySQL connection failed: {e}')
                time.sleep(5)
                continue

            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, name, value, updated_at FROM metrics")
                    rows = cursor.fetchall()
                    alerts = 0

                    for row in rows:
                        if row[2] > cfg['threshold']:
                            row_log = {
                                'id': row[0],
                                'name': row[1],
                                'value': row[2],
                                'updated_at': row[3].isoformat()
                            }
                            logger.warning(json.dumps(row_log))
                            alerts += 1

                    # Log final claro y único
                    logger.info(f"Processed {len(rows)} rows.")

                    last_status = {
                        'last_check': datetime.utcnow().isoformat() + 'Z',
                        'rows_processed': len(rows),
                        'alerts': alerts
                    }

            except Exception as e:
                logger.warning(f'Query failed: {e}')
                conn = None  

            time.sleep(cfg['query_interval'])

# REST API
app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    api_key = request.headers.get('X-API-KEY')
    if api_key != current_config.get('api_key'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(last_status)

def start_rest_server(port):
    global rest_server, rest_server_thread

    class ServerThread(threading.Thread):
        def __init__(self, app, port):
            threading.Thread.__init__(self)
            self.port = port
            self.server = make_server('0.0.0.0', port, app)
            self.ctx = app.app_context()
            self.ctx.push()
            self.daemon = True

        def run(self):
            logger.info(f"REST API running on port {self.port}")
            self.server.serve_forever()

        def shutdown(self):
            logger.info(f"Shutting down REST API on port {self.port}")
            self.server.shutdown()
            self.server.server_close()

    if rest_server_thread:
        try:
            rest_server.shutdown()
            rest_server_thread.join()
        except Exception as e:
            logger.warning(f"Failed to shut down previous REST server: {e}")

    rest_server = ServerThread(app, port)
    rest_server_thread = rest_server
    rest_server.start()

# Manejo de señales
def handle_sighup(signum, frame):
    global conn, current_rest_port

    logger.info("SIGHUP recibido: recargando configuración...")
    load_config()

    with config_lock:
        if conn:
            try:
                conn.close()
                logger.info("MySQL connection closed for hot swap.")
            except Exception as e:
                logger.warning(f"Error closing MySQL connection: {e}")
            conn = None

        new_port = current_config.get('rest_port', 8080)
        if new_port != current_rest_port:
            logger.info(f"REST port changed: {current_rest_port} → {new_port}")
            current_rest_port = new_port
            start_rest_server(new_port)
        else:
            logger.info("REST port unchanged; keeping current server.")

def handle_sigterm(signum, frame):
    global conn
    logger.info('Shutting down...')
    if conn:
        try:
            conn.close()
            logger.info('MySQL connection closed.')
        except Exception as e:
            logger.warning(f'Error closing MySQL connection: {e}')
    os._exit(0)

if hasattr(signal, 'SIGHUP'):
    signal.signal(signal.SIGHUP, handle_sighup)
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

# Main
if __name__ == '__main__':
    if not os.path.exists('/var/log'):
        os.makedirs('/var/log')

    load_config()
    current_rest_port = current_config.get('rest_port', 8080)
    start_rest_server(current_rest_port)

    t_monitor = threading.Thread(target=monitor_loop, daemon=True)
    t_monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_sigterm(None, None)