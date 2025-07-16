.PHONY: build up prueba1 prueba2 changeport sighup full

API_KEY=123

build:
	sudo docker-compose build

up: build
	sudo docker-compose up -d
	@sleep 5

prueba1:
	@PORT=$$(sed -n 's/.*"rest_port": \([0-9]*\).*/\1/p' config.json); \
	echo "Probando puerto $$PORT..."; \
	curl -H "X-API-KEY: $(API_KEY)" http://localhost:$$PORT/status
	@sleep 2

changeport:
	@CUR=$$(sed -n 's/.*"rest_port": \([0-9]*\).*/\1/p' config.json); \
	if [ "$$CUR" = "8080" ]; then NEW=9090; else NEW=8080; fi; \
	sed -i 's/"rest_port": '$$CUR'/"rest_port": '$$NEW'/' config.json; \
	echo "Puerto cambiado a $$NEW en config.json"

sighup:
	sudo docker kill -s HUP monitor_service
	@sleep 5

prueba2:
	@PORT=$$(sed -n 's/.*"rest_port": \([0-9]*\).*/\1/p' config.json); \
	echo "Llamando a puerto $$PORT..."; \
	curl -H "X-API-KEY: $(API_KEY)" http://localhost:$$PORT/status
	@sleep 2

full: up prueba1 changeport sighup prueba2
	@echo "Todo el flujo ejecutado correctamente."
