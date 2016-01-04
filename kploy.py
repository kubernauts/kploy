#!/usr/bin/env python

"""
The kploy main UX.

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2015-11-29
@status: beta
"""

import argparse
import logging
import os
import sys
import pprint
import base64
import kploycommon

from tabulate import tabulate
from pyk import toolkit
from pyk import util

DEBUG = False    # you can change that to enable debug messages ...
VERBOSE = False  # ... but leave this one in peace
DEPLOYMENT_DESCRIPTOR = "Kployfile"
EXPORT_ARCHIVE_FILENAME = "app.kploy"
SECRETS_FILE_EXT = ".secret"
RC_DIR = "rcs/"
SVC_DIR = "services/"
ENV_DIR = "env/"
KAR_BASE_URL = "http://registry.kploy.net/api/v1"
VALID_WORKSPACE_PREFIXES = (
    "http://github.com/",
    "https://github.com/"
)

if DEBUG:
  FORMAT = "%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]"
  logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="%Y-%m-%dT%I:%M:%S")
else:
  FORMAT = "%(asctime)-0s %(message)s"
  logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%dT%I:%M:%S")
  logging.getLogger("requests").setLevel(logging.WARNING)

class InvalidWorkspaceError(Exception):
    """
    Error when executing the `push` command: The `source` field in the `Kployfile` file is neither a GitHub username or repo URL.
    """
    pass

class NoSuchAppError(Exception):
    """
    Error when executing the `pull` command: The supplied app ID is invalid, that is, the app does not exist (at least not in this workspace).
    """
    pass

def cmd_dryrun(param):
    """
    Looks for a `Kployfile` file in the current directory and tries
    to validate its content, incl. syntax validation and mock execution.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Trying to execute a dry run on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        print("Validating application `%s/%s` ..." %(kploy["namespace"], kploy["name"]))
        
        print("\n  CHECK: Is the Kubernetes cluster up & running and accessible via `%s`?" %(kploy["apiserver"]))
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        nodes = pyk_client.execute_operation(method="GET", ops_path="/api/v1/nodes")
        if VERBOSE: logging.info("Got node list %s " %(util.serialize_tojson(nodes.json())))
        print("  \o/ ... I found %d node(s) to deploy your wonderful app onto." %(len(nodes.json()["items"])))
        
        print("\n  CHECK: Are there RC and service manifests available around here?")
        try:
            rcs = os.path.join(here, RC_DIR)
            logging.debug("Asserting %s exists" %(os.path.dirname(rcs)))
            assert os.path.exists(rcs)
            rc_manifests_confirmed = kploycommon._visit(rcs, "RC", cache_remotes=kploy["cache_remotes"])
            print("         I found %s RC manifest(s) in %s" %(int(len(rc_manifests_confirmed)), os.path.dirname(rcs)))
            if VERBOSE: kploycommon._dump(rc_manifests_confirmed)

            services = os.path.join(here, SVC_DIR)
            logging.debug("Asserting %s exists" %(os.path.dirname(services)))
            assert os.path.exists(services)
            svc_manifests_confirmed = kploycommon._visit(services, "service", cache_remotes=kploy["cache_remotes"])
            print("         I found %s service manifest(s) in %s" %(int(len(svc_manifests_confirmed)), os.path.dirname(services)))
            if VERBOSE: kploycommon._dump(svc_manifests_confirmed)
            print("  \o/ ... I found both RC and service manifests to deploy your wonderful app!")
        except:
            print("No RC and/or service manifests found to deploy your app. You can use `kploy init` to create missing artefacts.")
            sys.exit(1)
    except (IOError, IndexError, KeyError) as e:
        print("Something went wrong:\n%s" %(e))
        sys.exit(1)
    print(80*"=")
    print("\nOK, we're looking good! You're ready to deploy your app with `kploy run` now :)\n")

def cmd_run(param):
    """
    Looks for a `Kployfile` file in the current directory and tries to run it.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Trying to run %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        # set up a Namespace for this app:
        kploycommon._create_ns(pyk_client, kploy["namespace"], VERBOSE)
        # set up a Secrets for this app:
        env = os.path.join(here, ENV_DIR)
        secrets = {}
        logging.debug("Visiting %s" %env)
        for _, _, file_names in os.walk(env):
            for afile in file_names:
                if afile.endswith(SECRETS_FILE_EXT):
                    logging.debug("Got a secret input: %s" %(afile))
                    key = os.path.splitext(afile)[0]
                    logging.debug("Secret key: %s" %(key))
                    with open(os.path.join(env, afile), "r") as sec_file:
                        raw_data = sec_file.read().strip()
                    logging.debug("Secret data: %s" %(raw_data))
                    val = base64.b64encode(raw_data)
                    logging.debug("Secret base64 encoded data: %s" %(val))
                    secrets[key] = val
        kploycommon._create_secrets(pyk_client, kploy["name"], kploy["namespace"], secrets, VERBOSE)
        # collect Services and RCs ...
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_manifests_confirmed = kploycommon._visit(services, 'service', cache_remotes=kploy["cache_remotes"])
        rc_manifests_confirmed = kploycommon._visit(rcs, 'RC', cache_remotes=kploy["cache_remotes"])
        # ... and deploy them:
        kploycommon._deploy(pyk_client, kploy["namespace"], here, SVC_DIR, svc_manifests_confirmed, 'service', VERBOSE)
        kploycommon._deploy(pyk_client, kploy["namespace"], here, RC_DIR, rc_manifests_confirmed, 'RC', VERBOSE)
    except (Exception) as e:
        print("Something went wrong deploying your app:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)
    print(80*"=")
    print("\nOK, I've deployed `%s/%s`.\nUse `kploy list` and `kploy stats` to check how it's doing." %(kploy["namespace"], kploy["name"]))

def cmd_list(param):
    """
    Lists app resources and their status.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Listing resource status of app based on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        print("Resources of app `%s/%s`:\n" %(kploy["namespace"], kploy["name"]))
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_list = kploycommon._visit(services, 'service', cache_remotes=True)
        rc_list = kploycommon._visit(rcs, 'RC', cache_remotes=True)
        res_list = []
        # gather Services status:
        print("[Services and RCs]\n")
        for svc in svc_list:
            svc_manifest, _  = util.load_yaml(filename=os.path.join(here, SVC_DIR, svc))
            svc_name = svc_manifest["metadata"]["name"]
            svc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/services/", svc_name])
            svc_URL = "".join([kploy["apiserver"], svc_path])
            svc_status = kploycommon._check_status(pyk_client, svc_path)
            res_list.append([svc_name, os.path.join(SVC_DIR, svc), "service", svc_status, svc_URL])
        # gather RC status:
        for rc in rc_list:
            rc_manifest, _  = util.load_yaml(filename=os.path.join(here, RC_DIR, rc))
            rc_name = rc_manifest["metadata"]["name"]
            rc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/replicationcontrollers/", rc_name])
            rc_URL = "".join([kploy["apiserver"], rc_path])
            rc_status = kploycommon._check_status(pyk_client, rc_path)
            res_list.append([rc_name, os.path.join(RC_DIR, rc), "RC", rc_status, rc_URL])
        print(tabulate(res_list, ["NAME", "MANIFEST", "TYPE", "STATUS", "URL"], tablefmt="plain"))
        # gather Secrets status:
        print("\n" + 80*"=")
        print("[Secrets]")
        sec_list = []
        secret_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/secrets/kploy-secrets"])
        sec_URL = "".join([kploy["apiserver"], secret_path])
        secret = pyk_client.describe_resource(secret_path)
        if secret.status_code == 200:
            print("URL: %s" %(sec_URL))
            secret_data = secret.json()["data"]
            for k, v in secret_data.iteritems():
                sec_list.append([k, base64.b64decode(v)])
            print(tabulate(sec_list, ["KEY", "VALUE"], tablefmt="plain"))
        else:
            print("No env data deployed.")
        print("\n" + 80*"=")
    except (Exception) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

def cmd_init(param):
    """
    Creates a dummy `Kployfile` file in the current directory sets up the directories.
    """    
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if not param:
        param = EXPORT_ARCHIVE_FILENAME
        if os.path.exists(kployfile):
            print("Hey! %s already exists.\nI'm not going to destroy existing work. #kthxbye" %(kployfile))
            sys.exit(1)
    archivefile = os.path.join(here, param)
    if not os.path.exists(SVC_DIR):
        os.makedirs(SVC_DIR)
    if not os.path.exists(RC_DIR):
        os.makedirs(RC_DIR)
    if os.path.exists(archivefile): # set up via archive
        if VERBOSE: logging.info("Detected archive %s" %(archivefile))
        kploycommon._init_from_archive(archivefile)
        print(80*"=")
        print("\nOK, I've set up the app from archive.\nYou can now validate it with `kploy dryrun`\n")
    else: # create from scratch
        if VERBOSE: logging.info("Setting up app %s " %(kployfile))
        ikploy = {}
        ikploy["apiserver"] = "http://localhost:8080"
        ikploy["author"] = "CHANGE_ME"
        ikploy["cache_remotes"] = False
        ikploy["name"] = "CHANGE_ME"
        ikploy["namespace"] = "default"
        ikploy["source"] = "CHANGE_ME"
        if VERBOSE: logging.info("%s" %(ikploy))
        util.serialize_yaml_tofile(kployfile, ikploy)
        print(80*"=")
        print("\nOK, I've set up the `%s`, the app deployment descriptor from scratch and created necessary directories." %(DEPLOYMENT_DESCRIPTOR))
        print("Now edit the app deployment descriptor and copy manifests into the respective directories.\n")

def cmd_destroy(param):
    """
    Destroys the app, removing all resources.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Trying to destroy app based on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        # delete all services and RCs:
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_manifests_confirmed = kploycommon._visit(services, 'service', cache_remotes=True)
        rc_manifests_confirmed = kploycommon._visit(rcs, 'RC', cache_remotes=True)
        kploycommon._destroy(pyk_client, kploy["namespace"], here, SVC_DIR, svc_manifests_confirmed, 'service', VERBOSE)
        kploycommon._destroy(pyk_client, kploy["namespace"], here, RC_DIR, rc_manifests_confirmed, 'RC', VERBOSE)
        # delete secrets:
        secret_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/secrets/kploy-secrets"])
        pyk_client.delete_resource(resource_path=secret_path)
        # delete the namespace:
        ns_path = "".join(["/api/v1/namespaces/", kploy["namespace"]])
        pyk_client.delete_resource(resource_path=ns_path)
    except (Exception) as e:
        print("Something went wrong destroying your app:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)
    print(80*"=")
    print("\nOK, I've destroyed `%s/%s`\n" %(kploy["namespace"], kploy["name"]))

def cmd_stats(param):
    """
    Shows cluster utilization and provides summary of the pods' state, from the point of view of your app.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Providing stats for your app based on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        print("Runtime stats for app `%s/%s`:" %(kploy["namespace"], kploy["name"]))
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        # provide container summary:
        print("\n[Your app's pods]\n")
        guarded_pods_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/pods?labelSelector=guard%3Dpyk"])
        pods = pyk_client.execute_operation(method="GET", ops_path=guarded_pods_path)
        pods_list = pods.json()["items"]
        if not pods_list:
            print "No pods are online. "
            return
        pod_details = []
        used_nodes = []
        for pod in pods_list:
            if pod["status"]["hostIP"] not in used_nodes:
                used_nodes.append(pod["status"]["hostIP"])
            pod_details.append([
                pod["metadata"]["name"],
                pod["status"]["hostIP"],
                pod["status"]["phase"],
                "".join([kploy["apiserver"], pod["metadata"]["selfLink"]])
            ])
        print(tabulate(pod_details, ["NAME", "HOST", "STATUS", "URL"], tablefmt="plain"))
        print("\n" + 80*"=")
        # provide utilization info:
        print("[Nodes used by your app]\n")
        nodes = pyk_client.execute_operation(method="GET", ops_path="/api/v1/nodes")
        nodes_list = nodes.json()["items"]
        node_ips = []
        for node in nodes_list:
            if node["metadata"]["name"] in used_nodes:
                node_ips.append([
                    node["metadata"]["name"],
                    node["status"]["nodeInfo"]["osImage"],
                    node["status"]["nodeInfo"]["containerRuntimeVersion"],
                    node["status"]["capacity"]["pods"] + ", " + node["status"]["capacity"]["cpu"] + ", " + node["status"]["capacity"]["memory"],
                    "".join([kploy["apiserver"], node["metadata"]["selfLink"]])
                ])
        print(tabulate(node_ips, ["IP", "HOST OS", "CONTAINER RUNTIME", "CAPACITY (PODS, CPU, MEM)", "URL"], tablefmt="plain"))
        print("\n" + 80*"=")
    except (Exception) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

def cmd_export(param):
    """
    Creates an archive of all relevant app files, incl. Kployfile and manifest directories.
    You can use the resulting archive then with `kploy init` to bootstrap you app in a different location.
    """
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Exporting app based on content from %s " %(here))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        if not param:
            param = EXPORT_ARCHIVE_FILENAME
        archive_filename, archive_file = kploycommon._export_init(here, DEPLOYMENT_DESCRIPTOR, param)
        print("Adding content of app `%s/%s` to %s" %(kploy["namespace"], kploy["name"], archive_filename))
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_list = kploycommon._visit(services, 'service', cache_remotes=True)
        rc_list = kploycommon._visit(rcs, 'RC', cache_remotes=True)
        res_list = []
        for svc in svc_list:
            svc_file_name = os.path.join(SVC_DIR, svc)
            kploycommon._export_add(archive_file, svc_file_name)
        for rc in rc_list:
            rc_file_name = os.path.join(RC_DIR, rc)
            kploycommon._export_add(archive_file, rc_file_name)
        kploycommon._export_done(archive_file)
    except (Exception) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

def cmd_debug(pod_name):
    """
    Enables you to debug a Pod by taking it offline through removing the `guard=pyk` label.
    Usage: `debug pod`, for example, `debug webserver-42abc`.
    """
    if not pod_name:
        print("Sorry, I need a Pod name in order to do my work. Do a `kploy stats` first to glean the Pod name you want to debug, e.g. `webserver-42abc`.")
        print("With the Pod name you can then run `kploy debug webserver-42abc` to take the Pod offline and subsequently for example use `kubectl exec` to enter the Pod.")
        sys.exit(1)
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    print("Trying to take Pod %s offline for debugging ..." %(pod_name))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        pod_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/pods/", pod_name])
        pod = pyk_client.describe_resource(pod_path)
        resource = pod.json()
        resource["metadata"]["labels"] = {}
        logging.debug("Removed guard label from Pod, now labeled with: %s" %(resource["metadata"]["labels"]))
        pyk_client.execute_operation(method='PUT', ops_path=pod_path, payload=util.serialize_tojson(resource))
        # now we just need to make sure that the newly created Pod is again owned by kploy:
        rc_name = pod_name[0:pod_name.rfind("-")] # NOTE: this is a hack, it assumes a certain generator pattern; need to figure a better way to find a Pod's RC
        logging.debug("Generating RC name from Pod: %s" %(rc_name))
        rc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/replicationcontrollers/", rc_name])
        rc = pyk_client.describe_resource(rc_path)
        kploycommon._own_pods_of_rc(pyk_client, rc, kploy["namespace"], rc_path, VERBOSE)
    except (Exception) as e:
        print("Something went wrong when taking the Pod offline:\n%s" %(e))
        sys.exit(1)
    print(80*"=")
    print("\nOK, the Pod %s is offline. Now you can, for example, use `kubectl exec` now to debug it." %(pod_name))

def cmd_scale(scale_def):
    """
    Enables you to scale an RC up or down by setting the number of replicas.
    Usage: `scale rc=replica_count`, for example, `scale webserver-rc=10`.
    """
    if not scale_def:
        print("Sorry, I need a scale definition in order to do my work. Do a `kploy list` first to glean the RC name you want to scale, e.g. `webserver-rc`.")
        print("With the RC name you can then run `kploy scale webserver-rc=5` to scale the respective RC to 5 replicas.")
        sys.exit(1)
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    try:
        rc_name = scale_def.split("=")[0]
        replica_count = int(scale_def.split("=")[1])
    except (Exception) as e:
        print("Can't parse scale definition `%s` due to: %s" %(scale_def, e))
        print("The scale definition should look as follows: `rc=replica_count`, for example, `scale webserver-rc=10`.")
        sys.exit(1)
    print("Trying to scale RC %s to %d replicas" %(rc_name, replica_count))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        rc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/replicationcontrollers/", rc_name])
        rc = pyk_client.describe_resource(rc_path)
        resource = rc.json()
        old_replica_count = resource["spec"]["replicas"]
        if VERBOSE: logging.info("Scaling RC from %d to %d replicas" %(old_replica_count, replica_count))
        logging.debug("RC about to be scaled: %s" %(resource))
        resource["spec"]["replicas"] = replica_count
        pyk_client.execute_operation(method='PUT', ops_path=rc_path, payload=util.serialize_tojson(resource))
        # and make sure that the newly created Pods are owned by kploy (on scale up)
        if replica_count > old_replica_count:
            logging.debug("Scaling up, trying to own new Pods")
            rc = pyk_client.describe_resource(rc_path)
            kploycommon._own_pods_of_rc(pyk_client, rc, kploy["namespace"], rc_path, VERBOSE)
    except (Exception) as e:
        print("Something went wrong when scaling RC:\n%s" %(e))
        sys.exit(1)
    print(80*"=")
    print("OK, I've scaled RC %s to %d replicas. You can do a `kploy stats` now to verify it." %(rc_name, replica_count))

def cmd_push(param):
    """
    Exports the app and uploads it to KAR, the kploy app registry (https://github.com/kubernauts/kploy.net).
    Note that you MUST set the `source` field in the `Kployfile` file to a GitHub username or repo URL,
    otherwise the push operation will fail. For example, you can use `source : https://github.com/mhausenblas`
    if you don't have a project repo for the app (yet) or `source : https://github.com/mhausenblas/abc`
    if you want to explicitly set the app's project repo.
    """    
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    archivefile = os.path.join(here, "".join([".", EXPORT_ARCHIVE_FILENAME]))
    app_link = KAR_BASE_URL
    if VERBOSE: logging.info("Creating temporary app archive %s" %(archivefile))
    cmd_export(archivefile)
    if VERBOSE: logging.info("Trying to upload %s" %(archivefile))
    try:
        kploy, _ = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        if kploy["source"].startswith(VALID_WORKSPACE_PREFIXES):
            print("Using %s as the app's workspace" %(kploy["source"]))
            res = kploycommon._push_app_archive(kploy["source"], archivefile, KAR_BASE_URL, VERBOSE)
            app_link = "".join([res.json()["selfLink"], "?workspace=", kploy["source"]])
        else:
            raise InvalidWorkspaceError 
    except (InvalidWorkspaceError) as iwe:
        print(iwe.__doc__)
        print("To learn how to fix this, run `kploy explain push`")
        sys.exit(1)
    except (Exception) as e:
        print("Something went wrong pushing your app to the registry:\n%s" %(e))
        sys.exit(1)
    finally:
        if os.path.exists(archivefile):
           os.remove(archivefile) 
    print(80*"=")
    print("\nOK, I've successfully pushed the app archive to the registry:")
    print("%s" %(app_link))
    print("\nTo list the available app(s), use the `kploy pull` command.\n")


def cmd_pull(param):
    """
    Lists apps or downloads + imports app from KAR, the kploy app registry (https://github.com/kubernauts/kploy.net).
    Note that you MUST set the `source` field in the `Kployfile` file to a GitHub username or repo URL,
    otherwise the pull operation will fail. For example, you can use `source : https://github.com/mhausenblas`
    if you don't have a project repo for the app (yet) or `source : https://github.com/mhausenblas/abc`
    if you want to explicitly set the app's project repo.
    
    Without argument all available apps are listed, with an argument the respective app is first
    downloaded and then imported (as with `kploy init`):
    
    kploy pull
    
    kploy pull $ID
    """    
    here = os.path.realpath(".")
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    archivefile = os.path.join(here, "".join([".", EXPORT_ARCHIVE_FILENAME]))
    app_link = KAR_BASE_URL
    try:
        kploy, _ = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        if kploy["source"].startswith(VALID_WORKSPACE_PREFIXES):
            print("Using %s as the app's workspace" %(kploy["source"]))
            if not param:
                if VERBOSE: logging.info("Trying to list apps in the workspace ...")
                res = kploycommon._list_apps(kploy["source"], KAR_BASE_URL, VERBOSE)
                apps = res.json()
                app_list = []
                for app in apps:
                    app_list.append([
                        # to do: add time stamp column here; need to provide it in kploy.net
                        app["name"].split("/")[-1].split(".")[0], # to do: this is a hack and should really be done in kploy.net
                        app["size"]
                    ])
                print(tabulate(app_list, ["ID", "SIZE"], tablefmt="plain"))
            else:
                app_id = param
                if VERBOSE: logging.info("Trying to download app %s from the workspace ..." %(app_id))
                if not kploycommon._download_app(kploy["source"], app_id, archivefile, KAR_BASE_URL, VERBOSE):
                    raise NoSuchAppError
                else:
                    cmd_init(archivefile)
        else:
            raise InvalidWorkspaceError 
    except (InvalidWorkspaceError) as iwe:
        print(iwe.__doc__)
        print("To learn how to fix this, run `kploy explain push`")
        sys.exit(1)
    except (NoSuchAppError) as nsae:
        print(nsae.__doc__)
        print("To learn how to fix this, run `kploy explain pull`")
        sys.exit(1)
    except (Exception) as e:
        print("Something went wrong pulling from the registry:\n%s" %(e))
        sys.exit(1)
    finally:
        if os.path.exists(archivefile):
           os.remove(archivefile)
    if not param:
        print(80*"=")
        print("\nOK, I've successfully pulled from the registry.")
        print("\nYou can now `kploy pull $ID` to download and init an app.")
        print("\nWARNING: a `kploy pull $ID` will overwrite whatever you had locally.\n")

if __name__ == "__main__":
    try:
        cmds = {
            "dryrun" : cmd_dryrun,
            "run" : cmd_run,
            "list": cmd_list,
            "init": cmd_init,
            "destroy": cmd_destroy,
            "stats": cmd_stats,
            "export": cmd_export,
            "debug": cmd_debug,
            "scale": cmd_scale,
            "push" : cmd_push,
            "pull" : cmd_pull
        }
        
        parser = argparse.ArgumentParser(
            description="kploy is an opinionated Kubernetes deployment system for appops",
            epilog="Examples: `kploy init`, `kploy run`, `kploy list`, or to learn its usage: `kploy explain run`, `kploy explain list`, etc.")
        parser.add_argument("command", nargs="*", help="Currently supported commands are: %s and if you want to learn about a command, prepend `explain`, like: explain list " %(kploycommon._fmt_cmds(cmds)))
        parser.add_argument("-v", "--verbose", help="let me tell you every little dirty secret", action="store_true")
        args = parser.parse_args()
        if len(args.command) == 0:
            parser.print_help()
            sys.exit(0)
        if args.verbose:
            VERBOSE = True
        logging.debug("Got command %s" %(args))
        if args.command[0] == "explain":
            cmd = args.command[1]
            print(cmd + ":" + cmds[cmd].__doc__)
        else:
            cmd = args.command[0]
            param = None
            if len(args.command) == 2: # we have an additional parameter for the command
                param = args.command[1]
            logging.debug("Executing command %s with param %s" %(cmd, param))
            if cmd in cmds.keys():
                cmds[cmd](param)
    except (Exception) as e:
        print("Something went wrong:\n%s" %(e))
        sys.exit(1)