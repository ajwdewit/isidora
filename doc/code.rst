
GPRE code documentation
=======================

This section provides an overview of all code documentation that is part of GPRE. This part of the documentation is mostly generated from the documentation headers in the source code. Further, it can be used to quickly navigate the source code as each documented function or class is linked to the relevant code section using the [source] link.

GPRE service implementation
---------------------------

Code for all specific GPRE services is described here

Weather service
...............

.. automodule:: gpre.create_weather_graph
    :members: generate_weather_charts_for_location, get_weather_data, generate_WIND_chart_plotly,
              generate_RAIN_chart_plotly, generate_TMAX_chart_plotly, generate_TMIN_chart_plotly

.. automodule:: gpre.get_weather_forecast_map_data
    :members: get_weather_forecast_map_data

Crop stage prediction service
.............................

.. automodule:: gpre.predict_crop_stages
    :members: predict_crop_stages

Disease service
...............

.. automodule:: gpre.create_disease_graph
    :members: generate_disease_chart_for_location, write_disease_excel_output, compute_disease_timeseries,
              run_disease_model, generate_disease_graph, compute_historical_stats

.. automodule:: gpre.get_disease_forecast_map_data
    :members: get_disease_forecast_map_data


Webserver scripts
-----------------

All webserver scripts are thin wrappers around GPRE scripts that perform the actual processing. All webserver scripts use Flask through a WSGI interface for exposing the HTTP URL.

.. autofunction:: flask_app.get_weather_charts

.. autofunction:: flask_app.get_weather_forecast

.. autofunction:: flask_app.get_disease_chart

.. autofunction:: flask_app.get_disease_forecast

.. autofunction:: flask_app.get_crop_stages

.. autofunction:: flask_app.run_darksky_caching

.. autofunction:: flask_app.run_disease_caching

.. autofunction:: flask_app.download_file


Simulator for phenology, management alerts and weather alerts
-------------------------------------------------------------

Simulation of crop phenology
............................

.. autoclass:: phenology.phenology_simulator.GenericBBCHPhenology
    :members:


Simulation of management alerts simulator
.........................................

.. autoclass:: phenology.management_alerts_simulator.ManagementRules
    :members:


Simulation of weather alerts simulator
......................................

.. autoclass:: phenology.weather_alerts_simulator.WeatherAlerts
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.GenericWeatherAlert
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.TmaxStressThreshold
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.RainStressThreshold
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.RHMAXStressThreshold
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.TminStressThreshold
    :members: initialize

.. autoclass:: phenology.weather_alerts_simulator.FOGthreshold
    :members: initialize


Data providers
..............

.. automodule:: phenology.data_providers
    :members:   
    
