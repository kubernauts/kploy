#!/usr/bin/env python

"""
The kploy main UX.

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2015-11-29
@status: init
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

if DEBUG:
  FORMAT = "%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]"
  logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="%Y-%m-%dT%I:%M:%S")
else:
  FORMAT = "%(asctime)-0s %(message)s"
  logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%dT%I:%M:%S")

logging.getLogger("requests").setLevel(logging.WARNING)

def cmd_dryrun():
    """
    Looks for a `Kployfile` file in the current directory and tries
    to validate its content, incl. syntax validation and mock execution.
    """
    here = os.path.dirname(os.path.realpath(__file__))
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

def cmd_run():
    """
    Looks for a `Kployfile` file in the current directory and tries to run it.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Trying to run %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        # set up a namespace for this app:
        kploycommon._create_ns(pyk_client, kploy["namespace"], VERBOSE)

        # set up a secrets for this app:
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
    except (Error) as e:
        print("Something went wrong deploying your app:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)
    print(80*"=")
    print("\nOK, I've deployed `%s/%s`.\nUse `kploy list` and `kploy stats` to check how it's doing." %(kploy["namespace"], kploy["name"]))

def cmd_list():
    """
    Lists apps and their status.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Listing resource status of app based on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        print("Resources of app `%s/%s`:" %(kploy["namespace"], kploy["name"]))
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_list = kploycommon._visit(services, 'service', cache_remotes=True)
        rc_list = kploycommon._visit(rcs, 'RC', cache_remotes=True)
        res_list = []
        for svc in svc_list:
            svc_manifest, _  = util.load_yaml(filename=os.path.join(here, SVC_DIR, svc))
            svc_name = svc_manifest["metadata"]["name"]
            svc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/services/", svc_name])
            svc_URL = "".join([kploy["apiserver"], svc_path])
            svc_status = kploycommon._check_status(pyk_client, svc_path)
            res_list.append([svc_name, os.path.join(SVC_DIR, svc), "service", svc_status, svc_URL])
        for rc in rc_list:
            rc_manifest, _  = util.load_yaml(filename=os.path.join(here, RC_DIR, rc))
            rc_name = rc_manifest["metadata"]["name"]
            rc_path = "".join(["/api/v1/namespaces/", kploy["namespace"], "/replicationcontrollers/", rc_name])
            rc_URL = "".join([kploy["apiserver"], rc_path])
            rc_status = kploycommon._check_status(pyk_client, rc_path)
            res_list.append([rc_name, os.path.join(RC_DIR, rc), "RC", rc_status, rc_URL])
        print tabulate(res_list, ["NAME", "MANIFEST", "TYPE", "STATUS", "URL"], tablefmt="plain")
    except (Error) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

def cmd_init():
    """
    Creates a dummy `Kployfile` file in the current directory sets up the directories.
    """    
    here = os.path.dirname(os.path.realpath(__file__))
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    archivefile = os.path.join(here, EXPORT_ARCHIVE_FILENAME)
    if os.path.exists(kployfile):
        print("Hey! %s already exists.\nI'm not going to destroy existing work. #kthxbye" %(kployfile))
        sys.exit(1)
    if not os.path.exists(SVC_DIR):
        os.makedirs(SVC_DIR)
    if not os.path.exists(RC_DIR):
        os.makedirs(RC_DIR)
    if os.path.exists(archivefile): # set up via archive
        if VERBOSE: logging.info("Detected archive %s" %(archivefile))
        kploycommon._init_from_archive(archivefile)
        print(80*"=")
        print("\nOK, I've set up the deployment from archive.\nYou can now validate it with `kploy dryrun`\n")
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
        print("\nOK, I've set up the %s deployment file and created necessary directories.\nNow edit the deployment file and copy manifests into the respective directories.\n" %(DEPLOYMENT_DESCRIPTOR))

def cmd_destroy():
    """
    Destroys the app, removing all resources.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Trying to destroy app based on %s " %(kployfile))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        logging.debug(kploy)
        pyk_client = kploycommon._connect(api_server=kploy["apiserver"], debug=DEBUG)
        rc_manifests_confirmed, svc_manifests_confirmed = [], []
        services = os.path.join(here, SVC_DIR)
        rcs = os.path.join(here, RC_DIR)
        svc_manifests_confirmed = kploycommon._visit(services, 'service', cache_remotes=True)
        rc_manifests_confirmed = kploycommon._visit(rcs, 'RC', cache_remotes=True)
        kploycommon._destroy(pyk_client, kploy["namespace"], here, SVC_DIR, svc_manifests_confirmed, 'service', VERBOSE)
        kploycommon._destroy(pyk_client, kploy["namespace"], here, RC_DIR, rc_manifests_confirmed, 'RC', VERBOSE)
    except (Error) as e:
        print("Something went wrong destroying your app:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)
    print(80*"=")
    print("\nOK, I've destroyed `%s/%s`\n" %(kploy["namespace"], kploy["name"]))

def cmd_stats():
    """
    Shows cluster utilization and provides summary of the pods' state, from the point of view of your app.
    """
    here = os.path.dirname(os.path.realpath(__file__))
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
        print tabulate(pod_details, ["NAME", "HOST", "STATUS", "URL"], tablefmt="plain")
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
        print tabulate(node_ips, ["IP", "HOST OS", "CONTAINER RUNTIME", "CAPACITY (PODS, CPU, MEM)", "URL"], tablefmt="plain")
        print("\n" + 80*"=")
    except (Error) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

def cmd_export():
    """
    Creates an archive of all relevant app files, incl. Kployfile and manifest directories.
    You can use the resulting archive then with `kploy init` to bootstrap you app in a different location.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    kployfile = os.path.join(here, DEPLOYMENT_DESCRIPTOR)
    if VERBOSE: logging.info("Exporting app based on content from %s " %(here))
    try:
        kploy, _  = util.load_yaml(filename=kployfile)
        archive_filename, archive_file = kploycommon._export_init(here, DEPLOYMENT_DESCRIPTOR, EXPORT_ARCHIVE_FILENAME)
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
    except (Error) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with `kploy dryrun` first!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        cmds = {
            "dryrun" : cmd_dryrun,
            "run" : cmd_run,
            "list": cmd_list,
            "init": cmd_init,
            "destroy": cmd_destroy,
            "stats": cmd_stats,
            "export": cmd_export
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
        logging.debug("Got command `%s`" %(args))
        if args.command[0] == "explain":
            cmd = args.command[1]
            print(cmd + ":" + cmds[cmd].__doc__)
        else:
            cmd = args.command[0]
            if cmd in cmds.keys():
                cmds[cmd]()
    except:
        sys.exit(1)