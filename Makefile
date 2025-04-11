# Local
dev:
	@panel serve ./src/dashboard.py --show --dev
# Docker
dashboard:
	@docker build -t intersect-dashboard -f Dockerfile.dashboard .

service:
	@docker build -t intersect-service -f Dockerfile.dashboard_service .

storage:
	@docker build -t intersect-storage -f Dockerfile.storage_service .

up:
	@docker compose -f compose_local.yaml up -d

down:
	@docker compose -f compose_local.yaml down

deploy:
	@docker compose up -d

undeploy:
	@docker compose down

rmvolumes:
	@docker volume rm nsdf-intersect_intersect_bragg_volume nsdf-intersect_intersect_transition_volume nsdf-intersect_intersect_andie_volume nsdf-intersect_intersect_scientist_cloud_volume

# clients

realtime:
	@python clients/realtime_client.py
transition:
	@python clients/transition_client.py
