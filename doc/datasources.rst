Data sources
============

Weather
-------

DarkSky API
...........

GPRE uses the API provided by DarkSky to retrieve the weather forecast for the upcoming 7 days consisting of daily weather variables. Most of the variables provided by the DarkSky API are not relevant for agronomic applications (moonphase, windbearing, etc) therefore only a small subset of the variables is used:

- dewpointTemperature in degrees C;
- temperatureHigh in degrees C;
- temperatureLow in degrees C;
- windSpeed in m/sec;
- precipIntensity in mm/hour;

Examples of the API call can be found in the table below. Extensive information is available from the documentation for the `DarkSky API`_

Next to a forecast API, DarkSky also provides a TimeMachine API which can be used to retrieve the weather variables for a day in the past. During development of GPRE several problems were encountered with the TimeMachine API:

- Each TimeMachine call only provides the data for one day. This makes querying a time-series relatively expensive and slow.
- For Myanmar the TimeMachine API provides weather data only for one year in the past which is insufficient for model calibration and computation of the climatology.

Therefore GPRE does not rely on DarkSky for historical data but instead uses the ERA-INTERIM archive.

============================ ====== =====================
 API type                    units   example
============================ ====== =====================
Forecast API                   SI     `ForecastApi`_
TimeMachine API                SI     `TimeMachineAPI1`_
TimeMachine API + timezone\
and ISO time string            SI     `TimeMachineAPI2`_
============================ ====== =====================

Note that datetimes in the DarkSky JSON response are presented as UNIX time stamps in the local timezone. This can be converted to timezone aware date/time in python using::

    >>> import datetime as dt
    >>> import pytz
    >>> DarkSky_timestamp = 1592988827
    >>> timezone = pytz.timezone("Asia/Yangon")
    >>> tz_aware_datetime = dt.datetime.fromtimestamp(DarkSky_timestamp, timezone)
    >>> print(tz_aware_datetime)
    datetime.datetime(2020, 6, 24, 15, 23, 47, tzinfo=<DstTzInfo 'Asia/Yangon' +0630+6:30:00 STD>)


.. _ForecastApi: https://api.darksky.net/forecast/abea5442bd4f5671da76c765324df777/20.74,96.76/?exclude=currently,minutely,hourly&units=si

.. _TimeMachineAPI1: https://api.darksky.net/forecast/abea5442bd4f5671da76c765324df777/20.74,96.76,1466892000/?exclude=currently,minutely,hourly&units=si

.. _TimeMachineAPI2: https://api.darksky.net/forecast/abea5442bd4f5671da76c765324df777/20.74,96.76,2020-06-22T12:00:00+01:00/?exclude=currently,minutely,hourly&units=si

.. _DarkSky API: https://darksky.net/dev/docs


ECMWF ERA-INTERIM
.................

ERA-INTERIM  is  a  reanalysis  of  the  global  atmosphere  since  1989,  continuing  in  real  time  (Berrisford et  al.  2009).  The  ERA-INTERIM  atmospheric  model and reanalysis system has a spatial resolution of 0.7°×0.7°  and  60  atmospheric  layers.  Due  to  an  improved reanalysis system, performance of ERA-INTERIM has improved  compared  to  previous  reanalysis  data  sets such as ERA-40 (ECMWF 2007).

Currently ERA-INTERIM is superseded by the latest reanalysis "ERA5" and its agriculturally enhanced version `AgERA5`_. ERA5 and AgERA5 were not yet available at the start of development of GPRE, but hopefully the ERA-INTERIM database currently used for GPRE can be replaced by AgERA5 before the end of the project.

The ERA-INTERIM version used for GPRE has been downscaled to a 0.25x0.25 (~25km) degree grid and is available in the GPRE database since 2000. Also the climatology used by GPRE is based upon the ERA-INTERIM archive.


.. _AgERA5: https://doi.org/10.24381/cds.6c68c9bb

Combining weather data sources
..............................

Combining time-series of weather variables from different data sources can sometimes be tricky due to systematic differences between the data sources. Particularly for weather variables derived from weather models  differences in temperature may exist due to differences in the estimated elevation of the land surface at a given point. Also differences in other variables can exist due to different model physics or boundary conditions.

Some differences can be corrected for, particularly temperature differences can often be corrected using so-called "lapse-rate" corrections. However, this implies that the target elevation of both data source at that particular location is known. However, DarkSky does not provide an elevation for its target location for both its forecast response and its TimeMachine response. Therefore, such corrections are not possible using data from DarkSky.

When looking at graphs or maps that combine weather data from the archive and the forecast it is therefore useful to bear in mind that systematic offsets may be present. This can be different for different location depending on how well the datasets are consistent for that location

Phenology modelling
-------------------

For setting up the phenological model two main sources of inputs are required:

- Information on the phenological response of the crop to temperature and possibly day length. These parameters are assumed to be relatively invariant across varieties for a given crop type. Examples are the base and cutoff temperatures for phenological development.
- Information on the duration of the different growth stages of a particular crop. This information is assumed to be highly variable among varieties of a given crop.

For deriving these inputs different sources have been used. For the first category, the parameter values have been derived from existing crop simulation models and literature review on phenological development. For example the parameter files for the WOFOST crop simulation model provide information about the temperature response function of maize, rice, mungbean and sugarcane.

For calibrating the duration of the phenological stages for different crops and varieties, field data has been collected on the typical duration of crop varieties in Myanmar. Based on that information the duration of crop stages has been calibrated interactively using a workflow implemented in Jupyter notebooks.

Disease modelling
-----------------

The disease modelling is based on the disease environmental response functions for age, temperature and humidity from the `EpiRice`_ model. Note that the disease modelling does not implement the entire EpiRice model, but only the environmental response functions which are used to compute the susceptibility of the plant for the disease given the conditions. Those environmental response functions are not described in the paper but can be obtained from the `R implementation`_  of EpiRice.


.. _EpiRice: https://doi.org/10.1016/j.cropro.2011.11.009
.. _R implementation: http://adamhsparks.github.io/epirice/


