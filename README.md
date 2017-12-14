# DC
The `dc` command is a wrapper around [`docker-compose`](https://docs.docker.com/compose/) that codifies workflows and repeatedly used commands into rememberable, easy to type one-liners.  Can be installed from pypi:

```
pip install dc-workflows
```

## sample dc.yml

Take following `dc.yml` file:

```
profiles:
  build:
    - docker-compose.yml
    - build

  local:
    - docker-compose.yml
    - postgres

  stack:
    - docker-compose-stack.yml

  test:
    - docker-compose.yml
    - postgres
    - test

tasks:
  publish:
    command: dc --profile build -e api --tag-version --tag-docker-image --write-tag --push build

  deploy:
    command: dc --profile stack -e api --deploy

  dev-publish:
    command: dc --profile build -e dev-api --tag-version --tag-docker-image --write-tag --push build

  dev-deploy:
    command: dc --profile stack -e dev-api --deploy

  local:
    command: dc --profile local -e local-api

  local-build:
    command: dc task local build app

  test:
    command: dc --profile test --project-name api-test

  test-build:
    command: dc task test build
```

It defines four profiles; for local development, testing, building, deploying a stack to a Docker Swarm.  It also defines a number of tasks.  Notice their length and imagine consistently writing them throughout your work day.

Using `dc` with the configuration above, publishing a production image is done with the command:

```
dc task publish
```

Similarly, deploying to the Swarm:

```
dc task deploy
```

Tasks themselves are composable, such as `local` and `local-build` above.  Note that `local-build` is written as an extension to the `local` task.


### Environments

Instead of keeping environments in the repo's working copy, they are, by default, stored in `~/.docker/_environments`.  This location can be overridden with the `DC_ENVIRONMENT` environment variable.  These files are simple `key=value` pairs, such as:

```
DJANGO_DEBUG=False
DOCKER_IMAGE=roberto/api:0.0.1
```


### Tag Versioning

The `--tag-version` argument uses another utility, [tag-version](https://github.com/rca/tag-version) to generate a tag based on git tags.

The `--tag-docker-image` argument will use the `tag-version` command's result as the tag for the generated docker image.

The `--write-tag` argument will re-write the `DOCKER_IMAGE` variable in the environment file.

The `--push` argument will automatically run `docker push` when the build runs successfully.


## History
Docker Compose is great.  It allows you to put together pretty sophisticated commands that, in turn, produce some really powerful results.  The problem is remembering the commands as they can become long an cumbersome.

For example, `docker-compose` allows to overlay multiple compose files together where each subsequent compose file overrides the previous file's settings.  Repeatedly writing this on the command line is cumbersome and error-prone:

```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml [...]
```

Docker Compose also allows specifying environment variables in a `.env` file rather than hard coding them in the compose files themselves.  This is also error-prone, especially when using compose to deploy stacks, which may be production environments that use different settings for backing services such as databases.

Another issue with vanilla `docker-compose` is its inconsistency when substituting environment variables in compose.yml files; sometimes they apply, sometimes they don't.

`dc` eliminates these limitations by pre-processing the compose file and rendering out a yml file with the values found in the environment.  It also eliminates accidentally mis-writing a command, by aliasing the commands with memorable tasks.
