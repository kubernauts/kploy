# A Walkthrough Example

Let's have a look at a concrete session with the following example app and resource definitions:

    $ cat Kployfile
    apiserver: http://ma.dcos.ca1.mesosphere.com/service/kubernetes
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

Let's check our deployment:

    $ ./kploy dryrun
    Validating application `simple_app` ...

      CHECK: Is the Kubernetes cluster up & running and accessible via `http://ma.dcos.ca1.mesosphere.com/service/kubernetes`?
      \o/ ... I found 3 node(s) to deploy your wonderful app onto.

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
    Use `kploy list` to check how it's doing.

    $ ./kploy list -v
    2015-12-14T10:35:38 Listing resource status of app based on /Users/mhausenblas/Documents/repos/mhausenblas/kploy/Kployfile
    Resources of `simple_app`:
    NAME           MANIFEST                     TYPE     STATUS    URL
    webserver-svc  services/webserver-svc.yaml  service  online    http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/namespaces/default/services/webserver-svc
    webserver-rc   rcs/nginx-webserver-rc.yaml  RC       online    http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/namespaces/default/replicationcontrollers/webserver-rc

And just to make sure everything is fine, let's use `kubectl` to check the deployment:

    $ kubectl get pods
    NAME                 READY     STATUS    RESTARTS   AGE
    webserver-rc-ct8dk   1/1       Running   0          14s
    $ kubectl get rc
    CONTROLLER     CONTAINER(S)   IMAGE(S)      SELECTOR                       REPLICAS
    webserver-rc   nginx          nginx:1.9.7   app=webserver,status=serving   1
    $ kubectl get service
    NAME             LABELS                                    SELECTOR                       IP(S)          PORT(S)
    k8sm-scheduler   component=scheduler,provider=k8sm         <none>                         10.10.10.9     10251/TCP
    kubernetes       component=apiserver,provider=kubernetes   <none>                         10.10.10.1     443/TCP
    webserver-svc    <none>                                    app=webserver,status=serving   10.10.10.114   80/TCP
    $ http http://ma.dcos.ca1.mesosphere.com/service/kubernetes/api/v1/proxy/namespaces/default/services/webserver-svc/
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