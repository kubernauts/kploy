# kploy

[![version](https://img.shields.io/pypi/v/kploy.svg)](https://pypi.python.org/pypi/kploy/)
[![downloads](https://img.shields.io/pypi/dm/kploy.svg)](https://pypi.python.org/pypi/kploy/)
[![build status](https://travis-ci.org/kubernauts/kploy.svg?branch=master)](https://travis-ci.org/kubernauts/kploy)

Welcome to kploy, an opinionated Kubernetes deployment system for appops.
We use convention over configuration in order to enable you to run 
microservices-style applications with Kubernetes as simple and fast as possible.

## Usage

See [kubernetes.sh/kploy](http://kubernetes.sh/kploy/) for installation and usage.

## Dependencies

All of the following are included in the setup:

* The [pyk](https://github.com/kubernauts/pyk) toolkit
* Pretty-print tabular data with [tabulate](https://pypi.python.org/pypi/tabulate)

## Releases

- [x] In v0.9: adds `scale` command (autoscale yet TBD)
- [x] In v0.8: adds `debug` command, some refactoring
- [x] In v0.7: adds support for environment data: automagic handling of Kubernetes Secrets on `run`
- [x] In v0.6: `export` command creates snapshot of app; can be imported when doing `init`
- [x] In v0.5: simple support for helm charts via remotes (`*.url`)
- [x] In v0.4: support for namespaces (via `namespace` field in Kployfile)
- [x] In v0.3: moved to Kubernauts org, new location is https://github.com/kubernauts/kploy 
- [x] In v0.2: `init` command and app management: resources via `list` and runtime statistics via `stats`
- [x] In v0.1: `dryrun` and `run` commands

## Roadmap

With v0.9 kploy is now considered beta. This means the goal is now to stabilize the API,
gather usage experience and community feedback. See the [issue](https://github.com/kubernauts/kploy/issues) 
list for further planned features (mainly for 2.x).