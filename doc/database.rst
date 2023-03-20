GPRE database
=============

Overview of schemas
-------------------

The GPRE database consists of two schemas:

  - The ``gpre`` schema which contains all data required to run the GPRE services
  - the ``gpre_staging`` schema which contains copies or links to the data in the ``gpre`` schema and can be used to the test and experiment with new services, crops or varietes.

When setting the environment variable ``DEVELOP=1``  GPRE will always connect to the ``gpre_staging`` schema. See also the section on *System and Installation*. Otherwise the ``gpre`` schema will be used.

Most of the objects in the ``gpre_staging`` schema are views to the ``gpre`` schema in order to avoid data duplication. However, in order to add and test new crops the following objects are defined as tables with the same structure as the tables in the ``gpre`` schema:

    - `crop`
    - `crop_parameter_value`
    - `varieties`
    - `variety_parameter_value`
    - `management_alerts`
    - `weather_alerts`

Overview of all objects
-----------------------

The following table provides an overview of all objects in the ``gpre`` schema. Object types are provided as table `T`, view `V`` or procedure `P`. Note that some tables are currently not used or have been replaced by views. Those tables have been kept in the database scheme as they may become relevant in the future.

=============================== ====== =================================================================================
Name                             Type   Description
=============================== ====== =================================================================================
crop                              T     Stores unique crop ID and name
crop_parameter_value              T     Stores crop parameter values for BBCH phenology model
date_manipulation                 T     Auxiliary table for operations involving dates (e.g. group-by)
disease_map_cache                 T     Stores the disease map data at regional level for Myanmar
era_grid                          T     The grid definition of the ERA-INTERIM historical weather archive
grid                              T     The 0.1 degree grid definition for Myanmar
grid_005                          T     An alternative 0.05 degree grid definition for Myanmar *not used*
grid_weather_forecast             T     Table for storing the weather forecast *not used* (DarkSky API is now used)
grid_weather_forecast_d0          T     Table for storing the first day of the weather forecast *not used*
grid_weather_lta                  V     View for providing the long-term-average historical weather data
grid_weather_lta_tbl              T     Table for providing the long-term-average historical weather data *not used*
grid_weather_observed             V     View for providing the actual historical weather data
grid_weather_observed_tbl         T     Table for providing the actual historical weather data *not used*
management_alerts                 T     Table for providing management alerts linked to BBCH stages
regions                           T     Table for providing information regions in Myanmar
season                            T     Stores the season definitions
varieties                         T     Stores unique variety ID and variety name for each crop
variety_parameter_value           T     Stores parameters for BBCH model specific for a variety
weather_alerts                    T     Stores weather alerts linked to a BBCH phenological stage
weather_hres_grid_myanmar         T     Stores historical weather data from the ERA-INTERIM archive
weather_hres_grid_myanmar_lta     T     Stores long-term-average weather derived from the ERA-INTERIM archive
weather_map_cache                 T     Stores the weather forecast for each region derived from DarkSky
get_grid                          P     Returns grid ID for given latitude, longitude and cellsize
get_grid_weather                  P     Returns actual weather data for given grid ID and year range
=============================== ====== =================================================================================

Base tables
-----------

The base tables in the database define properties that are used in nearly all other tables and views and are used to define relationships. The primary keys in those tables could function as foreign keys in the other tables although this is currently not enforced in the database.

Crop table
..........

Stores the unique crop_no together with a crop_name.

+-----------+-------------+------+-----+---------+-------+
| Field     | Type        | Null | Key | Default | Extra |
+===========+=============+======+=====+=========+=======+
| crop_no   | int(11)     | NO   | PRI | NULL    |       |
+-----------+-------------+------+-----+---------+-------+
| crop_name | varchar(40) | YES  |     | NULL    |       |
+-----------+-------------+------+-----+---------+-------+

Varieties table
...............

Stores the unique crop_no, variety_no together with a variety_name.

+--------------+-------------+------+-----+---------+-------+
| Field        | Type        | Null | Key | Default | Extra |
+==============+=============+======+=====+=========+=======+
| crop_no      | int(11)     | NO   | PRI | NULL    |       |
+--------------+-------------+------+-----+---------+-------+
| variety_no   | int(11)     | NO   | PRI | NULL    |       |
+--------------+-------------+------+-----+---------+-------+
| variety_name | varchar(40) | YES  |     | NULL    |       |
+--------------+-------------+------+-----+---------+-------+

Seasons table
.............

Stores the identifiers for the different cropping seasons. Management alerts can be different for different cropping seasons and therefore it can be useful to descriminate between seasons.

+-------------------+-------------+------+-----+-----------------------------+
| Field             | Type        | Null | Key | Description                 |
+===================+=============+======+=====+=============================+
| season_no         | int(11)     | NO   | PRI | Unique season ID            |
+-------------------+-------------+------+-----+-----------------------------+
| season_name       | varchar(40) | YES  |     | Name of the cropping season |
+-------------------+-------------+------+-----+-----------------------------+
| season_definition | varchar(60) | YES  |     | Description of the season   |
+-------------------+-------------+------+-----+-----------------------------+


Regions table
.............

Stores unique code of the lowest level administrative regions (GID_3) including the latitude/longitude of each region and the administrative regions to which it belongs.

+-----------+--------------+------+-----+---------+-------+
| Field     | Type         | Null | Key | Default | Extra |
+===========+==============+======+=====+=========+=======+
| GID_0     | char(3)      | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| NAME_0    | varchar(50)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| GID_1     | varchar(10)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| NAME_1    | varchar(50)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| GID_2     | varchar(20)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| NAME_2    | varchar(50)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| GID_3     | varchar(20)  | NO   | PRI | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| NAME_3    | varchar(50)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| TYPE_3    | varchar(50)  | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| longitude | decimal(8,3) | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+
| latitude  | decimal(8,3) | NO   |     | NULL    |       |
+-----------+--------------+------+-----+---------+-------+

grid table
..........

Stores the unique ``grid_no`` for the grid definition in Myanmar. Moreover it provides the latitude and longitude of the grid centroids, the average elevation of the grid terrain (over land), and whether the grid contains land (``has_land`` = 1). The additional column ``idgrid_cgms14glo`` provides the ID of the nearest grid in the ``era_grid`` table. The latter is required to build the link between the GPRE grid definition and the global ERA-INTERIM grid definition.

The tables ``grid_005`` has the same structure as the ``grid`` table. The structure of the table ``grid_era5`` is also similar.

+------------------+---------+------+-----+---------+-------+
| Field            | Type    | Null | Key | Default | Extra |
+==================+=========+======+=====+=========+=======+
| grid_no          | int(11) | NO   | PRI | NULL    |       |
+------------------+---------+------+-----+---------+-------+
| latitude         | float   | NO   |     | NULL    |       |
+------------------+---------+------+-----+---------+-------+
| longitude        | float   | NO   | MUL | NULL    |       |
+------------------+---------+------+-----+---------+-------+
| elevation        | float   | YES  |     | NULL    |       |
+------------------+---------+------+-----+---------+-------+
| has_land         | int(11) | NO   |     | NULL    |       |
+------------------+---------+------+-----+---------+-------+
| idgrid_cgms14glo | int(11) | NO   |     | NULL    |       |
+------------------+---------+------+-----+---------+-------+



Weather tables
--------------

Currently, only the historical weather data and its climatology is stored in the GPRE database because the weather forecast is directly derived from the DarkSky API. The historical data is derived from the ERA-INTERIM archive that is available at Wageningen Environmental Research (WEnR). Data from the WEnR data is transferred each day for the Myanmar window. The tables are replicated from the WEnR database and therefore have a slightly different structure compared to the other weather tables. The mapping between the WEnR structure and the GPRE structure is accomplished through the views ``grid_weather_observed`` and ``grid_weather_lta``.

The weather tables that store the ERA-INTERIM weather archive (``weather_hres_grid_myanmar``) and its climatology (``weather_hres_grid_myanmar_lta``) have the following structure.

+-----------------+--------------+------+-----+----------------------------------------------+
| Field           | Type         | Null | Key | Description and units                        |
+=================+==============+======+=====+==============================================+
| idgrid          | int(11)      | NO   | PRI | Unique grid ID                               |
+-----------------+--------------+------+-----+----------------------------------------------+
| day             | date         | NO   | PRI | date or day number                           |
+-----------------+--------------+------+-----+----------------------------------------------+
| temperature_max | decimal(3,1) | NO   |     | degrees Celsius                              |
+-----------------+--------------+------+-----+----------------------------------------------+
| temperature_min | decimal(3,1) | NO   |     | degrees Celsius                              |
+-----------------+--------------+------+-----+----------------------------------------------+
| temperature_avg | decimal(3,1) | NO   |     | degrees Celsius                              |
+-----------------+--------------+------+-----+----------------------------------------------+
| vapourpressure  | decimal(4,2) | NO   |     | vapour pressure hPa                          |
+-----------------+--------------+------+-----+----------------------------------------------+
| windspeed       | decimal(5,1) | NO   |     | wind speed m/sec at 10m                      |
+-----------------+--------------+------+-----+----------------------------------------------+
| precipitation   | decimal(4,1) | NO   |     | precipitation in mm/day                      |
+-----------------+--------------+------+-----+----------------------------------------------+
| e0              | decimal(4,2) | NO   |     | open water reference evaporation in mm/day   |
+-----------------+--------------+------+-----+----------------------------------------------+
| es0             | decimal(4,2) | NO   |     | soil reference evaporation in mm/day         |
+-----------------+--------------+------+-----+----------------------------------------------+
| et0             | decimal(4,2) | NO   |     | crop reference evapotranspiration in mm/day  |
+-----------------+--------------+------+-----+----------------------------------------------+
| radiation       | decimal(6,0) | NO   |     | Incoming global radiation in kJ/m2/day       |
+-----------------+--------------+------+-----+----------------------------------------------+
| snowdepth       | decimal(6,2) | YES  |     | Snow depth in cm                             |
+-----------------+--------------+------+-----+----------------------------------------------+


The weather tables and views whose name starts with "grid_weather" have a structure that is similar to the table below.

+----------------------+---------------+------+-----+----------------------------------------------+
| Field                | Type          | Null | Key | Description and units                        |
+======================+===============+======+=====+==============================================+
| grid_no              | int(11)       | NO   | PRI | grid identifier                              |
+----------------------+---------------+------+-----+----------------------------------------------+
| day                  | date          | NO   | PRI | date or day number (in case of LTA           |
+----------------------+---------------+------+-----+----------------------------------------------+
| maximum_temperature  | decimal(10,5) | NO   |     | degrees Celsius                              |
+----------------------+---------------+------+-----+----------------------------------------------+
| minimum_temperature  | decimal(10,5) | NO   |     | degrees Celsius                              |
+----------------------+---------------+------+-----+----------------------------------------------+
| vapour_pressure      | decimal(10,5) | NO   |     | vapour pressure hPa                          |
+----------------------+---------------+------+-----+----------------------------------------------+
| windspeed            | decimal(10,5) | NO   |     | wind speed m/sec at 10m                      |
+----------------------+---------------+------+-----+----------------------------------------------+
| rainfall             | decimal(10,5) | NO   |     | precipitation in mm/day                      |
+----------------------+---------------+------+-----+----------------------------------------------+
| e0                   | decimal(10,5) | NO   |     | open water reference evaporation in mm/day   |
+----------------------+---------------+------+-----+----------------------------------------------+
| es0                  | decimal(10,5) | NO   |     | soil reference evaporation in mm/day         |
+----------------------+---------------+------+-----+----------------------------------------------+
| et0                  | decimal(10,5) | NO   |     | crop reference evapotranspiration in mm/day  |
+----------------------+---------------+------+-----+----------------------------------------------+
| calculated_radiation | decimal(10,5) | NO   |     | Incoming global radiation in kJ/m2/day       |
+----------------------+---------------+------+-----+----------------------------------------------+
| snow_depth           | decimal(10,5) | YES  |     | Snow depth in cm                             |
+----------------------+---------------+------+-----+----------------------------------------------+


Crop parameters and alerts
--------------------------

Tables for phenology parameters
...............................

There are two tables for storing crop phenological parameters, these are named ``crop_parameter_value`` and ``variety_parameter_value``. The parameter values for a specific variety take precedence over the parameter for the crop. In practices this means that temperature response functions for phenology are often specified per crop, while the number of degree-days for reaching a phenology stage are described for each variety specifically. Both tables have a structure similar to the one below.

+-----------------------+--------------+------+-----+----------------------------------+
| Field                 | Type         | Null | Key | Description                      |
+=======================+==============+======+=====+==================================+
| crop_no               | int(11)      | NO   | PRI | The crop number                  |
+-----------------------+--------------+------+-----+----------------------------------+
| parameter_code        | varchar(20)  | NO   | PRI | the parameter name               |
+-----------------------+--------------+------+-----+----------------------------------+
| parameter_value       | varchar(255) | YES  |     | the parameter value              |
+-----------------------+--------------+------+-----+----------------------------------+
| parameter_description | varchar(255) | YES  |     | the description of the parameter |
+-----------------------+--------------+------+-----+----------------------------------+

Tables for messages and alerts
..............................

The system contains two tables for storing messages and alerts. Management messages are stored in the table ``management_alerts`` which provides the crop management messages linked to a particular crop BBCH stage, see table below.

+----------------+-------------+------+-----+--------------------------------------------------------+
| Field          | Type        | Null | Key | Description                                            |
+================+=============+======+=====+========================================================+
| crop_no        | int(11)     | NO   | PRI | crop ID                                                |
| variety_no     | int(11)     | NO   | PRI | variety ID                                             |
| season_no      | int(11)     | NO   | PRI | season ID                                              |
| message_no     | int(11)     | NO   | PRI | message ID                                             |
| BBCH_code      | varchar(45) | YES  |     | BBCH code to which the message corresponds             |
| offset_days    | int(11)     | YES  |     | days before (-) or after (+) reaching the BBCH stage   |
| management_msg | longtext    | YES  |     | The message itself                                     |
+----------------+-------------+------+-----+--------------------------------------------------------+

Weather alerts are signalled when (a combination of) adverse weather conditions occur that are important for
a farmer to take action on. Such weather alerts can for example be defined as the probably of fog occurrence on three consecutive days, which would increase the changes of development of late blight in potato. The definition of the weather alerts is done in the table ``weather_alerts`` (see below). The parameters required for such an alert can be highly crop specific and therefore the parameters are stored in the table as a JSON string which is parsed by the system.

+-------------+--------------+------+-----+-----------------------------------------------------------------+
| Field       | Type         | Null | Key | Description                                                     |
+=============+==============+======+=====+=================================================================+
| crop_no     | int(11)      | NO   | PRI | crop ID                                                         |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| variety_no  | int(11)      | NO   | PRI | variety ID                                                      |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| season_no   | int(11)      | NO   | PRI | season ID                                                       |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| message_no  | int(11)      | NO   | PRI | message ID                                                      |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| parameters  | varchar(255) | YES  |     | parameters for weather alert as JSON string                     |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| weather_msg | longtext     | YES  |     | the weather alert message                                       |
+-------------+--------------+------+-----+-----------------------------------------------------------------+
| signal      | varchar(255) | YES  |     | the signal to be broadcasted, see the ``pcse.signals`` module   |
+-------------+--------------+------+-----+-----------------------------------------------------------------+


Caching tables
--------------

Caching tables are used to stored pre-computed results which would otherwise take to long provide to the user. The system contains two caching tables, one for weather maps ``weather_map_cache`` and one for disease maps  ``disease_map_cache``. The tables just store the computed results as JSON for a given day (and disease). The HTTP API is simply returning the data for the current day from the relevant table.

