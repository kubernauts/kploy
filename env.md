# Environment Data

The `env/` directory contains data that you want to provide to your services as runtime parameters. 
Currently, there's only one type of env data supported: secrets.

## Secrets

Imagine you need to pass confidential data, such as a database password or a Twitter consumer key, to a service. 
You would use kploy's environment mechanism to provide this data; just make sure that you exclude the `env` directory from your version control system (as in: add it, for example, to the [.gitignore](https://git-scm.com/docs/gitignore) file).

In the following we have two chunks of secret data, a database password `dbpassword` and a [Twitter consumer key](https://themepacific.com/how-to-generate-api-key-consumer-token-access-key-for-twitter-oauth/994/) called `tkk`:

    $ echo "abadpassword" > env/dbpassword.secret
    $ echo "075d077c888bb0c5a296ad1c65e07267b77c0a9eb264b914621d6b72c770cd84" > env/tkk.secret

Note that if you want kploy to treat your env data as [Kubernetes Secrets](http://kubernetes.io/v1.0/docs/user-guide/secrets.html) you MUST add a `.secret` file extension. Only then kploy understands it as a secret and it will create two Kubernetes Secrets as follows out of it:

    apiVersion: v1
    kind: Secret
    metadata:
      name: simple_app_secrets
    type: Opaque
    data:
      dbpassword: YWJhZHBhc3N3b3Jk
      tkk: MDc1ZDA3N2M4ODhiYjBjNWEyOTZhZDFjNjVlMDcyNjdiNzdjMGE5ZWIyNjRiOTE0NjIxZDZiNzJjNzcwY2Q4NA==

In order for this to work, make sure that the file name (like: `tkk.secret`) is a DNS subdomain as defined in [RFC 1035](http://tools.ietf.org/html/rfc1035) and that the file size (the payload) does not exceed 1 MB: you'll get a warning if this is the case and your secrets will not be deployed, as a consequence. Note also that kploy will automatically perform the required [base64](https://en.wikipedia.org/wiki/Base64) encoding.

TBD: usage example

TBD: integrate http://kubernetes.sh/kploy/