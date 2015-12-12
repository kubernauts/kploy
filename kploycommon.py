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
    flist = []
    logging.debug("Visiting %s" %dir_name)
    for _, _, file_names in os.walk(dir_name):
        for afile in file_names:
            logging.debug("Detected %s %s" %(resource_name, afile))
            flist.append(afile)
    return flist

def _dump(alist):
    for litem in alist:
        logging.info("-> %s" %litem)