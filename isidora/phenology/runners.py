# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Defines runners that can run the actual crop simulation. Currently two runners are implemented:

- `notebook_runner` which can be imported in Jupyter notebook and is useful for interactive exploratory
  analysis. It returns tje JSON results structure as well as a pandas dataframe with simulation results.
- `web_runner` which is used to run behind a webserver and returns the JSON structure as understood by
  web browsers.
"""
import json

import sqlalchemy as sa
import pandas as pd

import config
from . import data_providers as dp
from pcse.engine import Engine
from pcse.base_classes import ParameterProvider


def notebook_runner(latitude=None, longitude=None, sowing_date=None, crop_no=None, variety_no=-1, season_no=-1):
    """Make a run for given longitude, latitude, sowing date, crop_no and variety_no.

    :param latitude: latitude of the site
    :param longitude: longitude of the site
    :param sowing_date: the sowing date for the crop simulation
    :param crop_no: the crop number (cropid) as defined in the database
    :param variety_no: the variety number (varid) as defined in the database
    :param season_no: the season number (seasonid) as defined in the database for distinguishing between
        different cropping seasons.
    :return: The JSON data structure and the output from the PCSE Engine as a pandas dataframe
    """

    # create a db connection
    DBengine = sa.create_engine(config.database.dbc)

    # Pull in data from the database
    wdp = dp.CombinedECMWFDarkSkyWeatherDataProvider(latitude, longitude)
    crop = dp.CropDataProvider(DBengine, crop_no, variety_no)

    management_alerts, mremark = dp.fetch_management_alerts(DBengine, crop_no, variety_no, season_no)
    crop["MANAGEMENT_ALERTS"] = management_alerts

    weather_alerts, wremark = dp.fetch_weather_alerts(DBengine, crop_no, variety_no, season_no)
    crop["WEATHER_ALERTS"] = weather_alerts

    # generate timer parameters based on sowing_date
    timerdata = dp.make_timerdata(sowing_date, crop, crop_start_type=config.simulator.crop_start_type,
                                  crop_end_type=config.simulator.crop_end_type)
    pprovider = ParameterProvider(cropdata=crop, soildata={}, sitedata={}, timerdata=timerdata)

    # Run the simulation for phenology
    engine = Engine(pprovider, wdp, config=config.simulator.simulator_config)
    engine.run_till_terminate()
    df = pd.DataFrame(engine.get_output())
    df.index = pd.to_datetime(df.day)

    # get results from model run
    palerts = engine.get_variable("BBCH_DATES")
    walerts = engine.get_variable("WEATHER_MESSAGES")
    malerts = engine.get_variable("MANAGEMENT_MESSAGES")

    # get phenology + management + weather alert messages and add them to json
    palerts = ',\n'.join(palerts)
    palerts = '"phenology":[\n%s\n]' % palerts

    malerts = ',\n'.join(malerts)
    malerts = '\n"managementalerts":[\n%s\n]' % malerts

    walerts = ',\n'.join(walerts)
    walerts = '\n"weatheralerts":[\n%s\n]' % walerts

    # add messages together
    alerts = [palerts, walerts, malerts]
    alerts = filter(None, alerts)
    alerts = '{' + ','.join(alerts) + '}'

    # Replace quotes and let YAML parse it
    alerts = json.loads(alerts)

    return alerts, df


def GPRE_service_runner(wdp, sowing_date, crop_no=None, variety_no=-1, season_no=-1):
    """Make a run for given longitude, latitude, sowing date, crop_no and variety_no.

    :param wdp: The weather data provider to be used
    :param sowing_date: date object providing sowing date of the crop
    :param crop_no: The crop number
    :param variety_no: The variety number (defaults to -1, generic variety)
    :param season_no: The season number (defaults to -1: generic season)
    :return: The JSON data structure on phenology, management and weather alerts

    Note that this function does not pull the weather data but expects a weather dataprovider
    as an input parameter. This allows for some optimization avoiding expensive cal
    to databases and internet resources.
    """

    # create a db connection
    DBengine = sa.create_engine(config.database.dbc)

    crop = dp.CropDataProvider(DBengine, crop_no, variety_no)

    management_alerts, mremark = dp.fetch_management_alerts(DBengine, crop_no, variety_no, season_no)
    crop["MANAGEMENT_ALERTS"] = management_alerts

    weather_alerts, wremark = dp.fetch_weather_alerts(DBengine, crop_no, variety_no, season_no)
    crop["WEATHER_ALERTS"] = weather_alerts

    # generate timer parameters based on sowing_date
    timerdata = dp.make_timerdata(sowing_date, crop, crop_start_type=config.simulator.crop_start_type,
                                  crop_end_type=config.simulator.crop_end_type)
    pprovider = ParameterProvider(cropdata=crop, soildata={}, sitedata={}, timerdata=timerdata)

    # Run the simulation for phenology
    engine = Engine(pprovider, wdp, config=config.simulator.simulator_config)
    engine.run_till_terminate()

    # get results from model run
    palerts = engine.get_variable("BBCH_DATES")
    walerts = engine.get_variable("WEATHER_MESSAGES")
    malerts = engine.get_variable("MANAGEMENT_MESSAGES")

    # get phenology + management + weather alert messages and add them to json
    palerts = ',\n'.join(palerts)
    palerts = '"phenology":[\n%s\n]' % palerts

    malerts = ',\n'.join(malerts)
    malerts = '\n"managementalerts":[\n%s\n]' % malerts

    walerts = ',\n'.join(walerts)
    walerts = '\n"weatheralerts":[\n%s\n]' % walerts

    # add messages together
    alerts = [palerts, walerts, malerts]
    alerts = filter(None, alerts)
    alerts = '{' + ','.join(alerts) + '}'

    # parse the JSON
    alerts = json.loads(alerts)

    return alerts
