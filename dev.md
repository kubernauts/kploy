# Development and Operations

What follows is a description of advanced uses of kploy in the development and operations phases.

## Debugging

With kploy you can live-debug any Pod of your application by using the `debug` command.
What happens is the following: kploy uses a variant of [this recipe](https://gist.github.com/mhausenblas/b74742ad10f756e680c5)
to take the offending Pod offline (essentially, kploy removes all labels and then the RC automatically kicks in to replace the Pod in question).

So, if you want to debug a certain Pod you first need to get an idea which Pods are running:

    $ ./kploy stats
    Runtime stats for app `myns/simple_app`:
    
    [Your app's pods]
    
    NAME                 HOST       STATUS    URL
    use-secret-rc-ilsxn  10.0.3.74  Running   http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/pods/use-secret-rc-ilsxn
    webserver-rc-h2mtw   10.0.3.75  Running   http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/pods/webserver-rc-h2mtw
    webserver-rc-t48sa   10.0.3.74  Running   http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/pods/webserver-rc-t48sa
    webserver-rc-vc8ak   10.0.3.76  Running   http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/pods/webserver-rc-vc8ak
    
    ================================================================================
    [Nodes used by your app]
    
    IP         HOST OS         CONTAINER RUNTIME    CAPACITY (PODS, CPU, MEM)    URL
    10.0.3.74  CoreOS 835.8.0  docker://1.8.3       40, 4, 13891Mi               http://52.35.162.3/service/kubernetes/api/v1/nodes/10.0.3.74
    10.0.3.75  CoreOS 835.8.0  docker://1.8.3       40, 4, 13891Mi               http://52.35.162.3/service/kubernetes/api/v1/nodes/10.0.3.75
    10.0.3.76  CoreOS 835.8.0  docker://1.8.3       40, 4, 13891Mi               http://52.35.162.3/service/kubernetes/api/v1/nodes/10.0.3.76
    
    ================================================================================

Let's assume that in the above scenario the Pod `webserver-rc-t48sa` somewhat acts badly and you want to debug it. So you do:

    $ ./kploy debug webserver-rc-t48sa
    Trying to take Pod webserver-rc-t48sa offline for debugging ...
    Waiting 5 sec before looking for pods of RC /api/v1/namespaces/myns/replicationcontrollers/webserver-rc
    ================================================================================
    
    OK, the Pod `webserver-rc-t48sa` is offline. Now you can, for example, use `kubectl exec` now to debug it.

Note that after the debugging session you'll have to get rid of the Pod yourself manually via `kubectl delete pod webserver-rc-t48sa`.