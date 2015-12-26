# Development and Operations

What follows is a description of advanced uses of kploy in the development and operations phases.

## Debugging

With kploy you can live-debug any Pod of your application by using the `debug` command.
What happens in a nutshell is the following: kploy uses a variant of [this recipe](https://gist.github.com/mhausenblas/b74742ad10f756e680c5)
to take the offending Pod offline. Note that after the debugging session you'll have to get
rid of the Pod yourself manually via `kubectl delete pod xxx`.

    $ ./kploy stats
    
    $ ./kploy debug webserver-rc-29pxj