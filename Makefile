.PHONY: build up test8080 changeport sighup test9090 full

# 1. Construir y levantar los servicios
build:
	sudo docker-compose build

up: build
	sudo docker-compose up -d
	@sleep 5

# 2. Probar en puerto 8080
test8080:
	curl http://localhost:8080/status 
	@sleep 2

# 3. Cambiar config.json (de 8080 a 9090)
changeport:
	sed -i 's/"rest_port": 8080/"rest_port": 9090/' config.json
	@cat config.json | grep rest_port
	@sleep 1

# 4. Enviar señal SIGHUP
sighup:
	sudo docker kill -s HUP monitor_service
	@sleep 5

# 5. Probar en puerto 9090
test9090:
	curl http://localhost:9090/status 

# 6. Flujo completo automatizado
full: up test8080 changeport sighup test9090
	@echo "✅ Todo el flujo ejecutado correctamente."

