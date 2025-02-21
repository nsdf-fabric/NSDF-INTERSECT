# NSDF-INTERSECT

This repository hosts the dashboard, dashboard service, and test clients for the [NOMAD experiment Fe2O3](https://docs.google.com/document/d/1wsDgHqE7Mg6-hM07lKuhoV7-m2mvKDEZ/edit).

## 📈 Dashboard

The dashboard is the visualization component for monitoring the experiment in real-time.

### 🐳 Docker

#### Building the image

To build the Docker image for the dashboard, run the following:

```bash
docker build --platform linux/amd64 -t intersect-dashboard -f Dockerfile.dashboard .
```

#### Running the container

To run the Docker container for the dashboard, execute the following:

```bash
docker run --rm -p 10042:10042 intersect-dashboard
```

## 🖥️ Dashboard service

The dashboard service uses [intersect-sdk](https://github.com/INTERSECT-SDK/python-sdk) to enable endpoints that work with message brokers (i.e RabbitMQ).
The service will include three endpoints to serve the dashboard component: `get_bragg_data`, `get_transition_data`, and `get_next_temperature`.

### 🐳 Docker

#### Building the image

To build the Docker image for the service, run the following:

```bash
docker build -t intersect-service -f Dockerfile.dashboard_service .
```

#### Running the container

To run the Docker container for the service, execute the following:

```bash
docker run --rm -p 10043:10043 intersect-service
```

## 🧪 Testing with the client

To test the networking of the service and the observer on the dashboard, we can use intersect-sdk to create clients that serve the purpose of simulating
the traffic through the message broker. We have two clients.

### dashboard_client.py

This is a simple client that sends only one `.gsa` file from `GSAS` directory.

To run this client make sure you have the service running, then you can execute the following:

```bash
python dashboard_client.py
```

### realtime_client.py

This is a client that implements a message stack with different events (get_bragg_data, get_transition_data, get_next_temperature) and wait times, in order to simulate a real-time stream of events. More information
on this type of client here [counting example](https://intersect-python-sdk.readthedocs.io/en/latest/examples/counting.html).

To run this client make sure you have the service running, then you can execute the following:

```bash
python realtime_client.py
```

## 📦 Running all services

Prerequisites: make sure to build the [intersect-dashboard](https://github.com/nsdf-fabric/NSDF-INTERSECT?tab=readme-ov-file#building-the-image) image and the [intersect-service](https://github.com/nsdf-fabric/NSDF-INTERSECT?tab=readme-ov-file#building-the-image-1) image.

To run all the services, you can use the `compose.yaml` file to run the broker, the dashboard, and the service.

```bash
docker compose up -d
```

To stop and clean up the services.

```bash
docker compose down
```
