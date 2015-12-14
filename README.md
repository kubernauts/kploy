# kploy

[![version](https://img.shields.io/pypi/v/kploy.svg)](https://pypi.python.org/pypi/kploy/)
[![downloads](https://img.shields.io/pypi/dm/kploy.svg)](https://pypi.python.org/pypi/kploy/")
[![build status](https://travis-ci.org/mhausenblas/kploy.svg?branch=master)](https://travis-ci.org/mhausenblas/kploy)

Welcome to kploy, an opinionated Kubernetes deployment system for appops.
We use convention over configuration in order to enable you to run 
microservices-style applications with Kubernetes as simple and fast as possible.

<a href="http://www.youtube.com/watch?feature=player_embedded&v=TJpucj4v4iE" target="_blank">
 <img src="http://img.youtube.com/vi/TJpucj4v4iE/0.jpg" alt="kploy demo" width="240" border="1" />
</a>

See also the [walkthrough example](examples.md) for further details to get started.

## Dependencies

All of the following are included in the setup:

* The [pyk](https://github.com/mhausenblas/pyk) toolkit
* Pretty-print tabular data with [tabulate](https://pypi.python.org/pypi/tabulate)

## Prepare your deployment

In the following I assume you're in a directory that we will call `$KPLOY_DEMO_HOME`, going forward.

First you create a file `Kployfile` which must be formatted in [YAML](http://yaml.org/) and be located in `$KPLOY_DEMO_HOME`.
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

Now you're ready to validate your deployment. Note that you can also use the `init` command to create the required scaffolding, like so: 

    $ ./kploy init
    ================================================================================
    
    OK, I've set up the Kployfile deployment file and created necessary directories.
    Now edit the deployment file and copy manifests into the respective directories.
    
    $ ls -al
    drwxr-xr-x  10 mhausenblas  staff   748B 13 Dec 17:41 .
    drwxr-xr-x  23 mhausenblas  staff   816B  5 Dec 07:44 ..
    -rw-r--r--   1 mhausenblas  staff    85B 13 Dec 17:41 Kployfile
    drwxr-xr-x   2 mhausenblas  staff    68B 13 Dec 17:41 rcs
    drwxr-xr-x   2 mhausenblas  staff    68B 13 Dec 17:41 services
    
    $ cat Kployfile
    apiserver: http://localhost:8080
    author: CHANGE_ME
    name: CHANGE_ME
    source: CHANGE_ME

## Deploy your app

To validate your deployment use the `dryrun` command:

    $ ./kploy dryrun
    Validating application `test_app` ...

      CHECK: Is the Kubernetes cluster up & running and accessible via `http://52.10.201.177/service/kubernetes`?
      \o/ ... I found 1 node(s) to deploy your wonderful app onto.

      CHECK: Are there RC and service manifests available around here?
             I found 1 RC manifest(s) in /Users/mhausenblas/Documents/repos/mhausenblas/kploy/rcs
             I found 1 service manifest(s) in /Users/mhausenblas/Documents/repos/mhausenblas/kploy/services
      \o/ ... I found both RC and service manifests to deploy your wonderful app!
    ================================================================================

    OK, we're looking good! You're ready to deploy your app with `kploy run` now :)

Looks fine, so to actually deploy your app, do:

    $ ./kploy run
    2015-12-14T10:34:45 From /Users/mhausenblas/Documents/repos/mhausenblas/kploy/services/webserver-svc.yaml I created the service "webserver-svc" at /api/v1/namespaces/default/services/webserver-svc
    2015-12-14T10:34:46 From /Users/mhausenblas/Documents/repos/mhausenblas/kploy/rcs/nginx-webserver-rc.yaml I created the RC "webserver-rc" at /api/v1/namespaces/default/replicationcontrollers/webserver-rc
    ================================================================================

    OK, I've deployed `simple_app`.
    Use `kploy list` to check how it's doing.

There you go, you just deployed an app on Kubernetes, with a single command. Well done!

## Manage your app

To see how your app is doing, use the `list` command. All services and RCs of the app will be listed, along with their status
(`online` means it's deployed and running) and their resource URL:

    $ ./kploy list
    Resources of `simple_app`:
    NAME           MANIFEST                     TYPE     STATUS    URL
    webserver-svc  services/webserver-svc.yaml  service  online   http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/namespaces/default/services/webserver-svc
    webserver-rc   rcs/nginx-webserver-rc.yaml  RC       online   http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/namespaces/default/replicationcontrollers/webserver-rc

Hint: if you want to learn about any of the supported commands, simply add an `explain` before the command, for example:

    $ ./kploy explain list
    list:
        Lists apps and their status.

If you want to learn more about how your app uses the cluster, use the `stats` command:

    $ ./kploy stats
    Stats for `simple_app`:

    [Your app's pods]

    NAME                HOST             STATUS    URL
    webserver-rc-29pxj  167.114.218.157  Running   http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/namespaces/default/pods/webserver-rc-29pxj

    ================================================================================
    [Nodes used by your app]

    IP               HOST OS                CONTAINER RUNTIME    CAPACITY (PODS, CPU, MEM)    URL
    167.114.218.157  CentOS Linux 7 (Core)  docker://1.8.2       40, 40, 256708Mi             http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/nodes/167.114.218.157

    ================================================================================


## Tear down your app

To tear down your app, use the `destroy` command, for example:

    $ ./kploy destroy
    2015-12-14T10:23:42 Deleted resource /api/v1/namespaces/default/services/webserver-svc
    2015-12-14T10:23:42 Deleted resource /api/v1/namespaces/default/replicationcontrollers/webserver-rc
    ================================================================================
    
    OK, I've destroyed `simple_app`

## To Do

- [x] Add app management (list of apps, check apps status)
- [x] Add init command (creates Kployfile and placeholder RC and service file)
- [x] Add destroy command
- [x] Add stats command, showing utilization, containers state summary
- [ ] Add scale command
- [ ] Add support for namespaces (field in Kployfile)
- [ ] Add deep validation for `dryrun` via validating RCs and services through API server
- [ ] Add dependency management (via labels)
