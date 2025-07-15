# Monitor Service

Este proyecto implementa un servicio de monitorización que consulta datos en MySQL, 
exponga un endpoint REST, gestione configuración dinámica y sea desplegable mediante 
Docker. 

---

## 🧩 Requisitos

- Python 3.10 o superior
- Docker & Docker Compose
- Linux x64 o WSL2 en Windows
- Make

---

## ⚙️ Configuración (`config.json`)

```json
{
  "mysql_host": "mysql",
  "mysql_user": "monitor",
  "mysql_password": "monitor123",
  "mysql_db": "monitoring",
  "threshold": 50,
  "query_interval": 10,
  "rest_port": 8080
}

---

## Contenido del Repositorio

 Quartux.py # Código principal 
 config.json # Configuración del servicio
 init.sql # Script para crear la base de datos
 logs/ # Directorio de logs
 Dockerfile # Imagen base del servicio
 docker-compose.yml # Orquestación del servicio y base de datos
 Makefile # Automatización para compilación
 evidencia/ # Capturas 
 README.md # Este archivo

---

## Señales admitidas

| Señal   | Acción                                                            |
| ------- | ----------------------------------------------------------------- |
| SIGHUP  | Recarga `config.json`, aplica cambios sin reiniciar el contenedor |
| SIGINT  | Finaliza el servicio limpiamente (`CTRL+C`)                       |
| SIGTERM | Finaliza el servicio limpiamente (detención Docker)               |

---

## Endpoint REST


El servicio expone: GET /status

Devuelve el último estado consultado como JSON:

{
  "last_check": "2025-07-08T10:23:00Z",
  "rows_processed": 3,
  "alerts": 1
}

---

## Docker

Archivos importantes:

-Dockerfile – Construye la imagen del servicio

-docker-compose.yml – Lanza el contenedor junto a MySQL

-init.sql – Crea la base de datos y tabla de ejemplo

Se ejecuta mediante docker-compose build y docker-compose up, se puede camabiar el código sin reconstruir imagen.

---

## Makefile

Incluye un Makefile para automatizar la pruebas

-make full - Ejecuta la automatización de pruebas en Linux

¿Qué hace?

Construye los contenedores

Hace un curl al puerto 8080

Cambia el puerto en config.json a 9090

Lanza un SIGHUP al contenedor

Hace un curl al nuevo puerto (9090)

---

## Base de datos

El siguiente script se ejecuta automáticamente al lanzar el contenedor MySQL gracias al volumen ./init.sql

CREATE DATABASE IF NOT EXISTS monitoring;
USE monitoring;

CREATE TABLE IF NOT EXISTS metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    value INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metrics (name, value) VALUES
('Temperature', 42),
('Pressure', 60),
('Humidity', 30);

---

## Evidencia

Se generan en /var/log/monitor_service.log dentro del contenedor.

Ejemplo:

{"timestamp": "2025-07-08T10:23:00Z", "level": "INFO", "message": "Processed 3 rows."}
{"timestamp": "2025-07-08T10:24:00Z", "level": "WARNING", "message": "Threshold exceeded: {...}"}

---

## Endpoint

curl http://localhost:8080/status

Respuesta esperada:

{
  "last_check": "2025-07-15T16:44:03.508654Z",
  "rows_processed": 3,
  "alerts": 1
}

Si el puerto cambia al 9090, cambia:

curl http://localhost:9090/status

---

##Autor

Este proyecto es propiedad de Kevin Cárdenas Téllez
