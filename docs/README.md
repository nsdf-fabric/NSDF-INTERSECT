# NSDF Helm charts

This repo is meant to manage publishment of the NSDF-INTERSECT Helm charts.

There are currently two charts:

- `intersect-core-linode`: This chart contains intersect-core, includes the message broker and proxy-http-server.
- `nsdf-intersect`: This chart contains NSDF services developed for the neutron diffraction experiments (NOMAD, POWGEN), includes the dashboard (bragg peak, transition plot visualization),
  and an intersect service to consume messages from the broker.

## Chart usage

[Helm](https://helm.sh) must be installed to use the charts. Please refer to Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

`helm repo add <alias> https://nsdf-fabric.github.io/NSDF-INTERSECT/`

If you had already added this repo earlier, run `helm repo update` to retrieve the latest versions of the packages. You can then run `helm search repo <alias>` to see the charts.

Available charts:

- `intersect-core-linode`
- `nsdf-intersect`

To install a chart:

```bash
helm install <chart-name> <alias>/<chart-name>
```

To uninstall the chart:

```bash
helm delete <chart-name>
```
