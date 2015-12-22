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

- [x] In v0.5: simple support for helm charts via remotes
- [x] In v0.4: support for namespaces (field in Kployfile)
- [x] In v0.3: moved to Kubernauts org, new location is https://github.com/kubernauts/kploy 
- [x] In v0.2: stats command, showing utilization, containers state summary and destroy command
- [x] In v0.2: init command (creates Kployfile and placeholder RC and service file) and app management (list of apps, check apps status)
- [x] In v0.1: dryrun and run commands

## Roadmap

- [ ] Add export command (result can be imported with `myexampleapp.kploy` in CWD when doing `kploy init`)
- [ ] Add environment handling (Secrets, etc.) via additional sub-directory
- [ ] Add debug command, implementing https://gist.github.com/mhausenblas/b74742ad10f756e680c5
- [ ] Add scale command
- [ ] Add support for Jobs

See also the [issue](https://github.com/kubernauts/kploy/issues) list for further planned features.