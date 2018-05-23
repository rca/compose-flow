# Compose Flow

This utility is built on top of [Docker Compose](https://docs.docker.com/compose/) and [Swarm Mode](https://docs.docker.com/engine/swarm/).  It establishes conventions for publishing Images and deploying [Stacks](https://docs.docker.com/get-started/part5/#prerequisites) that are easily shared between team members -- and bots -- who need to manage running services.


## Installation

```
pip install compose-flow
```


## A quick example and why compose-flow exists

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

It also defines some "Tasks", which are commonly run within this example project.  The `psql` task using `docker-compose` against the `local` environment expands to:

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
compose-flow -e prod publish
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

Behind the scenes this uses `docker stack` to clean up and re-deploy your code


### Using docker-compose

All of `docker-compose` is available via the `compose` subcommand, for instance, the following is the same as `docker-compose up` plus environment and compose file management:

```
compose-flow -e local compose up
```


## Managing a remote Docker Swarm

`compose-flow remote` manages connections to a remote Docker Swarm via `ssh`.  To connect to a remote swarm run the command:

```
$ compose-flow -e dev remote connect --host <user>@<host>
copy and paste the commands below or run this command wrapped in an eval statement:

export DOCKER_HOST=unix:///tmp/compose-flow-usre@host.sock
```

Running the command `export DOCKER_HOST=unix:///tmp/compose-flow-usre@host.sock` wires up your shell to the remote host.  For Bash, the command can be run like so and the export command is run automatically:

```
eval `compose-flow -e dev remote connect --host <user>@<host>`
```

Similarly to disconnect:

```
eval `compose-flow -e dev remote close`
```


## Environments

Instead of using environments written to files in the repo's working copy, they are stored on the Swarm via [`docker config`](https://docs.docker.com/engine/swarm/configs/).  They can also be kept locally on the filesystem at `~/.docker/_environments` (but then they can't be shared within a team, or accessible if you're on another workstation like work and home).  This location can be overridden with the `DC_ENVIRONMENT` environment variable.  These files are simple `key=value` pairs, such as:

```
DJANGO_DEBUG=False
DOCKER_IMAGE=roberto/api:0.0.1
```

To push up a new environment configuration, simply use:
```compose-flow -e dev env push ~/.docker/_environments/dev-project-env```
while connected to the cluster.
This works on local machines as well if docker swarm mode is turned on (`docker swarm init`):
```compose-flow -e local env push ~/.docker/_environments/local-project-env```

## Tag Versioning

Behind the scenes, versions are generated based on git tags with the [tag-version](https://github.com/rca/tag-version) utility.


# History
Docker Compose is great.  It allows you to put together pretty sophisticated commands that, in turn, produce some really powerful results.  The problem is remembering the commands as they can become long an cumbersome.

For example, `docker-compose` allows to overlay multiple compose files together where each subsequent compose file overrides the previous file's settings.  Repeatedly writing this on the command line is cumbersome and error-prone:

```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml [...]
```

Docker Compose also allows specifying environment variables in a `.env` file rather than hard coding them in the compose files themselves.  This is also error-prone, especially when using compose to deploy stacks, which may be production environments that use different settings for backing services such as databases.

Another issue with vanilla `docker-compose` is its inconsistency when substituting environment variables in compose.yml files; sometimes they apply, sometimes they don't.

`compose-flow` eliminates these limitations by pre-processing the compose file and rendering out a yml file with the values found in the environment.  It also eliminates accidentally mis-writing a command, by aliasing the commands with memorable tasks.
