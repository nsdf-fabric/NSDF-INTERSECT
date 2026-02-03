# Notes on deployments

This directory pertains strictly to Github-managed deployments on servers. It is not related to the application chart.

To execute this job, you must manually choose the `Linode Deployment` job from Github Actions; it will not execute otherwise. Check [the deploy-linode GH workflow](../.github/workflows/deploy-linode.yml) to see the full deployment manifest.

Note that we do NOT publish this directory's Helm chart to a repository, we simply use it on the command-line.

## Secrets

These are stored as Github secrets.

- `LINODE_B64_KUBECONFIG` - base64-encoded Kubeconfig for the Kubernetes cluster
- `LINODE_B64_SECRET_VALUES` - base64-encoded secret values we apply additionally to the deployment
- `LINODE_B64_DIAL_VALUES` - base64-encoded secret values to apply to the Dial chart deployment

### Secrets values yaml file

To update `LINODE_B64_SECRET_VALUES` or `LINODE_B64_DIAL_VALUES`, use `examples.secrets-values.yaml` or `dial-example.secret-values.yaml` respectively, as a template for new yaml (say `new-secrets.yaml`) and...

1. Update the passwords secrets where `CHANGEME` occurs
   - To create random, you can use: `python -c "import secrets; print(secrets.token_urlsafe())"`

2. Base64 encode the yaml file: `base64 new-secret.yaml`
3. Update the GitHub Actions `LINODE_B64_SECRET_VALUES`/`LINODE_B64_DIAL_VALUES` with this encoded string from step (2):
   - link: https://github.com/nsdf-fabric/NSDF-INTERSECT/settings/secrets/actions

4. Save changes!
