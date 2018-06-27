# Compose Flow

This utility is built on top of [Docker Compose](https://docs.docker.com/compose/) and [Swarm Mode](https://docs.docker.com/engine/swarm/).  It establishes conventions for publishing Images, deploying [Stacks](https://docs.docker.com/get-started/part5/#prerequisites) across multiple installations (like separate dev and prod Swarms), and working with service containers that are easily shared between team members -- and bots -- who need to manage running services.


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

`compose-flow` can also work across multiple Swarms, for example, when you are developing locally on your own laptop and are deploying to a remote swarm.  You can also have separate installations for dev and prod.  This can be accomplished by defining a "remoteconfig":

```
compose-flow remoteconfig edit
```

Then you could paste something like the following:

```
remotes:
  dev:
    ssh: ${CF_REMOTE_USER}@dev-swarm-manager-1

  prod:
    ssh: ${CF_REMOTE_USER}@prod-swarm-manager-1
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

# History
Docker Compose is great.  It allows you to put together pretty sophisticated commands that, in turn, produce some really powerful results.  The problem is remembering the commands as they can become long an cumbersome.

For example, `docker-compose` allows to overlay multiple compose files together where each subsequent compose file overrides the previous file's settings.  Repeatedly writing this on the command line is cumbersome and error-prone:

```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml [...]
```

Docker Compose also allows specifying environment variables in a `.env` file rather than hard coding them in the compose files themselves.  This is also error-prone, especially when using compose to deploy stacks, which may be production environments that use different settings for backing services such as databases.

Another issue with vanilla `docker-compose` is its inconsistency when substituting environment variables in compose.yml files; sometimes they apply, sometimes they don't.

`compose-flow` eliminates these limitations by pre-processing the compose file and rendering out a yml file with the values found in the environment.  It also eliminates accidentally mis-writing a command, by aliasing the commands with memorable tasks.
