.. GEOBIS_ref_Guide documentation master file, created by
   sphinx-quickstart on Tue Jan 02 09:07:26 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GEOBIS crop model service
=========================

The GEOBIS crop model service has been developed as part of the Geodata Based Information Services for smallholder farmers in Bangladesh (GEOBIS, which is funded by G4AW).

GEOBIS uses spatial and other geodata for providing effective, time- and location- and crop stage specific advisory services to smallholder farmers in Bangladesh. It is aimed at improving agricultural productivity and farmer income, upgrading agricultural zoning and at improving the management of weather related emergencies.

GEOBIS will provide farmers with weather related information, advice on the usage of seeds, land preparation, sowing, transplanting, irrigation, fertilizers and agrochemicals, and advice on preventive and remedial measures for controlling pest and diseases. 

Farmers will be informed through mobile phones, call centre, a website, app-based services as well as personal advice via extension officers and Lal Teer’s field staff. 

The GEOBIS crop model (web) service provides crop growth data (BBCH) for a number of crops that are grown in Bangladesh:

+--------------+----------+---------------+----------------------------------+
| Crop         | Crop ID  | Variety ID's  |         Seasons (ID's)           |
+--------------+----------+---------------+--------+------------+------------+
|              |          |               | Rabi   |  Kharif-I  |  Kharif-II |
+--------------+----------+---------------+--------+------------+------------+
|              |          |               | 1      |  2         |  3         |
+==============+==========+===============+========+============+============+
| Maize        |    1     |    1-24       | **Y**  |     Y      |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Tomato       |    2     |    1-32       | **Y**  |     N      |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Potato       |    3     |    1-82       | **Y**  |     N      |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Radish       |    4     |    1-12       | **Y**  |     N      |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Pumpkin      |    5     |    1-9        | **Y**  |     Y      |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Chilli       |    6     |    1-7        | **Y**  |     Y      |     Y      |
+--------------+----------+---------------+--------+------------+------------+
| Okra         |    7     |    1-8        |   N    |   **Y**    |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Cucumber     |    8     |    1-5        |   N    |   **Y**    |     N      |
+--------------+----------+---------------+--------+------------+------------+
| Bottle Gourd |    9     |    1-12       | **Y**  |     N      |     Y      |
+--------------+----------+---------------+--------+------------+------------+
| Bitter Gourd |   10     |    1-5        |   N    |   **Y**    |     Y      |
+--------------+----------+---------------+--------+------------+------------+
| Rice         |   11     |    1-8        | **Y**  |     Y      |     Y      |
+--------------+----------+---------------+--------+------------+------------+
| Egg plant    |   12     |    1-?        | **Y**  |     ?      |     Y      |
+--------------+----------+---------------+--------+------------+------------+

*(Y: yes; N: no)*
**(Y: operational)**
(Y: to be implemented)

Start & end of seaons:

- Rabi: 16 October to 15 March
- Kharif-1: 16 March to 15 July
- Kharif-2: 16 July to 15 October

The GEOBIS crop model service is based on PCSE (the Python Crop Simulation Environment) and delivers a JSON string containing the predicted crop growth plus alerts for crop treatments and possible weather induced stress.

A request (consisting of a crop ID, a location and a sowing date): e.g. http://27.147.142.61/geobis/request.py?cropid=10&lat=25.1233&lon=89.21333&sowday=20171230

results in the following JSON output::

	{"type":"cached",
	"request":"cropid=10&lat=25.1233&lon=89.21333&sowday=20171230&varid=-1",
	"result":{
	"phenology":[
	{"day":"2017-12-30","bbch":"BBCH_01","t_sum":0.0},
	{"day":"2018-01-07","bbch":"BBCH_10","t_sum":28.9},
	{"day":"2018-02-12","bbch":"BBCH_15","t_sum":150.8},
	{"day":"2018-03-05","bbch":"BBCH_21","t_sum":288.8},
	{"day":"2018-03-14","bbch":"BBCH_41","t_sum":374.9},
	{"day":"2018-03-21","bbch":"BBCH_61","t_sum":446.8},
	{"day":"2018-04-01","bbch":"BBCH_81","t_sum":583.9}
	],
	"weatheralerts":[
	{"day":"2017-12-30","msg_id":"502","msg":"cold stress"},
	{"day":"2018-01-02","msg_id":"502","msg":"cold stress"}
	],
	"managementalerts":[
	{"day":"2017-12-24","msg_id":"1","msg":"Management seed quality"},
	{"day":"2017-12-24","msg_id":"2","msg":"Management fertilizer"},
	{"day":"2017-12-24","msg_id":"3","msg":"Management pesticide"},
	{"day":"2017-12-31","msg_id":"4","msg":"Management pesticide"},
	{"day":"2018-02-05","msg_id":"5","msg":"Management irrigation"},
	{"day":"2018-02-05","msg_id":"6","msg":"Management waterlogging"},
	{"day":"2018-02-26","msg_id":"7","msg":"Management sticking"},
	{"day":"2018-03-07","msg_id":"8","msg":"Management pesticide"},
	{"day":"2018-03-07","msg_id":"9","msg":"Management virus control"},
	{"day":"2018-03-14","msg_id":"10","msg":"Management fruit fly"},
	{"day":"2018-03-25","msg_id":"11","msg":"Management irrigation"}
	]
	}}


The GEOBIS crop model service has been developed by Wageningen Environmental Research (WENR, formerly known as Alterra) together with with:

- Lal Teer Seed Limited (Bangladesh)
- Capacity building and research: Interdisciplinary Centre for Food Security (ICF) at Bangladesh Agricultural University (BAU) (Bangladesh)
- IT-platform and web-based solutions: mPower (Bangladesh)

More information on GEOBIS can be found `here <https://g4aw.spaceoffice.nl/files/files/G4AW/project%20leaflets/A4%20leaflet%20GEOBIS%20LR.pdf>`_.

More information on G4AW can be found `here <https://g4aw.spaceoffice.nl/nl/>`_.

.. image:: figures/G4AW.png

.. toctree::
   :maxdepth: 2

Reference guide
---------------
.. toctree::
   :maxdepth: 3
   
   introduction.rst
   weather.rst
   phenological_modelling.rst
   mysql_database.rst

User guide
----------
.. toctree::
   :maxdepth: 3
   
   daily_monitoring.rst
   crops.rst
   
Code documentation
------------------
   
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
