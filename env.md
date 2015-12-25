# Environment Data

The `env/` directory contains data that you want to provide to your services as runtime parameters. 
Currently, there's only one type of env data supported: secrets.

## Secrets

Imagine you need to pass confidential data, such as a database password or a Twitter consumer key, to a service. 
You would use kploy's environment mechanism to provide this data; just make sure that you exclude the `env` directory from your version control system (as in: add it, for example, to the [.gitignore](https://git-scm.com/docs/gitignore) file).

### Define

In the following we have two chunks of secret data, a database password `dbpassword` and a [Twitter consumer key](https://themepacific.com/how-to-generate-api-key-consumer-token-access-key-for-twitter-oauth/994/) called `tkk`. 
We want to provide these two secrets to services. First, we define them like so:

    $ echo "abadpassword" > env/dbpassword.secret
    $ echo "075d077c888bb0c5a296ad1c65e07267b77c0a9eb264b914621d6b72c770cd84" > env/tck.secret

Note that if you want kploy to treat your env data as a [Kubernetes Secret](http://kubernetes.io/v1.0/docs/user-guide/secrets.html), you MUST add a `.secret` file extension to the filename. Only then kploy picks it up and creates two entries in the (namespace-)global Secret `kploy-secrets`:

    apiVersion: v1
    kind: Secret
    metadata:
      name: kploy-secrets
    type: Opaque
    data:
      dbpassword: YWJhZHBhc3N3b3Jk
      tck: MDc1ZDA3N2M4ODhiYjBjNWEyOTZhZDFjNjVlMDcyNjdiNzdjMGE5ZWIyNjRiOTE0NjIxZDZiNzJjNzcwY2Q4NA==

In order for this to work, make sure that the file name (e.g, `tck.secret`) is a DNS subdomain as defined in [RFC 1035](http://tools.ietf.org/html/rfc1035) and that the file size (the payload) does not exceed 1 MB: you'll get a warning if this is the case and your secrets will not be deployed, as a consequence. Note also that kploy will automatically perform the required [base64](https://en.wikipedia.org/wiki/Base64) encoding.

### Use

After you've executed `kploy run` you can see the secret available:

    $ kubectl get secrets --namespace=myns
    NAME            TYPE      DATA      AGE
    kploy-secrets   Opaque    2         20s

In your app, you can consume a secret then as described below. Here, the password is only dumped to screen, but normally you'd use it for something more meaningful:

    $ cat rcs/alpine-use-secret-rc.yaml
    apiVersion: v1
    kind: ReplicationController
    metadata:
      name: use-secret-rc
    spec:
      replicas: 1
      selector:
        app: secretdump
      template:
        metadata:
          labels:
            app: secretdump
        spec:
          volumes:
          - name: global-secrets
            secret:
              secretName: kploy-secrets
          containers:
          - image: alpine:2.7
            name: alpine
            command: ["/bin/sh","-c"]
            args: ["while true ; do cat /tmp/dbpassword ; sleep 10 ; done"]
            volumeMounts:
            - mountPath: "/tmp"
              name: global-secrets

Note that the following part is fixed:


    volumes:
    - name: global-secrets
      secret:
        secretName: kploy-secrets

What you will have to provide is the mount point, that is, setting `mountPath` accordingly:

    volumeMounts:
    - mountPath: "/tmp"
      name: global-secrets

### How does it work?

What happens with `env/*.secret` files is the following: on `kploy run` (and only then) kploy will go through the list of files it finds and generate one [Kubernetes Secret](http://kubernetes.io/v1.0/docs/user-guide/secrets.html) per file it finds. It will deploy the secrets first before any services or RCs are deployed. Each secret input file `xxx.secret` is mapped to a key-value pair that can be consumed from any pod in the app's namespace.

So, you'd start out with creating a bunch of `.secret` files in `env/`

    $ ls -al env/
    drwxr-xr-x  2 mhausenblas  staff  136 25 Dec 14:48 .
    drwxr-xr-x  9 mhausenblas  staff  748 25 Dec 12:04 ..
    -rw-r--r--@ 1 mhausenblas  staff   13 25 Dec 11:48 dbpassword.secret
    -rw-r--r--  1 mhausenblas  staff   65 25 Dec 14:48 tck.secret

This would be mapped to two entries in the (namespace-)global Secret called `kploy-secrets` as so:

    $ $ ./kploy list
    Resources of app `myns/simple_app`:

    [Services and RCs]

    NAME           MANIFEST                       TYPE     STATUS    URL
    webserver-svc  services/webserver-svc.yaml    service  online    http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/services/webserver-svc
    use-secret-rc  rcs/alpine-use-secret-rc.yaml  RC       online    http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/replicationcontrollers/use-secret-rc
    webserver-rc   rcs/nginx-webserver-rc.yaml    RC       online    http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/replicationcontrollers/webserver-rc

    ================================================================================
    [Secrets]
    URL: http://52.35.162.3/service/kubernetes/api/v1/namespaces/myns/secrets/kploy-secrets
    KEY         VALUE
    tck         075d077c888bb0c5a296ad1c65e07267b77c0a9eb264b914621d6b72c770cd84
    dbpassword  abadpassword

