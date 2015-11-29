# kploy

Welcome to kploy, an opinionated Kubernetes deployment system for appops.
We use convention over configuration in order to enable you to run 
microservices-style applications with Kubernetes as simple and fast as possible.

## Dependencies

* The [pyk](https://github.com/mhausenblas/pyk) toolkit

## Preparing your deployment

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

## Deploy your app

To validate your deployment run the following command in `$KPLOY_DEMO_HOME`:

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

To actually deploy your app, do:

    $ ./kploy run -v
    2015-11-29T08:16:43 Trying to run /Users/mhausenblas/Documents/repos/mhausenblas/kploy/Kployfile
    2015-11-29T08:16:43 Deploying RC /Users/mhausenblas/Documents/repos/mhausenblas/kploy/rcs/nginx-webserver-rc.yaml
    2015-11-29T08:16:43 From /Users/mhausenblas/Documents/repos/mhausenblas/kploy/rcs/nginx-webserver-rc.yaml I created the RC "webserver-rc" at /api/v1/namespaces/default/replicationcontrollers/webserver-rc
    2015-11-29T08:16:44 Deploying service /Users/mhausenblas/Documents/repos/mhausenblas/kploy/services/webserver-svc.yaml
    2015-11-29T08:16:44 From /Users/mhausenblas/Documents/repos/mhausenblas/kploy/services/webserver-svc.yaml I created the service "webserver-svc" at /api/v1/namespaces/default/services/webserver-svc
    ================================================================================
    
    OK, I've deployed `simple_app`

And just to make sure everything is fine, let's use `kubectl` to check the deployment:

    $ dcos kubectl get pods
    NAME                 READY     STATUS    RESTARTS   AGE
    webserver-rc-ct8dk   1/1       Running   0          14s
    $ dcos kubectl get rc
    CONTROLLER     CONTAINER(S)   IMAGE(S)      SELECTOR                       REPLICAS
    webserver-rc   nginx          nginx:1.9.7   app=webserver,status=serving   1
    $ dcos kubectl get service
    NAME             LABELS                                    SELECTOR                       IP(S)          PORT(S)
    k8sm-scheduler   component=scheduler,provider=k8sm         <none>                         10.10.10.9     10251/TCP
    kubernetes       component=apiserver,provider=kubernetes   <none>                         10.10.10.1     443/TCP
    webserver-svc    <none>                                    app=webserver,status=serving   10.10.10.114   80/TCP
    $ dcos kubectl get endpoints
    NAME             ENDPOINTS
    k8sm-scheduler   10.0.3.45:25504
    kubernetes       10.0.3.45:25502
    webserver-svc    10.0.3.45:1032
    $ http http://52.10.201.177/service/kubernetes/api/v1/proxy/namespaces/default/services/webserver-svc/
    HTTP/1.1 200 OK
    Accept-Ranges: bytes
    Connection: keep-alive
    Content-Length: 612
    Content-Type: text/html
    Date: Sun, 29 Nov 2015 08:18:49 GMT
    Etag: "564b4b31-264"
    Last-Modified: Tue, 17 Nov 2015 15:43:45 GMT
    Server: openresty/1.7.10.2
    
    <!DOCTYPE html>
    <html>
    <head>
    <title>Welcome to nginx!</title>
    . . .

There you go, you just deployed an app on Kubernetes, with a single command. Well done!

Note that I've used the following files for testing:

    $ cat Kployfile
    apiserver: http://52.10.201.177/service/kubernetes
    author: Michael Hausenblas
    name: simple_app
    source: https://github.com/mhausenblas/kploy

    $ cat rcs/nginx-webserver-rc.yaml
    apiVersion: v1
    kind: ReplicationController
    metadata:
      name: webserver-rc
    spec:
      replicas: 1
      selector:
        app: webserver
        status: serving
      template:
        metadata:
          labels:
            app: webserver
            guard: pyk
            status: serving
        spec:
          containers:
          - image: nginx:1.9.7
            name: nginx
            ports:
              - containerPort: 80

    $ cat services/webserver-svc.yaml
    apiVersion: v1
    kind: Service
    metadata:
      name: webserver-svc
    spec:
      selector:
        app: webserver
        status: serving
      ports:
        - port: 80
          targetPort: 80
          protocol: TCP

## To Do

- [x] Implement basic functionality (dry run and run)
- [ ] Add init command (creates Kployfile and placeholder RC and service file)
- [ ] Add app management (list of apps, check apps status)
- [ ] Add tear down command
- [ ] Add dependency management
- [ ] Add Travis build
- [ ] Add deep validation for `dryrun`, that is validate RCs and services via the API server
