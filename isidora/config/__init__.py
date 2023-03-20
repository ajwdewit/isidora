# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Top level configuration that defines some of the global settings such as:

  - logging behaviour
  - Bounding box of the area of interest
  - Name of the area of interest.
  - Whether the system should be ran in debug_mode or not
"""
import os, sys
import time
import logging.config

from . import weather
from . import database
from . import webserver
from . import simulator



def get_logging_config(log_fname):
    """Log configuration for data processing
    """
    log_file_name = log_fname
    log_level_file = "INFO"
    log_level_console = "INFO"
    log_config = \
            {
                'version': 1,
                'disable_existing_loggers': True,
                'formatters': {
                    'standard': {
                        'format': '%(asctime)s [%(levelname)s] -- %(name)s --: %(message)s'
                    },
                    'brief': {
                        'format': '[%(levelname)s] - %(message)s'
                    },
                },
                'handlers': {
                    'console': {
                        'level':log_level_console,
                        'class':'logging.StreamHandler',
                        'formatter':'brief'
                    },
                    'file': {
                        'level':log_level_file,
                        'class':'logging.handlers.RotatingFileHandler',
                        'formatter':'standard',
                        'filename':log_file_name,
                        'mode':'a',
                        'encoding': 'utf8',
                        'maxBytes': 1024**2,
                        'backupCount': 7
                    },
                },
                'root': {
                         'handlers': ['console', 'file'],
                         'propagate': True,
                         'level':'NOTSET'
                }
            }
    return log_config


# Relative directory config
currentdir = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(currentdir)


#####################################################################################
#                   SPATIAL DEFINITION OF AREA OF INTEREST
#####################################################################################

# Make subset for select only GFS for given bounding box
lat_bnds, lon_bnds = [8.5, 29.0], [92.0, 101.5]

# Resolution of downscaled product [decimal degrees]
cell_size = 0.1

# Identifier for the area of interest
area_name = "Myanmar"


#####################################################################################
#                            LOGGING CONFIGURATION
#####################################################################################
log_fname = os.path.join(top_dir, "logs", "{area}_processing_%Y%m%d.log".format(area=area_name))
log_fname = time.strftime(log_fname)
log_config = get_logging_config(log_fname)
logging.config.dictConfig(log_config)
