"""
The kploy commons (utility) functions.

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2015-12-12
@status: init
"""

import os
import logging
import requests
import zipfile
from time import sleep

from pyk import toolkit
from pyk import util

PODS_UP_DELAY_IN_SEC = 5 # how long to wait before trying to own RC's pods
EXPORT_EXT = ".kploy"

def _fmt_cmds(cmds):
    """
    Formats the supported commands nicely.
    """
    keys = sorted(cmds.keys())
    fk = "\n"
    for k in keys:
        fk += "`" + k + "`, "
    return fk

def _connect(api_server, debug):
    """
    Tries to connect to cluster and ping it.
    If successful it returns the Pyk client.
    """
    try:
        pyk_client = toolkit.KubeHTTPClient(kube_version="1.1", api_server=api_server, debug=debug)
        pyk_client.execute_operation(method="GET", ops_path="/api/v1")
    except:
        print("\nCan't connect to the Kubernetes cluster at %s\nCheck the `apiserver` setting in your Kployfile, your Internet connection or maybe it's a VPN issue?" %(api_server))
        sys.exit(1)
    return pyk_client

def _visit(dir_name, resource_name, cache_remotes=False):
    """
    Walks a given directory and returns list of resource manifest files (in YAML format).
    It will also dereference and download remotes (manifest files that end in a `.url`).
    """
    flist = []
    logging.debug("Visiting %s" %dir_name)
    for _, _, file_names in os.walk(dir_name):
        for afile in file_names:
            if not afile.endswith(".url"): # potentially a manifest
                if afile.endswith(".yaml"): # for now only YAML files are interpreted as valid input format
                    logging.debug("Got %s manifest %s" %(resource_name, afile))
                    flist.append(afile)
                else:
                    logging.debug("Ignoring unknown file %s for now" %(afile))
            else: # we have a remote, for example, `abc.yaml.url`
                remote_ref_file_name = os.path.join(dir_name, afile)
                file_name = _download_remote(remote_ref_file_name, do_cache=cache_remotes)
                logging.debug("Skipping remote %s manifest %s" %(resource_name, file_name))
    return flist

def _dump(alist):
    """
    Dumps a list to the INFO logger.
    """
    for litem in alist:
        logging.info("-> %s" %litem)

def _get_pods_of_rc(pyk_client, rc, namespace):
    """
    Retrieves a list of all pods a certain RC manages.
    """
    pods_selectors = rc["spec"]["selector"]
    sel = ""
    for k, v in pods_selectors.iteritems():
        sel += "".join([k, "%3D", v , ","])
    if sel.endswith(","):
        sel = sel[:-1]
    pods_of_rc_path = "".join(["/api/v1/namespaces/", namespace, "/pods?labelSelector=", sel])
    pods = pyk_client.execute_operation(method="GET", ops_path=pods_of_rc_path)
    pods_list = pods.json()["items"]
    return pods_list

def _deploy(pyk_client, namespace, here, dir_name, alist, resource_name, verbose):
    """
    Deploys resources based on manifest files. Currently the following resources are supported:
    replication controllers, services.
    """
    for litem in alist:
        file_name = os.path.join(os.path.join(here, dir_name), litem)
        if verbose: logging.info("Deploying %s %s" %(resource_name, file_name))
        if resource_name == "service":
            _, res_path = pyk_client.create_svc(manifest_filename=file_name, namespace=namespace)
        elif resource_name == "RC":
            _, res_path = pyk_client.create_rc(manifest_filename=file_name, namespace=namespace)
        if verbose: logging.info("Now trying to own %s" %(res_path))
        _own_resource(pyk_client, res_path, verbose)
        res = pyk_client.describe_resource(res_path)
        logging.debug(res.json())
        # now make sure that a RC's pods are also owned:
        if resource_name == "RC":
            print("Waiting %d sec before looking for pods of RC %s" %(PODS_UP_DELAY_IN_SEC, res_path))
            sleep(PODS_UP_DELAY_IN_SEC)
            pods_list = _get_pods_of_rc(pyk_client, res.json(), namespace)
            for pod in pods_list:
                if verbose: logging.info("Now trying to own %s" %(pod["metadata"]["selfLink"]))
                _own_resource(pyk_client, pod["metadata"]["selfLink"], verbose)

def _destroy(pyk_client, namespace, here, dir_name, alist, resource_name, verbose):
    """
    Destroys resources based on manifest files. Currently the following resources are supported:
    replication controllers, services.
    """
    for litem in alist:
        file_name = os.path.join(os.path.join(here, dir_name), litem)
        if file_name.endswith(".url"):
            file_name = _deref_remote(file_name)
        if verbose: logging.info("Trying to destroy %s %s" %(resource_name, file_name))
        res_manifest, _  = util.load_yaml(filename=file_name)
        res_name = res_manifest["metadata"]["name"]
        if resource_name == "service":
            res_path = "".join(["/api/v1/namespaces/", namespace, "/services/", res_name])
        elif resource_name == "RC":
            res_path = "".join(["/api/v1/namespaces/", namespace, "/replicationcontrollers/", res_name])
            res = pyk_client.describe_resource(res_path)
            if res.status_code == 404:  # the replication controller is already gone
                break                   # ... don't try to scale down
            else:
                resource = res.json()
                resource["spec"]["replicas"] = 0
                if verbose: logging.info("Scaling down RC %s to 0" %(res_path))
                pyk_client.execute_operation(method='PUT', ops_path=res_path, payload=util.serialize_tojson(resource))
        else: return None
        pyk_client.delete_resource(resource_path=res_path)

def _check_status(pyk_client, resource_path):
    """
    Checks the status of a resources.
    """
    res = pyk_client.describe_resource(resource_path)
    logging.debug(res.json())
    if res.status_code == 200: return "online"
    else: return "offline"

def _own_resource(pyk_client, resource_path, verbose):
    """
    Labels a resource with `guard=pyk` so that it can be
    selected with `?labelSelector=guard%3Dpyk`.
    """
    res = pyk_client.describe_resource(resource_path)
    resource = res.json()
    if "labels" in resource["metadata"]:
        labels = resource["metadata"]["labels"]
    else:
        labels = {}
    labels["guard"] = "pyk"
    resource["metadata"]["labels"] = labels
    if verbose: logging.info("Owning resource, now labeled with: %s" %(resource["metadata"]["labels"]))
    pyk_client.execute_operation(method='PUT', ops_path=resource_path, payload=util.serialize_tojson(resource))

def _create_ns(pyk_client, namespace, verbose):
    """
    Creates a new namespace, unless it's `default`.
    """
    if namespace == "default":
        return
    else:
        ns = {}
        ns["kind"] = "Namespace"
        ns["apiVersion"] = "v1"
        ns["metadata"] = {}
        ns["metadata"]["name"] = namespace
        ns["metadata"]["labels"] = {}
        ns["metadata"]["labels"]["guard"] = "pyk"
        if verbose: logging.info("Created namespace: %s" %(ns))
        pyk_client.execute_operation(method='POST', ops_path="/api/v1/namespaces", payload=util.serialize_tojson(ns))

def _download_remote(remote_ref_file_name, do_cache=False):
    """
    Resolves a remote reference file by downloading its content.
    """
    remote_content = ""
    real_file_name = _deref_remote(remote_ref_file_name)
    if do_cache: # re-use local copies of remotes
        if not os.path.exists(real_file_name): # download remote if we don't have it locally yet
            print "Downloading %s since I do not have it locally" %real_file_name
            _download_by_URL(remote_ref_file_name, real_file_name)
        else: # don't download if there is already a local copy (use cached version)
            logging.debug("Using cached version")
    else: # always download remotes
        _download_by_URL(remote_ref_file_name, real_file_name)
    return real_file_name

def _download_by_URL(remote_ref_file_name, real_file_name):
    """
    Downloads the content of a file by URL.
    """
    with open(remote_ref_file_name, 'r') as remote_ref_file:
        res_URL = remote_ref_file.read().strip()
        remote_content = requests.get(res_URL).text
        logging.debug(remote_content)
    with open(real_file_name, "w") as real_file:
        real_file.write(remote_content)

def _deref_remote(remote_ref_file_name):
    """
    Dereferences a remote file name: /path/to/abc.yaml.url -> /path/to/abc.yaml
    """
    real_file_name , _ = os.path.splitext(remote_ref_file_name)
    logging.debug(real_file_name)
    return real_file_name

def _export_init(here, deployment_descriptor, appname):
    """
    Creates the archive file to export the app into.
    """
    archive_filename = "".join([appname, EXPORT_EXT])
    kployfile = deployment_descriptor
    logging.debug("Trying to create app archive %s" %(archive_filename))
    archive_file = zipfile.ZipFile(archive_filename, mode='w')
    logging.debug("Trying to add deployment descriptor %s" %(kployfile))
    archive_file.write(kployfile)
    return (archive_filename, archive_file)

def _export_add(archive_file, filename):
    """
    Adds a file to the app archive.
    """
    logging.debug("Trying to add %s to app archive" %(filename))
    archive_file.write(filename)

def _export_done(archive_file):
    """
    Wraps up app archive generation
    """
    archive_file.close()
