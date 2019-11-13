# Deploying to Kubernetes

In order to streamline the transition to Kubernetes, we have integrated several new CLI tools into `compose-flow`.

* `kubectl` - native CLI interactions with the Kubernetes API
* `helm` - native package manager
* `rancher` - interact with Rancher-managed clusters
* `rke` - deploy new clusters outside of Rancher itself
* `kompose` - translate `docker-compose` files into Kubernetes YAML manifests

## Rancher

Rancher provides a unified platform for managing multiple Kubernetes clusters.

### Getting Started

First, follow the [official Rancher CLI setup guide](https://rancher.com/docs/rancher/v2.x/en/cli/)
to generate an API key for your Rancher deployment and configure your local
Rancher CLI installation.

### File Types & Directory Structure

An application deployed to Rancher will generally consist of a mixture of
hand-coded _manifest_ files and standard Helm chart deployments
(which are themselves templated collections of manifests).

Manifest files are generally stored under the directory `compose/k8s`

If a repo contains only manifest files and all manifests are deployed to all environments, it is acceptable to place those files directory under the `k8s` directory.

However, if a repo contains both manifests and Helm apps, you should have a separate `compose/k8s/manifests` directory. The Helm values or answers files can either be postfixed with `-answers.yml` or `-values.yml`, or placed in corresponding folders, e.g. `compose/k8s/answers`

Note that the paths to these files must be specified properly in `compose-flow.yml` as well (see secton below)

#### Catalog App Values vs. Answers

Rancher supports either flat **`answers`** or nested **`values`** for configuring Helm charts.

To select which format to use for each app, simply specify `values` or `answers` when providing the path to each file in `compose-flow.yml`.

**Note: you must provide _either_ `values` _or_ `answers` for each app - an error will be raised if both are provided for a single app.**

##### Example Flat Answers

```yaml
ingress.enabled: true
ingress.host: my-app.example.com
```

##### Example Nested Values

```yaml
ingress:
  enabled: true
  host: my-app.example.com
```

### Configuring `compose-flow.yml` for Rancher

To configure a `compose-flow` project for deployment to Rancher, add a section to `compose-flow.yml` with the following format:

```yaml
rancher:
  # Name of the Rancher Project to deploy into
  # Cluster will be inferred from the env name passed to `-e`
  project: Default

  # Optional mapping of environment names to Rancher cluster names
  clusters:
    rancher: local
    staging: dev

  # Catalog templates to be deployed
  apps:
  - name: redis
    namespace: redis
    # Note: the chart value must be the fully qualified reference
    chart: cattle-global-data:helm-redis
    answers: ./k8s/redis-answers.yaml
    version: 9.5.4

  # Raw Kubernetes YAML to be directly applied
  # By default, the YAML must include name and namespace metadata
  # Additional parameters can also be specified for each manifest using a dict
  manifests:
  - ./redis-ingress.yaml
  - path: ./k8s/manifests/rbac.yaml
    action: replace

  # Ensure all the namespaces referenced in your
  # manifests exist and are associated with the
  # appropriate Rancher project
  # NOTE: Helm charts create their own namespace
  namespaces:
  - my-app

  # Per-environment extra apps and manifests
  extras:
    prod:
      apps:
        - name: redis-backup
          namespace: redis
          chart: custom-redis-backup-chart
          values: redis-backup-values.yaml
          version: 0.0.1
      namespaces:
        - my-extra-namespace
      manifests:
        - ./k8s/manifests/redis-lb.yaml

```

Once configured, the following command will deploy the `compose-flow` project to a Rancher-managed cluster named `dev`:

```bash
compose-flow -e dev deploy rancher
```

#### Order of Operations

As it stands, we will apply all Helm app answers/values first in the order that they
are listed, followed by all manifest files in the order that they are listed.

When there are per-cluster manifests or Helm files specified under `extras`,
these will be appended to the list of default files for the corresponding type.

So the effective order of operations is currently:
```
namespaces => default apps => extra apps => default manifests => extra manifests
```

In future we plan to add support for customizing this order of operations,
so that some manifests could be deployed before the Helm apps.

## Configuration Management

Before deploying a new project, you must ensure that a config is present for each
target environment.

### Creating A New Config

To create a new config in a cluster called `dev` for the environment `dev`,
use the standard command:
```bash
cf -e dev env edit -f
```

When deploying projects to Rancher, `compose-flow` will automatically store
environment configs as Rancher secrets in a special `compose-flow-<project>`
namespace.

Typically, the name of the environment matches the name of the cluster. If this
is not the case, see the `clusters` section above to override the `env => cluster` mapping.

This will drop you into an editor (typically `vi`) where you can specify arbitrary
key-value pairs using the standard `KEY=value` syntax of `.env` files.

### Interpolation and Jinja Templating

Any variables specified in this config will be available for interpolation using
`${}` syntax within manifests or Helm answers/values, as well as mounted to
containers via the `environment` section of `docker-compose` files.

**Note: `compose-flow.yml` does _NOT_ currently support interpolation!**

For k8s manifest files and Helm answers/values, we also support templating with
Jinja2, however we do not currently expose config variables as a proper `Context`,
so you must interpolate them first as string literals using `${}` syntax:

```yaml
lowerCaseAnswer: {{ '${UPPER_CASE_VARIABLE}' | lower }}
```

## Pulling Private Images

In order to pull a private container image, you must provide authentication
credentials for the private registry.

The first step is to create a `dockerconfigjson Secret` containing the credentials,
following the [official Kubernetes documentation on this process](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials).

_Note: if multiple repos in a single Project pull images from the same registry,
only one `Secret` is needed._

### Service Account

If you have multiple Pods pulling images from the same private registry, the best
option is to [expose the registry credentials to your Pods via a `ServiceAccount`](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#add-imagepullsecrets-to-a-service-account).

Simply add the following section to your `ServiceAccount`:

```
imagePullSecrets:
  - name: my-registry-creds
```

### Image Pull Secret

If your Pods do not already have a Service Account, or you are working with a
Helm chart, you can also [mount the `Secret` directly on the Pod spec via the
`imagePullSecrets` list.](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#create-a-pod-that-uses-your-secret)

## Namespace Termination

Namespaces cannot be removed from a cluster until all resources contained within
them are successfully removed from the cluster.

So simply calling `kubectl delete namespace old-namespace` may lead `old-namespace`
to become stuck in the `Terminating` state, waiting for other resources to be removed.

However, sometimes certain resources become stuck removing - this can be caused
by underlying cluster issues such as API version mismatches on deployed resources
or broken system components.

In the event that a namespace becomes stuck in the `Terminating` state, use this
command to identify any resources still present in that namespace:

```bash
kubectl api-resources --verbs=list --namespaced -o name \
  | xargs -n 1 kubectl get --show-kind --ignore-not-found -n <namespace>
```

## Native Kubernetes Tooling

To use `kubectl` or `helm` you must setup a `kubeconfig` file separately, with contexts
named correspoding to the target environments you wish to deploy to.

For instance, if you are targeting a cluster named `dev` and you have a context defined in
your `kubeconfig` you could simply run:

`cf -e dev helm ls`

If instead your `kubeconfig` has a context named `my-dev-cluster`, then you must
define a `kubecontexts` mapping in `compose-flow.yml` like so:
```yaml
...
kubecontexts:
  dev: my-dev-cluster
...
```

### Deploy Native Manifests with `kubectl`

To deploy YAML manifests without going through the Rancher CLI, add a
`kubectl_manifests` sections to your `compose-flow.yml` with the same format as
the `manifests` from the `rancher` section:

```yaml
kubectl_manifests:
- ./my-manifest.yaml
- ./my-other-manifests/
- path: ./my-special-file.yaml
  action: create
  raw: true
```

#### Helm Charts

To install charts via the native `helm` CLI rather than as a Rancher `app`,
provide a `helm` section in `compose-flow.yml` with the same format as the
`apps` section from `rancher`

```yaml
helm:
- name: my-chart-release
  namespace: my-namespace
  chart: my-chart
  version: "0.0.1"
  values: ../my-values.yml
```
