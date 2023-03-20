# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Database credentials are defined at `config.database`.
"""
import socket
import os
from dotmap import DotMap


####################################################################################
#                            DATABASE CREDENTIALS
####################################################################################

if os.environ.get("DEVELOP"):
    print("using DEVELOP DB settings!")
    default_user = DotMap(
                        host="127.0.0.1",
                        user="isidora",
                        pwd="XXXXXXXXXX",
                        db="isidora",
                        port=3310)
else:
    default_user = DotMap(
                        host="35.192.200.139",
                        user="isidora",
                        pwd="XXXXXXXXXX",
                        db="isidora",
                        port=3306)



# Create db connection string (sqlalchemy)
def create_dbc(u):
    dbc_template = 'mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}'
    dbc = dbc_template.format(user=u.user, passwd=u.pwd, host=u.host, db=u.db, port=u.port)
    return dbc


dbc = create_dbc(default_user)

