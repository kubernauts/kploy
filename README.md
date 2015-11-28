# kploy

Welcome to kploy, an opinionated Kubernetes deployment system for appops.
We use convention over configuration in order to enable you to run 
microservices-style applications with Kubernetes as simple and fast as possible.

## Dependencies

* The [pyk](https://github.com/mhausenblas/pyk) toolkit

## Preparation

In the following I assume you're in a directory we will call `$KPLOY_DEMO_HOME`.

First you create a file `Kployfile` (formatted in YAM) with the following content in `$KPLOY_DEMO_HOME`:

    apiserver: http://localhost:8080
    name: test_app
    author: Your Name
    source: https://github.com/yourusername/therepo

Then you create two sub-directories in `$KPLOY_DEMO_HOME`, called `rcs` and `services`. 

Last but not least you copy your `Replication Controller` and `Service` manifests into these two directories, like so:

    $KPLOY_DEMO_HOME
    ├── rcs
        └── asimple_replication_controller.yaml
    └── services
        └── asimple_service.yaml

## Deployment

To validate your deployment run the following command in `$KPLOY_DEMO_HOME`:

    ./kploy dryrun

To actually deploy your app, do:

    ./kploy run

## Demo