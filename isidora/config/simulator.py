# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Various settings for the crop/agro/weather simulator are defined at `config.simulator`.
"""
import os

from phenology import signals


# Relative directory config
currentdir = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(currentdir)

#####################################################################################
#                   CONFIGURATION FOR THE SIMULATOR
#####################################################################################

# Configuration file for the simulation Engine
simulator_config = os.path.join(top_dir, "phenology", "simulator.conf")

# pcse settings for model agromanagement
crop_end_type = "maturity"
crop_start_type = "sowing"

# Historic_years, no. of years to fetch historic weather
historic_years = 1
# Future_years, no. of years to fetch lta weather in the future
future_years = 1

# Limitation on generation of weather alerts for future weather
# Weather forecasts only have skill for a limited number of days in 
# the future. Therefore, weather alerts will not be generated beyond
# the days specified in the settings below. The number of days can be 
# set for all weather alerts ("DEFAULT") or specific for each alert.
weather_alert_limit = {"DEFAULT": 3,
                       signals.TMAX_STRESS: 3,
                       signals.RAIN_STRESS: 3,
                       signals.RHMAX_STRESS: 3,
                       signals.TMIN_STRESS: 3,
                       signals.FOG_STRESS: 3
                       }

