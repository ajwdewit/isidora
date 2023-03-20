# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), June 2020
"""Data providers for crop simulation related data such as weather, crop and agromanagement.
"""
import datetime as dt
import json
from decimal import Decimal
import logging

from dotmap import DotMap
import pymysql
import pandas as pd
from pandas.core.frame import DataFrame
from sqlalchemy import MetaData, select, Table, and_
import requests

import config
from pcse import exceptions as exc
from pcse.base_classes import WeatherDataProvider, WeatherDataContainer
from pcse.util import check_date, ea_from_tdew, wind10to2


def fetch_crop_name(engine, crop_no, _cache={}):
    """Retrieves the name of the crop from the CROP table for
    given crop_no.

    :param engine: SqlAlchemy engine object providing DB access
    :param crop_no: integer cropid
    """
    if crop_no not in _cache:
        metadata = MetaData(engine)
        table_crop = Table("crop", metadata, autoload=True)
        r = select([table_crop],
                   table_crop.c.crop_no == crop_no).execute()
        row = r.fetchone()
        r.close()
        if row is None:
            msg = "Failed deriving crop name for cropid %s" % crop_no
            raise exc.PCSEError(msg)
        _cache[crop_no] = row.crop_name
    return _cache[crop_no]


def fetch_variety_name(engine, crop_no, variety_no, _cache={}):
    """Retrieves the name of the crop from the VARIETIES table for
    given crop_no, variety_no.

    :param engine: SqlAlchemy engine object providing DB access
    :param crop_no: integer cropid
    :param variety_no: integer varietyid
    """
    if (crop_no, variety_no) not in _cache:
        metadata = MetaData(engine)
        table_varieties = Table("varieties", metadata, autoload=True)
        r = select([table_varieties], and_(table_varieties.c.crop_no == crop_no,
                                           table_varieties.c.variety_no == variety_no)
                   ).execute()
        row = r.fetchone()
        r.close()
        if row is None:
            msg = "Failed deriving variety name for crop_no, variety_no %s, %s" % (crop_no, variety_no)
            raise exc.PCSEError(msg)
        _cache[(crop_no, variety_no)] = row.variety_name
    return _cache[(crop_no, variety_no)]


def fetch_season_name(engine, season_no, _cache={}):
    """Retrieves the name of the cropping seasons from the SEASON table for
    given season_no.

    :param engine: SqlAlchemy engine object providing DB access
    :param season_no: integer season id
    """
    if season_no not in _cache:
        metadata = MetaData(engine)
        table_season = Table("season", metadata, autoload=True)
        r = select([table_season],
                   table_season.c.season_no == season_no).execute()
        row = r.fetchone()
        r.close()
        if row is None:
            msg = "Failed deriving season name for season_no %s" % season_no
            raise exc.PCSEError(msg)
        _cache[season_no] = row.season_name
    return _cache[season_no]


def fetch_management_alerts(engine, crop_no, variety_no, season_no):
    """Retrieves the management_alerts from the database
    
    :param engine: SqlAlchemy engine object providing DB access
    :param crop_no: integer cropid (from url query string)
    :param variety_no: integer varid (from url query string)
    :param season_no: integer seasonid (from url query string)
    """
    metadata = MetaData(engine)
    remark = ""
    tbl = Table("management_alerts", metadata, autoload=True)
    r = select([tbl], and_(tbl.c.crop_no==crop_no,
                           tbl.c.variety_no==variety_no,
                           tbl.c.season_no==season_no)).execute()
    rows = r.fetchall()
    r.close()
    
    if not rows:
        # no management alerts for varid? get cropid alerts only
        remark = 'No managementalerts available for varid {0} and seasonid {2}'.format(variety_no, crop_no, season_no)
        rs = select([tbl], and_(tbl.c.crop_no==crop_no,
                           tbl.c.variety_no==-1,
                           tbl.c.season_no==-1)).execute()
        rows = rs.fetchall()
        rs.close()
    
    return rows, remark


def fetch_weather_alerts(engine, crop_no, variety_no, season_no):
    """Retrieves the weather_alerts from the database
    
    :param engine: SqlAlchemy engine object providing DB access
    :param crop_no: integer cropid (from url query string)
    :param variety_no: integer varid (from url query string)
    :param season_no: integer seasonid (from url query string)
    """
    metadata = MetaData(engine)
    remark= ""
    tbl = Table("weather_alerts", metadata, autoload=True)
    r = select([tbl], and_(tbl.c.crop_no==crop_no,
                           tbl.c.variety_no==variety_no,
                           tbl.c.season_no==season_no)).execute()
    rows = r.fetchall()
    r.close()
    
    if not rows:
        # no weatheralerts for varid? get cropid alerts only
        remark = 'No weatheralerts available for varid {0} and seasonid {2}'.format(variety_no, crop_no, season_no)
        rs = select([tbl], and_(tbl.c.crop_no==crop_no,
                           tbl.c.variety_no==-1,
                           tbl.c.season_no==-1)).execute()
        rows = rs.fetchall()
        rs.close()
    
    return rows,remark


class CropDataProvider(dict):
    """Retrieves the crop parameters for the given grid_no, crop_no and year
    from the tables CROP_CALENDAR, CROP_PARAMETER_VALUE and VARIETY_PARAMETER_VALUE.

    :param engine: SqlAlchemy engine object providing DB access
    :param crop_no: integer cropid, maps to the CROP_NO column in the table.
    :param variety_no: integer varietyid, maps to the VARIETY_NO column in the table.
    """

    def __init__(self, engine, crop_no, variety_no):
        dict.__init__(self)

        self.crop_no = int(crop_no)
        self.variety_no = int(variety_no)
        self.crop_name = fetch_crop_name(engine, self.crop_no)
        self.db_resource = str(engine)[7:-1]

        metadata = MetaData(engine)

        # get parameters from db
        self._fetch_crop_parameter_values(metadata, self.crop_no)
        # variety not mandatory
        self._fetch_variety_parameter_values(metadata, self.crop_no, self.variety_no)

        # Finally add crop name
        self["crop_name"] = self.crop_name
        
    def _fetch_crop_parameter_values(self, metadata, crop_no):
        """Derived the crop parameter values from the CROP_PARAMETER_VALUE
        table for given crop_no and add directly to dict self[].
        
        :param metadata: metadata containing db engine definition.
        :param crop_no: integer cropid, maps to the CROP_NO column in the table.
        """

        # Pull single value parameters from CROP_PARAMETER_VALUE
        table_crop_pv = Table('crop_parameter_value', metadata, autoload=True)
        r = select([table_crop_pv], table_crop_pv.c.crop_no == crop_no,order_by=table_crop_pv.c.parameter_code).execute()
        rows = r.fetchall()
        if not rows:
            msg = "No parameter value found for cropid=%s."
            raise exc.PCSEError(msg % self.crop_no)
        for row in rows:
            try:
                pvalue = eval(row.parameter_value)
            except SyntaxError:
                msg = "Failed parsing parameter: %s from table CROP_PARAMETER_VALUE" % row.parameter_value
                raise exc.PCSEError(msg)
            pcode = row.parameter_code
            self[pcode] = pvalue

    def _fetch_variety_parameter_values(self, metadata, crop_no, variety_no):
        """Derived the crop parameter values from the VARIETY_PARAMETER_VALUE
        table for given crop_no & variety_on and add directly to dict self[].
         
        :param metadata: metadata containing db engine definition.
        :param crop_no: integer cropid, maps to the CROP_NO column in the table.
        :param variety_no: integer varietyid, maps to the VARIETY_NO column in the table.
        """

        # Pull single value parameters from CROP_PARAMETER_VALUE
        table_crop_vpv = Table('variety_parameter_value', metadata, autoload=True)
        r = select([table_crop_vpv], and_(table_crop_vpv.c.crop_no == crop_no,
                                         table_crop_vpv.c.variety_no == variety_no),
                    order_by=table_crop_vpv.c.parameter_code).execute()
        rows = r.fetchall()
        for row in rows:
            try:
                pvalue = eval(row.parameter_value)
            except SyntaxError:
                msg = "Failed parsing parameter: %s for table VARIETY_PARAMETER_VALUE" % row.parameter_value
                raise exc.PCSEError(msg)
            pcode = row.parameter_code
            self[pcode] = pvalue


def make_timerdata(date, cropd, crop_start_type=None, crop_end_type=None):
    """generate timer data for the model pcse simulation

    :param date: starting date of the crop growth simulation
    :param cropd: crop data dict with the maximum duration of crop growth simulation
    :param crop_start_type: Start type of the simulation, either 'sowing' or 'emergence'
    :param crop_end_type: End type of the simulation, either 'maturity' or 'harvest'
    """
    max_dur = int(cropd.pop("MAX_DURATION"))
    gp = dt.timedelta(days=max_dur)

    r = {"CAMPAIGNYEAR": date.year,
         "START_DATE": date,
         "END_DATE": date + gp,
         "CROP_START_TYPE": crop_start_type,
         "CROP_START_DATE": date,
         "CROP_END_TYPE": crop_end_type,
         "CROP_END_DATE": date + gp,
         "MAX_DURATION": max_dur}

    return r


class GridWeatherDataProvider(WeatherDataProvider):
    """Retrieves meteodata from the GRID_WEATHER table in a CGMS (like) database.

    :param lat: Latitude of location to retrieve weather data
    :param lon: Longitude of location to retrieve weather data

    Note that all meteodata is first retrieved from the DB and stored
    internally. Therefore, no DB connections are stored within the class
    instance. This makes that class instances can be pickled.
    """

    def __init__(self, lat, lon):

        WeatherDataProvider.__init__(self)

        self.latitude = lat
        self.longitude = lon
        self.elevation = 25

        # set DB connect, we use pymysql here for calling stored procedures
        self.connection = pymysql.connect(host=config.database.myhost, user=config.database.myuser,
                                          password=config.database.mypwd, db=config.database.mydb,
                                          port=config.database.port,
                                          cursorclass=pymysql.cursors.DictCursor, autocommit=True)

        # Get location info (lat/lon/elevation)
        self._fetch_location_from_db()

        # Retrieved meteo data
        self._fetch_grid_weather_from_db()

        # Add description for print()
        self.description = ["Weather data derived for area %s" % config.area_name]

        self.connection.close()

    def _fetch_location_from_db(self):
        """Retrieves grid_no from 'grid' table via  a stored procedure and
        assigns it to self.grid_no"""
        # Pull grid nr from database

        try:
            cur = self.connection.cursor()
            cur.execute("call get_grid(%s,%s,%s)" % (self.latitude, self.longitude, config.cell_size));
            row = cur.fetchall()
            cur.close()
            if row is ():
                raise Exception("no rows found")
        except Exception as e:
            msg = "Failed deriving grid info for lat %s, lon %s :%s" % (self.latitude, self.longitude, e)
            raise exc.PCSEError(msg)

        self.grid_no = row[0]['grid_no']

    def _fetch_grid_weather_from_db(self):
        """Retrieves the meteo data from stored procedure 'grid_weather'.
        """

        try:
            cur = self.connection.cursor()
            cur.execute("call get_grid_weather(%s,%s,%s)" % (self.grid_no, config.simulator.historic_years,
                                                             config.simulator.future_years));
            rows = DataFrame(cur.fetchall())
            cur.close()

            meteopackager = self._make_WeatherDataContainer
            for row in rows.itertuples():
                if row.day is None:
                    continue
                DAY = self.check_keydate(row.day)
                t = {"DAY": DAY, "LAT": self.latitude,
                     "LON": self.longitude, "ELEV": self.elevation}
                wdc = meteopackager(row, t)
                self._store_WeatherDataContainer(wdc, DAY)
        except Exception as e:
            errstr = "Failure reading meteodata: " + str(e)
            raise exc.PCSEError(errstr)

    def _make_WeatherDataContainer(self, row, t):
        """Process record from grid_weather including unit conversion."""

        t.update({"TMAX": float(row.maximum_temperature),
                  "TMIN": float(row.minimum_temperature),
                  "VAP": float(row.vapour_pressure),
                  "WIND": float(row.windspeed),
                  "RAIN": float(row.rainfall),
                  "E0": float(row.e0),
                  "ES0": float(row.es0),
                  "ET0": float(row.et0),
                  "IRRAD": float(row.calculated_radiation)})
        wdc = WeatherDataContainer(**t)

        return wdc


class CombinedECMWFDarkSkyWeatherDataProvider(WeatherDataProvider):
    """Retrieves meteodata from the GRID_WEATHER_OBSERVED table in the database
    and combines it with a weather forecast from DarkSky plus a climatology
    for the remaining part of the year.

    :param latitude: Latitude of location to retrieve weather data
    :param longitude: Longitude of location to retrieve weather data
    """
    relevant_darksky_variables = ("precipIntensity", "dewPoint", "humidity", "pressure", "windSpeed",
                                  "cloudCover", "visibility", "temperatureMin", "temperatureMax")
    weather_data = None

    def __init__(self, latitude, longitude):

        WeatherDataProvider.__init__(self)

        self.latitude =float(latitude)
        self.longitude = float(longitude)
        self.elevation = -999

        # set DB connect, we use pymysql here for calling stored procedures
        c = config.database.default_user
        self.connection = pymysql.connect(host=c.host, user=c.user, password=c.pwd, db=c.db,
                                          port=c.port, cursorclass=pymysql.cursors.DictCursor,
                                          autocommit=True)

        # Get location info (lat/lon/elevation)
        self._fetch_location_from_db()

        # Retrieved meteo data
        self._fetch_grid_weather_from_db()
        self._integrate_DarkSky_forecast()
        self._compute_derived_variables()

        # Add description for print()
        self.description = ["Weather data derived for area %s" % config.area_name]

        self.connection.close()

    def _fetch_location_from_db(self):
        """Retrieves grid_no from 'grid' table via  a stored procedure and
        assigns it to self.grid_no"""
        # Pull grid nr from database

        cur = self.connection.cursor()
        try:
            cur.execute("call get_grid(%s,%s,%s)" % (self.latitude, self.longitude, config.cell_size))
            row = cur.fetchall()
            if row is ():
                raise Exception("no rows found")
            self.grid_no = row[0]['grid_no']
            cur.execute("select elevation from grid where grid_no=%i" % self.grid_no)
            row = cur.fetchone()
            self.elevation = row["elevation"]
        except Exception as e:
            msg = "Failed deriving grid info for lat %s, lon %s :%s" % (self.latitude, self.longitude, e)
            raise exc.PCSEError(msg)
        finally:
            cur.close()

    def _fetch_grid_weather_from_db(self):
        """Retrieves the meteo data from stored procedure 'grid_weather'.
        """
        try:
            cur = self.connection.cursor()
            cur.execute("call get_grid_weather(%s,%s,%s)" % (self.grid_no, config.simulator.historic_years,
                                                             config.simulator.future_years))
            rows = cur.fetchall()
            grid_weather_data = pd.DataFrame(rows)
            self.weather_data = pd.DataFrame({"DAY": pd.to_datetime(grid_weather_data.day),
                                              "TMAX": grid_weather_data.maximum_temperature.astype(float),
                                              "TMIN": grid_weather_data.minimum_temperature.astype(float),
                                              "VAP": grid_weather_data.vapour_pressure.astype(float),
                                              "WIND": (grid_weather_data.windspeed.astype(float)).apply(wind10to2),  # reference height 10 -> 2
                                              "RAIN": grid_weather_data.rainfall.astype(float)/10.,  # mm to cm
                                              "IRRAD": grid_weather_data.calculated_radiation.astype(float) * 1000.,  # kJ to J
                                              "ET0": grid_weather_data.et0.astype(float)/10.,  # mm to cm
                                              "ES0": grid_weather_data.et0.astype(float)/10.,  # mm to cm
                                              "E0": grid_weather_data.et0.astype(float)/10.  # mm to cm
                                              }).set_index("DAY")

        except Exception as e:
            msg = "Failed to retrieve grid weather data for grid %i" % self.grid_no
            logging.exception(msg)
            raise exc.PCSEError(msg)
        finally:
            cur.close()

    def _integrate_DarkSky_forecast(self):
        """Integrates the DarkSky forecast into the grid weather data from the database by overwriting
        the relevant days/variables with data from DarkSky.
        """
        forecast = self._call_darksky_forecast_api()
        pcse_forecast = pd.DataFrame({"DAY": pd.to_datetime(forecast.day),
                                      "TMAX": forecast.temperatureMax.astype(float),
                                      "TMIN": forecast.temperatureMin.astype(float),
                                      "VAP": (forecast.dewPoint.apply(ea_from_tdew)).astype(float) * 10., # kPa to hPa
                                      "WIND": forecast.windSpeed.astype(float),
                                      "RAIN": forecast.precipIntensity.astype(float) * 24/10.  # Convert from mm/hr to cm/day
                                      }).set_index("DAY")
        self.weather_data.update(pcse_forecast, overwrite=True)

        # Add latitude/longitude columns
        self.weather_data["LAT"] = self.latitude
        self.weather_data["LON"] = self.longitude

    def _compute_derived_variables(self):
        """Computes the TEMP and DTEMP values for the entire data frame with weather data.
        """
        self.weather_data["TEMP"] = (self.weather_data.TMAX + self.weather_data.TMIN)/2.0
        self.weather_data["DTEMP"] = (self.weather_data.TMAX + self.weather_data.TEMP)/2.0

    def _call_darksky_forecast_api(self):
        """queries the darksky forecast data for given location

        No caching is performed as the forecast has to be retrieved every day again anyway.

        :param location: the object specifying the location of the site
        :return: a list with dicts containing weather data
        """
        f_URL = config.weather.DARKSKY_forecast_api.format(latitude=self.latitude,
                                                           longitude=self.longitude)
        r = requests.get(f_URL)
        if r.status_code != 200:
            msg = "Failed to retrieve weather forecast data from DarkSky for lat/lon %s/%s"
            raise RuntimeError(msg % (self.latitude, self.longitude))
        daily_weather = self._parse_darksky_forecast_response(r.text)
        return pd.DataFrame(daily_weather)

    def _parse_darksky_forecast_response(self, json_response):
        """Parses the DarkSky forecast response.
        """
        r = json.loads(json_response)
        daily_weather = []
        issue_day = None
        try:
            for i, daily_data in enumerate(r["daily"]["data"]):
                utc_time = dt.datetime.utcfromtimestamp(daily_data["time"])
                if issue_day is None:
                    issue_day = (utc_time + dt.timedelta(seconds=config.weather.SECONDS_from_UTC)).date()
                t = {"day": issue_day + dt.timedelta(days=i), "latitude": self.latitude,
                     "longitude": self.longitude}
                for variable, value in daily_data.items():
                    if variable in self.relevant_darksky_variables:
                        t[variable] = float(value)
                daily_weather.append(t)
        except KeyError:
            msg = "No DarkSky forecast available"
            raise RuntimeError(msg)

        return daily_weather

    def __call__(self, day):
        d = check_date(day)
        ix = self.weather_data.index == str(d)
        if any(ix):
            for row in self.weather_data[ix].itertuples(index=False):
                return row
        else:
            raise KeyError("cannot find day '%s'" % d)

    @property
    def first_date(self):
        return self.weather_data.index.min()

    @property
    def last_date(self):
        return self.weather_data.index.max()

    @property
    def missing(self):
        return 0