# Glossary

## Profile

Profiles are a merged set of smaller docker-compose files as they are listed in the `profiles` section of
`compose-flow.yml`.  They allow the docker-compose configuration to be broken down into smaller, digestible chunks.


## Config

TODO: this is poorly named.  Naming stems from the `docker config` command and doesn't convey its purpose.


## Environment

The environment contains settings that are configurable between deployments.  This includes:

- the `environment` section of the compose file
- any ${foo} variables anywhere in the compose file


## Project Name

This is the same as `docker-compose --project-name`


## Remote

The name of a remote Swarm or Rancher cluster.


## Remote Config

This configuration defines remote clusters to operate on.  They can either be Swarm or Rancher clusters.
