# Another example and why compose-flow exists

Take following configuration file located at `compose/compose-flow.yml` within your project:

```
profiles:
  prod:
    - docker-compose.yml

  dev:
    - docker-compose.yml

  local:
    - docker-compose.yml
    - docker-compose.local.yml


tasks:
  psql:
    command: compose-flow compose exec postgres psql -U postgres postgres

  psql-drop-test-db:
    command: compose-flow compose exec postgres /bin/bash -c 'echo "DROP DATABASE test_db;" | psql -U postgres postgres'
```

It defines three "Profiles" for local, development, and production deployments.  They all share a base `docker-compose.yml` file, but you may need additional services locally that you don't need for development and production environments.  In the example above, `dev` and `prod` don't need a postgres service (they probably use a standalone system or a hosted database like RDS), but a postgres service is needed locally.

It also defines "Tasks", which are commonly run within this example project.  The `psql` task using `docker-compose` against the `local` environment expands to something resembling:

```
$ cp /path/to/local.env ./.env
$ docker-compose -f docker-compose.yml -f docker-compose.local.yml exec postgres psql -U postgres postgres
```

(Note: remember to replace `.env` when you deploy to prod...)

The equivalent command with `compose-flow` is:

```
$ compose-flow -e local task psql
```

The clear advantage is brevity.  A second advantage is not managing environment files yourself.  `compose-flow` also validates the runtime environment.  It checks that the environment defined in your compose files has a corresponding value at runtime to ensure all the variables are, in fact, defined.


### Publishing

Publishing is simple.  For example, to publish a production image:

```
compose-flow publish
```

Behind the scenes a unique version is generated for your Docker Image using `git tag`, for example, `1.3.0-3-gf67c2b8-compose-flow`.  The unique docker image is used in your deployment by simply specifying the docker image as a variable in your compose file, for instance:

```
version: '3.3'
services:
  app:
    build: ..
    image: ${DOCKER_IMAGE}
  [...]
```

The rest is taken care of.


### Deployment

Deployment is also simple:

```
compose-flow -e prod deploy
```

Behind the scenes this uses `docker stack` to clean up and re-deploy your code to the production Swarm cluster using production environment variables.


### Using docker-compose

All of `docker-compose` is available via the `compose` subcommand, for instance, the following is the same as `docker-compose up` plus environment and compose file management:

```
compose-flow -e local compose up
```

So why use `compose-flow` here instead of `docker-compose` directly?

- the docker-compose file is rendered using the `local` profile that is defined in `compose/compose-flow.yml`
- `${}` variables anywhere in the compose configuration are processed and rendered into the docker-compose yml file


## Managing a remote Docker Swarm

`compose-flow` can also work across multiple Swarms, for example, when you are developing locally on your own laptop and are deploying to a remote Swarm.  You can also define separate Swarms for dev and prod.  This can be accomplished by adding a `remotes` section to `~/.compose/config.yml`:

```
remotes:
  dev:
    ssh: username@dev-swarm-manager-1

  prod:
    ssh: username@prod-swarm-manager-1
```

With this configuration in place the above `deploy` example would deploy to `prod-swarm-manager-1`, while using `compose-flow -e dev deploy` would deploy to `dev-swarm-manager-1`.


## Executing commands in service containers

Sometimes it's necessary to run one-off commands in a service container running in a Swarm.  When deploying services to multi-node Swarms, Docker takes care of allocating that service container onto a particular node.  Over time that container can move about, and tracking down where that container is can be teidous.  This scenario is handled with the command:

```
compose-flow -e dev service exec app /bin/bash
```

Behind the scenes, this command finds the container for the dev app service, makes an SSH connection to the machine that is running that container and executes the command `/bin/bash`.  You'll be dropped into an interactive bash shell on the running service container!


## Environments

Instead of using environments written to files in the repo's working copy, they are stored on the Swarm via [`docker config`](https://docs.docker.com/engine/swarm/configs/).  These configurations are simple `key=value` pairs, such as:

```
DJANGO_DEBUG=False
DOCKER_IMAGE=roberto/api:0.0.1
```

To push up a new environment configuration, simply use:
```compose-flow -e dev env push ~/.docker/_environments/dev-project-env```
while connected to the cluster.
This works on local machines as well if docker swarm mode is turned on (`docker swarm init`):
```compose-flow -e local env push ~/.docker/_environments/local-project-env```

Environments can also be printed to the screen with the `cat` action:

```
compose-flow -e local env cat
```

And they can be edited in your `$EDITOR` with the `edit` action:

```
compose-flow -e local env edit
```


### Runtime environment variables

Sometimes it's necessary to inject an environment variable at runtime rather than hard-coding it into the config, for example, using the Jenkins `BUILD_NUMBER` variable.  This can be specified in the config with:

```
BUILD_NUMBER=runtime://
```

This will set the config's `BUILD_NUMBER` variable with the value of the `$BUILD_NUMBER` environment variable when the `compose-flow` command is run.

If the variable names differ, it's possible to specify what the runtime name is:

```
RUNTIME_USER=runtime://USER
```


### Variable substitutions

Variable substitution works in the environment as well, with the caveat that it will only allow substitutions for variables defined in the env file itself.  So, for example, if you want to substitute in the runtime user's username, first define a runtime variable:

```
RUNTIME_USER=runtime://USER
USER_VOL=${RUNTIME_USER}-data
```


## Working with a dirty working copies

Compose-flow is strict when it comes to pushing out changes with a dirty working copy.  This is so that anything that is deployed to a running environment should be traceable back to a commit in git.  But sometimes that is not desired.

For example, perhaps all you want to do is connect to a running container and your local working copy has some modifications.  Or you are working in a local environment where you want the changes to be dirty yet have the ability to run the software.


### The --dirty arg

Compose-flow can be run like so to, for instance, work locally with a dirty working copy:

```
compose-flow -e local --dirty compose build
```

Or to exec into a running service:

```
compose-flow -e prod --dirty service exec app /bin/bash
```


### configuring a dirty environment

Usually it's always okay for a local development environment to be dirty.  In such cases, it's better to simply set it in `compose/compose-flow.yml` once and not have to worry about setting `--dirty` in every command.  The following can be added to your .yml file:

```
options:
  local:
    dirty_working_copy_okay: true
```


## Tag versioning

Behind the scenes, versions are generated based on git tags with the [tag-version](https://github.com/rca/tag-version) utility.


## Expanding services

Sometimes replicas aren't exactly what is needed.  For example, there are some systems that spin up a number of workers, but each worker needs to work as its own unit instead of being part of a round-robin pool as `replicas` work by default.

It is possible to "expand" a service out into individual services, for example, the following configuration:

```
services:
  foo:
    build: ..
    image: ${DOCKER_IMAGE}
    environment:
      - PORT=8880
      - UI_PORT=9990
    ports:
      - 8000:8000
    deploy:
      replicas: 2


compose_flow:
  expand:
    foo:
      increment:
        env:
          - PORT
          - UI_PORT
        ports:
          source_port: true
          destination_port: true
```

will expand out to:

```
services:
  foo1:
    build: ..
    image: ${DOCKER_IMAGE}
    environment:
      - PORT=8880
      - UI_PORT=9990
    ports:
      - 8000:8000
    deploy:

  foo2:
    build: ..
    image: ${DOCKER_IMAGE}
    environment:
      - PORT=8881
      - UI_PORT=9991
    ports:
      - 8001:8001
    deploy:
```

## Deploying to Kubernetes

In order to streamline the transition to Kubernetes, we have integrated several new CLI tools into `compose-flow`.

* `kubectl` - native CLI interactions with the Kubernetes API
* `helm` - native package manager
* `rancher` - interact with Rancher-managed clusters
* `rke` - deploy new clusters outside of Rancher itself
* `kompose` - translate `docker-compose` files into Kubernetes YAML manifests

### Rancher

To configure a project for deployment to Rancher, add a section to `compose-flow.yml` with the following format:

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
    chart: helm-redis
    answers: redis-answers.yaml
    version: 4.0.1

  # Raw Kubernetes YAML to be directly applied
  # By default, the YAML must include name and namespace metadata
  # Additional parameters can also be specified for each manifest using a dict
  manifests:
  - ./redis-ingress.yaml
  - path: ./rbac.yaml
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
          answers: redis-backup-answers.yaml
          version: 0.0.1
      namespaces:
        - my-extra-namespace
      manifests:
        - ./redis-lb.yaml

```

Once configured, ensure your local Rancher CLI is logged in with a valid token, then run the following command to deploy a `compose-flow` project to a Rancher-managed cluster named `dev`:

```bash
compose-flow -e dev deploy rancher
```

### Native Kubernetes Tooling

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

#### Deploy Native Manifests with `kubectl`

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
  answers: ../my-answers.yml
```

# History
Docker Compose is great.  It allows you to put together pretty sophisticated commands that, in turn, produce some really powerful results.  The problem is remembering the commands as they can become long an cumbersome.

For example, `docker-compose` allows to overlay multiple compose files together where each subsequent compose file overrides the previous file's settings.  Repeatedly writing this on the command line is cumbersome and error-prone:

```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml [...]
```

Docker Compose also allows specifying environment variables in a `.env` file rather than hard coding them in the compose files themselves.  This is also error-prone, especially when using compose to deploy stacks, which may be production environments that use different settings for backing services such as databases.

Another issue with vanilla `docker-compose` is its inconsistency when substituting environment variables in compose.yml files; sometimes they apply, sometimes they don't.

`compose-flow` eliminates these limitations by pre-processing the compose file and rendering out a yml file with the values found in the environment.  It also eliminates accidentally mis-writing a command, by aliasing the commands with memorable tasks.
