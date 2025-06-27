# Helm chart

Most templates are based off of the [Bitnami Charts Template](https://github.com/bitnami/charts/tree/main/template/])

We also use the Bitnami Common library to try and standardize some boilerplate across all charts.

## Configure config yaml + node port

Example of `intersectConfig` for values.yaml:

```yaml
intersectConfig:
  data_stores:
    minio:
      - host: minio
        username: DATA_STORE_USER
        password: DATA_STORE_PASSWORD
        port: 9000

  brokers:
    - host: broker
      username: BROKER_USER
      password: BROKER_PASSWORD
      port: 1883
      protocol: mqtt3.1.1

  hierarchy:
    organization: nsdf
    facility: cloud
    system: diffraction
    subsystem: dashboard
    service: dashboard-service
```

Example of `storageConfig` for values.yaml:

```yaml
storageConfig:
  PROFILE_NAME: my-profile-name
  ENDPOINT_URL: my-endpoint-url
  BUCKET_NAME: my-bucket-name
  ACCESS_KEY_ID: my-access-key-id
  SECRET_ACCESS_KEY: my-secret-access-key
```

Example of node port for dashboard (served on 30180 of cluster):

```
dashboard:
  service:
    type: NodePort
    nodePort: 30180
```

## Linting

You'll need helm to be installed on your system, but you don't need to have a Kubernetes server configuration set up.

1. Change directory into `chart` if you haven't already.
2. `helm dependency update` (if Chart.lock already exists, use `helm dependency build` instead; if `charts` directory exists in this directory, you can either skip this step or first remove .tgz files from `charts`)
3. `helm lint .` (alternately, `helm template --validate .` or, if you can connect to a remote server, `helm upgrade -n <NAMESPACE> --dry-run --debug <RELEASE> .`)
