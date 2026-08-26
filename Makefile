# Dev
.PHONY: dev
dev:
	@panel serve ./src/dashboard.py --show --dev

.PHONY: all
all:
	@docker build -t intersect-dashboard:test services/nsdf_intersect_dashboard
	@docker build -t intersect-service:test services/nsdf_intersect_service
	@docker compose -f compose_local.yaml up -d

# Docker
.PHONY: dashboard
dashboard:
	@docker build -t intersect-dashboard services/nsdf_intersect_dashboard

.PHONY: service
service:
	@docker build -t intersect-service services/nsdf_intersect_service

.PHONY: storage
storage:
	@docker build -t intersect-storage services/nsdf_intersect_storage 


.PHONY: up
up:
	@docker compose -f compose_local.yaml up -d

.PHONY: down
down:
	@docker compose -f compose_local.yaml down

.PHONY: rmvolumes
rmvolumes:
	@docker volume rm nsdf-intersect_intersect_bragg_volume nsdf-intersect_intersect_transition_volume nsdf-intersect_intersect_andie_volume nsdf-intersect_intersect_scientist_cloud_volume

# clients
.PHONY: realtime
realtime:
	@python clients/realtime_client.py
.PHONY: transition
transition:
	@python clients/transition_client.py
