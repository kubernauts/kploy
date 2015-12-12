"""
The kploy commons (utility) functions

@author: Michael Hausenblas, http://mhausenblas.info/#i
@since: 2015-12-12
@status: init
"""

import os
import logging

from pyk import toolkit
from pyk import util

def _visit(dir_name, resource_name):
    """
    Walks a given directory and return list of files in there.
    """
    flist = []
    logging.debug("Visiting %s" %dir_name)
    for _, _, file_names in os.walk(dir_name):
        for afile in file_names:
            logging.debug("Detected %s %s" %(resource_name, afile))
            flist.append(afile)
    return flist

def _dump(alist):
    """
    Dumps a list to the INFO logger.
    """
    for litem in alist:
        logging.info("-> %s" %litem)

def _deploy(pyk_client, here, dir_name, alist, resource_name, verbose):
    """
    Deploys a resource based on a manifest. Currently the following resources are supported:
    replication controllers, services.
    """
    for litem in alist:
        file_name = os.path.join(os.path.join(here, dir_name), litem)
        if verbose: logging.info("Deploying %s %s" %(resource_name, file_name))
        if resource_name == "service":
            _, res_url = pyk_client.create_svc(manifest_filename=file_name)
        elif resource_name == "RC":
            _, res_url = pyk_client.create_rc(manifest_filename=file_name)
        else: return None
        res = pyk_client.describe_resource(res_url)
        logging.debug(res.json())