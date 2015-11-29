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

from pyk import toolkit
from pyk import util

DEBUG = False    # you can change that to enable debug messages ...
VERBOSE = False  # ... but leave this one in peace
DEPLOYMENT_DESCRIPTOR = "Kployfile"
RC_DIR = "rcs/"
SVC_DIR = "services/"


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
            print("Validating application `%s` ..." %(kploy["name"]))
            
            print("\n  CHECK: Is the Kubernetes cluster up & running and accessible via `%s`?" %(kploy["apiserver"]))
            try:
                pyk_client = toolkit.KubeHTTPClient(kube_version='1.1', api_server=kploy["apiserver"], debug=DEBUG)
                nodes = pyk_client.execute_operation(method='GET', ops_path='/api/v1/nodes')
                if VERBOSE: logging.info("Got node list %s " %(util.serialize_tojson(nodes.json())))
                print("  \o/ ... I found %d node(s) to deploy your wonderful app onto." %(len(nodes.json()["items"])))
            except:
                print("  :( ... I can't connect to the Kubernetes cluster, check the `apiserver` setting in your Kployfile")
                sys.exit(1)
            
            print("\n  CHECK: Are there RC and service manifests available around here?")
            try:
                rcs = os.path.join(here, RC_DIR)
                rc_manifests_confirmed = []
                logging.debug("Asserting %s exists" %(os.path.dirname(rcs)))
                assert os.path.exists(rcs)
                for _, _, rc_manifests in os.walk(rcs):
                    for rc_manifest in rc_manifests:
                        logging.debug("Detected RC %s" %(rc_manifest))
                        rc_manifests_confirmed.append(rc_manifest)
                print("         I found %s RC manifest(s) in %s" %(int(len(rc_manifests_confirmed)), os.path.dirname(rcs)))
                if VERBOSE:
                    for rcm in rc_manifests_confirmed:
                        logging.info("-> %s" %rcm)

                services = os.path.join(here, SVC_DIR)
                svc_manifests_confirmed = []
                logging.debug("Asserting %s exists" %(os.path.dirname(services)))
                assert os.path.exists(services)
                for _, _, services_manifests in os.walk(services):
                    for service_manifest in services_manifests:
                        logging.debug("Detected service %s" %(service_manifest))
                        svc_manifests_confirmed.append(service_manifest)
                print("         I found %s service manifest(s) in %s" %(int(len(svc_manifests_confirmed)), os.path.dirname(services)))
                if VERBOSE:
                    for svcm in svc_manifests_confirmed:
                        logging.info("-> %s" %svcm)

                print("  \o/ ... I found both RC and service manifests to deploy your wonderful app!")
            except:
                print("  :( ... No RC and/or service manifests found to deploy your app.")
                sys.exit(1)
    except (IOError, IndexError, KeyError) as e:
        print("Something went wrong:\n%s" %(e))
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
            pyk_client = toolkit.KubeHTTPClient(kube_version='1.1', api_server=kploy["apiserver"], debug=DEBUG)
            
            rc_manifests_confirmed = []
            svc_manifests_confirmed = []
            rcs = os.path.join(here, RC_DIR)
            for _, _, rc_manifests in os.walk(rcs):
                for rc_manifest in rc_manifests:
                    rc_manifests_confirmed.append(rc_manifest)
            services = os.path.join(here, SVC_DIR)
            for _, _, services_manifests in os.walk(services):
                for service_manifest in services_manifests:
                    svc_manifests_confirmed.append(service_manifest)
            
            for rcm in rc_manifests_confirmed:
                rc_filename = os.path.join(os.path.join(here, RC_DIR), rcm)
                if VERBOSE: logging.info("Deploying RC %s" %rc_filename)
                _, rc_url = pyk_client.create_rc(manifest_filename=rc_filename)
                rc = pyk_client.describe_resource(rc_url)
                logging.debug(rc.json())

            for svcm in svc_manifests_confirmed:
                svc_filename = os.path.join(os.path.join(here, SVC_DIR), svcm)
                if VERBOSE: logging.info("Deploying service %s" %svc_filename)
                _, svc_url = pyk_client.create_svc(manifest_filename=svc_filename)
                svc = pyk_client.describe_resource(svc_url)
                logging.debug(svc.json())
    except (Error) as e:
        print("Something went wrong:\n%s" %(e))
        print("Consider validating your deployment with with `kploy dryrun` first!")
        sys.exit(1)
    print(80*"=")
    print("\nOK, I've deployed `%s`\n" %(kploy["name"]))
    

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", help="The command to run, can be either `dryrun` or `run`")
        parser.add_argument("-v", "--verbose", help="Let me tell you every little dirty secrect", action="store_true")
        args = parser.parse_args()
        if args.verbose:
            VERBOSE = True
        cmds = {
            "dryrun" : cmd_dryrun,
            "run" : cmd_run
        }
        logging.debug("Got command `%s`" %(args.cmd))
        if args.cmd in cmds.keys():
            cmds[args.cmd]()
        else:
            print("Unknown command, sorry.")
    except:
        sys.exit(1)