# kploy

Welcome to kploy, an opinionated Kubernetes deployment system for appops.
We use convention over configuration in order to enable you to run 
microservices-style applications with Kubernetes as simple and fast as possible.

## Dependencies

* The [pyk](https://github.com/mhausenblas/pyk) toolkit

## Preparation

In the following I assume you're in a directory we will call `$KPLOY_DEMO_HOME`.

First you create a file `Kployfile`. This file must be formatted in [YAML](http://yaml.org/) and exist in `$KPLOY_DEMO_HOME`.
It has to have at least the following entries (only `apiserver` and `name` are interpreted right now):

    apiserver: http://localhost:8080
    author: Your Name
    name: test_app
    source: https://github.com/yourusername/therepo

Next, you create two sub-directories in `$KPLOY_DEMO_HOME`, called `rcs` and `services`.  Last but not least you copy your
`Replication Controller` and `Service` manifests into these two directories, like so:

    $KPLOY_DEMO_HOME
    ├── rcs
        └── asimple_replication_controller.yaml
    └── services
        └── asimple_service.yaml

Now you're ready to validate your deployment.

## Deployment

To validate your deployment run the following command in `$KPLOY_DEMO_HOME`:

    $ ./kploy dryrun
    Validating application `test_app` ...

      CHECK: Is the Kubernetes cluster up & running and accessible via `http://localhost:8080`?
      \o/ ... I found 1 node(s) to deploy your wonderful app onto.

      CHECK: Are there RC and service manifests available around here?
             I found 1 RC manifest(s) in /Users/mhausenblas/Documents/repos/mhausenblas/kploy/rcs
             I found 1 service manifest(s) in /Users/mhausenblas/Documents/repos/mhausenblas/kploy/services
      \o/ ... I found both RC and service manifests to deploy your wonderful app!
    ================================================================================

    OK, we're looking good! You're ready to deploy your app with `kploy run` now :)
    

To actually deploy your app, do:

    $ ./kploy run

## Demo

TBD


## To Do

- [ ] Add Travis build
- [ ] Add deep validation for `dryrun`, that is validate RCs and services via the API server
