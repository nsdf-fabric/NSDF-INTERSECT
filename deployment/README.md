# Notes on deployments

This directory pertains strictly to Github-managed deployments on servers. It is not related to the application chart.

To execute this job, you must manually choose the `Linode Deployment` job from Github Actions; it will not execute otherwise. Check [the deploy-linode GH workflow](../.github/workflows/deploy-linode.yml) to see the full deployment manifest.

Note that we do NOT publish this directory's Helm chart to a repository, we simply use it on the command-line.

## Secrets

These are stored as Github secrets.

- `LINODE_B64_KUBECONFIG` - base64-encoded Kubeconfig for the Kubernetes cluster
- `LINODE_B64_SECRET_VALUES` - base64-encoded secret values we apply additionally to the deployment
