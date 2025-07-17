# Local
dev:
	@panel serve ./src/dashboard.py --show --dev
# Docker
dashboard:
	@docker build -t intersect-dashboard:uv services/nsdf_intersect_dashboard

service:
	@docker build -t intersect-service:uv services/nsdf_intersect_service

storage:
	@docker build -t intersect-storage:uv services/nsdf_intersect_storage 

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
