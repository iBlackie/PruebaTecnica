# Monitor Service

Este proyecto implementa un servicio de monitorización que consulta datos en MySQL, 
exponga un endpoint REST, gestione configuración dinámica y sea desplegable mediante 
Docker. 

---

## Requisitos

- Python 3.10 o superior
- Docker & Docker Compose
- Linux x64 o WSL2 en Windows
- Make

---

## Configuración (`config.json`)

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
```
---

## Contenido del Repositorio

 - Quartux.py # Código principal 
 - config.json # Configuración del servicio
 - init.sql # Script para crear la base de datos
 - logs/ # Directorio de logs
 - Dockerfile # Imagen base del servicio
 - docker-compose.yml # Orquestación del servicio y base de datos
 - Makefile # Automatización para compilación
 - evidencia/ # Capturas 
 - README.md # Este archivo

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

- Dockerfile – Construye la imagen del servicio

- docker-compose.yml – Lanza el contenedor junto a MySQL

- init.sql – Crea la base de datos y tabla de ejemplo

Se ejecuta mediante docker-compose build y docker-compose up, se puede camabiar el código sin reconstruir imagen.

---

## Makefile para ejecutar en Ubuntu

Incluye un Makefile para automatizar la pruebas

- make full (Ejecuta la automatización de pruebas en Linux)

¿Qué hace? Un hot swap

Construye los contenedores

Hace un curl al puerto 8080

Cambia el puerto en config.json a 9090

Lanza un SIGHUP al contenedor

Hace un curl al nuevo puerto (9090)

O si empieza con el puerto 9090, pasa al puerto 8080.

---

## Base de datos

El siguiente script se ejecuta automáticamente al lanzar el contenedor MySQL gracias al volumen ./init.sql

```sql
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
```
---

## Evidencia

Se generan en /var/log/monitor_service.log dentro del contenedor.

Ejemplo:

{"timestamp": "2025-07-08T10:23:00Z", "level": "INFO", "message": "Processed 3 rows."}
{"timestamp": "2025-07-16T16:00:17.077626Z", "level": "WARNING", "message": "{\"id\": 5, \"name\": \"Pressure\", \"value\": 60, \"updated_at\": \"2025-07-14T21:19:08\""}

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

## Prueba en docker

Abrir cmd, entrar en la carpeta donde se guardan los archivos y ejecutar comandos:

- docker-compose build

- docker-compose up

- w (para abrir docker y seguir en la terminal de docker)

Una vez en la terminal de docker:

- Invoke-WebRequest -Uri http://localhost:8080/status -Headers $headers

Una vez ejecutado esto, vamos al JSON y cambiamos el puerto 8080 al 9090, guardamos y regresamos a la terminal para probar la recarga dinámica con la señal SIGHUP:

- docker kill -s HUP monitor_service (AQUI PROBAMOS EL SIGHUP, PARA RECARGA DINÁMICA)

- Invoke-WebRequest -Uri http://localhost:9090/status -Headers $headers

IMPORTANTE: Leer primero el JSON, para saber si el primer puerto a testear es el 8080 o el 9090, ya que de esto depende que pondremos en el endpoint status. 

Por último, en la terminal ejecutamos el siguiente comando para parar de forma ordenada, esto se ve reflejado el en los logs del monitor.

-docker kill -s SIGTERM monitor_service
---

## Seguridad

Se pide una contraseña, la cual está en el JSON, si no se tiene, el sistema no funciona y nos lanza un mensaje de "Unauthorized"

---

##Autor

Este proyecto es propiedad de Kevin Cárdenas Téllez
