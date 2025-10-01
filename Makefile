COMPOSE := docker compose
.PHONY: up upb down logs logs-f ps bash db-psql redis-cli rebuild
up:
	$(COMPOSE) up -d

upb:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --no-color

logs-f:
	$(COMPOSE) logs -f --no-color

ps:
	$(COMPOSE) ps

bash:
	$(COMPOSE) exec web bash || $(COMPOSE) run --rm web bash

db-psql:
	$(COMPOSE) exec db psql -U ${DB_USER} -d ${DB_NAME}

redis-cli:
	$(COMPOSE) exec redis redis-cli

rebuild:
	$(COMPOSE) build --no-cache web

celery-bash:
	$(COMPOSE) exec worker bash