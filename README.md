# NSDF-INTERSECT

This repository hosts the dashboard, dashboard service, and test clients for the [NOMAD experiment Fe2O3](https://docs.google.com/document/d/1wsDgHqE7Mg6-hM07lKuhoV7-m2mvKDEZ/edit).

#### Table of Contents

- [Dashboard](#-dashboard)
  - [Building dashboard image](#building-the-dashboard-image)
  - [Running the dashboard container](#running-the-dashboard-container)
- [Dashboard Service](#-dashboard-service)
  - [Building dashboard service image](#building-the-dashboard-service-image)
  - [Running the dashboard service container](#running-the-dashboard-service-container)
- [Testing Clients](#-testing-with-the-client)
  - [Single file client](#dashboard_clientpy)
  - [Real-time client](#realtime_clientpy)
- [Running all services](#-running-all-services)
- [Running with pre-built images](#running-with-pre-built-images)

## 📈 Dashboard

The dashboard is the visualization component for monitoring the experiment in real-time.

### 🐳 Docker

#### Building the dashboard image

To build the Docker image for the dashboard, run the following:

```bash
docker build --platform linux/amd64 -t intersect-dashboard -f Dockerfile.dashboard .
```

#### Running the dashboard container

To run the Docker container for the dashboard, execute the following:

```bash
docker run --rm -p 10042:10042 intersect-dashboard
```

## 🖥️ Dashboard service

The dashboard service uses [intersect-sdk](https://github.com/INTERSECT-SDK/python-sdk) to enable endpoints that work with message brokers (i.e RabbitMQ).
The service will include three endpoints to serve the dashboard component: `get_bragg_data`, `get_transition_data`, and `get_next_temperature`.

### 🐳 Docker

#### Building the dashboard service image

To build the Docker image for the service, run the following:

```bash
docker build -t intersect-service -f Dockerfile.dashboard_service .
```

#### Running the dashboard service container

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

Prerequisites: make sure to build the [intersect-dashboard](#building-the-dashboard-image) image and the [intersect-service](#building-the-dashboard-service-image) image.

To run all the services, you can use the `compose_local.yaml` file to run the broker, the dashboard, and the service.

```bash
docker compose -f compose_local.yaml up -d
```

To stop and clean up the services.

```bash
docker compose -f compose_local.yaml down
```

## Running with pre-built images

If you would like to get the images from the github registry, you can follow these steps:

1. If you are not logged into the ghcr, login into github registry with the following command:

```bash
docker login ghcr.io -u <your-gh-username> -p <your-pat>
```

2. Pull the pre-built dashboard and dasboard service image

```bash
docker pull ghcr.io/nsdf-fabric/intersect-dashboard:latest
docker pull ghcr.io/nsdf-fabric/intersect-service:latest
```

3. Run all services with `compose.yaml`

```bash
docker compose up -d
```

To stop and clean up the services.

```bash
docker compose down
```
