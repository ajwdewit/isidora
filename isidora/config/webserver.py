# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Web server related settings are defined here.
"""
import os, sys

# ------------------------------------------------------------------------------------------------
#                       Settings for downloadable excel files.
#
# In case of development we assume that the URL should point to localhost at port 5000.
# In production, we assume the IP address of the GPRE production server.
# ------------------------------------------------------------------------------------------------

if os.environ.get("DEVELOP"):
    ip_address = "127.0.0.1"
    port = 5000
else:
    ip_address = "104.198.254.142"
    port = 80

download_base_url = "http://%s:%s/api/v1/download/" % (ip_address, port)