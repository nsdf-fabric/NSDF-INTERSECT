dashboard:
	@docker build --platform linux/amd64 -t intersect-dashboard -f Dockerfile.dashboard .

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
	@docker volume rm nsdf-intersect_intersect_bragg_data nsdf-intersect_intersect_next_temperature_data nsdf-intersect_intersect_scientist_cloud_volume nsdf-intersect_intersect_transition_data
