# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Jappe Franke (jappe.franke@wur.nl), Allard de Wit (allard.dewit@wur.nl),
# Wouter Meijninger (wouter.meijninger@wur.nl) November 2017
"""Main model for determining crop weather alerts
"""

import datetime

import numpy as np
from . import signals

import config
from pcse.traitlets import Instance, Int, List, Unicode
from pcse.exceptions import PCSEError
from pcse.base_classes import SimulationObject, ParamTemplate
from pcse.decorators import prepare_rates, prepare_states

# Convert hPa to kPa
hPa2kPa = lambda x: x/10.
# Saturated Vapour pressure [kPa] at temperature temp [C]
SatVapourPressure = lambda temp: 0.6108 * np.exp((17.27 * temp) / (237.3 + temp))


class WeatherAlerts(SimulationObject):
    """Groups all weather alerts and ensures execution of all individual alerts.
    """
    weather_alerts = List()
    
    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parameters: dict with alert parameter values
        """
        self.weather_alerts = []
        # Read list weather alerts from database
        weather_alert_tbl = parameters["WEATHER_ALERTS"]
        for alert in weather_alert_tbl:
            if alert.signal == "TMAX_STRESS":
                parvalues = eval(alert.parameters)
                # Add message_no and message to parvalues dictionary
                parvalues.update(MESSAGE_NO=alert.message_no)
                parvalues.update(MESSAGE=alert.weather_msg)
                simobj = TmaxStressThreshold(day, kiosk, parvalues)
                self.weather_alerts.append(simobj)
            elif alert.signal == "TMIN_STRESS":
                parvalues = eval(alert.parameters)
                # Add message_no and message to parvalues dictionary
                parvalues.update(MESSAGE_NO=alert.message_no)
                parvalues.update(MESSAGE=alert.weather_msg)
                simobj = TminStressThreshold(day, kiosk, parvalues)
                self.weather_alerts.append(simobj)
            elif alert.signal == "RAIN_STRESS":
                parvalues = eval(alert.parameters)
                # Add message_no and message to parvalues dictionary
                parvalues.update(MESSAGE_NO=alert.message_no)
                parvalues.update(MESSAGE=alert.weather_msg)
                simobj = RainStressThreshold(day, kiosk, parvalues)
                self.weather_alerts.append(simobj)
            elif alert.signal == "RHMAX_STRESS":
                parvalues = eval(alert.parameters)
                # Add message_no and message to parvalues dictionary
                parvalues.update(MESSAGE_NO=alert.message_no)
                parvalues.update(MESSAGE=alert.weather_msg)
                simobj = RHMAXStressThreshold(day, kiosk, parvalues)
                self.weather_alerts.append(simobj)
            elif alert.signal == "FOG":
                parvalues = eval(alert.parameters)
                # Add message_no and message to parvalues dictionary
                parvalues.update(MESSAGE_NO=alert.message_no)
                parvalues.update(MESSAGE=alert.weather_msg)
                simobj = FOGthreshold(day, kiosk, parvalues)
                self.weather_alerts.append(simobj)  
            else:
                msg = "Signal not recognized: %s" % alert.signal
                raise PCSEError(msg)
        
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        for alert in self.weather_alerts:
            alert.calc_rates(day, drv)

    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """
        
        for alert in self.weather_alerts:
            alert.integrate(day, delt)


class GenericWeatherAlert(SimulationObject):
    """Super class for defining weather alerts. Only to be inherited from.
    """
    signal = None
    weather_alert_limit = None

    def __init__(self, day, kiosk, parameters):

        if self.signal is None:
            msg = "self.signal should be defined as class atttribute in class definition of weather alert."
            self.logger.error(msg)
            raise RuntimeError(msg)

        # Get default for weather alert limit
        default = config.simulator.weather_alert_limit["DEFAULT"]
        self.weather_alert_limit = config.simulator.weather_alert_limit.get(self.signal, default)

        SimulationObject.__init__(self, day, kiosk, parameters)

    def _valid_alert(self, day):
        """Determine if we are within the range where weather data can be trusted
        Either observed (past) data or a day of the weather forecasting within the range
        that we trust the forecast (defined by config.simulator.weather_alert_limit)
        """
        if (day - datetime.date.today()).days <= self.weather_alert_limit:
            return True
        else:
            return False


# Weather alert 1: Heat stress, if Tmax > Tcrit for x number of consecutive days
class TmaxStressThreshold(GenericWeatherAlert):
    """defines weather alert Heat stress simulation object"""
    NDAYS_TMAX_CRIT = Int(0)
    FLAG_TMAX_CRIT = Int(0)
    signal = signals.TMAX_STRESS

    class Parameters(ParamTemplate):
        """Parameters needed for determining heat stress occurrence"""
        TMAX_CRIT = List()
        TMAX_STRESS_DURATION = Int()
        TMAX_CRIT_BBCH = Instance(list)
        MESSAGE_NO = Int()
        MESSAGE = Unicode()
        
    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parameter values.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop weather threshold values from crop DB
        """
        self.params = self.Parameters(parameters)

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        # IF (actual BBCH_CURRENT_STAGE equals set_BBCH) AND (Tmax > Tcrit) THAN set FLAG = 1, otherwise FLAG = 0
        BBCH = self.kiosk["BBCH_CURRENT_STAGE"]
        if BBCH in self.params.TMAX_CRIT_BBCH:
            index = self.params.TMAX_CRIT_BBCH.index(BBCH)
            TMAX_CRIT = self.params.TMAX_CRIT[index]
            self.FLAG_TMAX_CRIT = 1 if drv.TMAX >= TMAX_CRIT else 0
        else:
            # Otherwise set FLAG = 0
            self.FLAG_TMAX_CRIT = 0
        # msg  = "%s: Tmax: %5.3f, flag value: %s, %s" % (day, drv.TMAX, self.FLAG_TMAX_CRIT, BBCH)
        # print(msg)
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step

        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """

        # Calculate duration: count number of consecutive days when FLAG = 1
        # When number of consequtive days equals Tmax_duration than sent message and re-set FLAG to 0
        if self.FLAG_TMAX_CRIT:
            self.NDAYS_TMAX_CRIT += int(self.FLAG_TMAX_CRIT * delt)
        else:
            self.NDAYS_TMAX_CRIT = 0

        # IF duration >= TMAX_duration than send signal (TMAX stress alert)
        if self.NDAYS_TMAX_CRIT >= self.params.TMAX_STRESS_DURATION and self._valid_alert(day):
            self._send_signal(signal=self.signal, message_no=self.params.MESSAGE_NO, message=self.params.MESSAGE,
                              day=(day - datetime.timedelta(days=self.params.TMAX_STRESS_DURATION)))
            # Set NDAYS_MAX_CRIT back to zero
            self.NDAYS_TMAX_CRIT = 0


# Weather alert 2: Rainfall alert, if Rain > Rain_crit for x number of consecutive days
class RainStressThreshold(GenericWeatherAlert):
    """defines weather alert rainfall stress simulation object"""
    FLAG_RAIN_CRIT = Int(0)
    NDAYS_RAIN_CRIT = Int(0)
    signal = signals.RAIN_STRESS


    class Parameters(ParamTemplate):
        """Extra parameters needed in model class"""
        RAIN_CRIT = List()
        RAIN_DURATION = Int()
        RAIN_CRIT_BBCH = Instance(list)
        MESSAGE_NO = Int()
        MESSAGE = Unicode()

    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop weather threshold values from crop DB
        """
        self.params = self.Parameters(parameters)

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        
        # IF (actual BBCH_CURRENT_STAGE equals set_BBCH) AND (Rain > Rain_crit) THAN set FLAG = 1, otherwise FLAG = 0
        BBCH = self.kiosk["BBCH_CURRENT_STAGE"]
        if BBCH in self.params.RAIN_CRIT_BBCH:
            index = self.params.RAIN_CRIT_BBCH.index(BBCH)
            RAIN_CRIT = self.params.RAIN_CRIT[index]
            self.FLAG_RAIN_CRIT = 1 if (drv.RAIN*10) >= RAIN_CRIT else 0
        else:
            # Otherwise set FLAG = 0
            self.FLAG_RAIN_CRIT = 0
        # msg  = "%s: Rain: %5.3f, flag value: %s, %s" % (day, (drv.RAIN*10), self.FLAG_RAIN_CRIT, BBCH)
        # print(msg)
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """

        # Calculate duration: count number of consecutive days when FLAG = 1
        # When number of consequtive days equals Rain_duration than sent message and re-set FLAG to 0
        if self.FLAG_RAIN_CRIT:
            self.NDAYS_RAIN_CRIT += int(self.FLAG_RAIN_CRIT * delt)
        else:
            self.NDAYS_RAIN_CRIT = 0
        # IF duration >= RAIN_duration than send signal (RAIN stress alert)
        if self.NDAYS_RAIN_CRIT >= self.params.RAIN_DURATION and self._valid_alert(day):
            self._send_signal(signal=self.signal, day=(day - datetime.timedelta(days=self.params.RAIN_DURATION)),
                              message_no=self.params.MESSAGE_NO, message=self.params.MESSAGE)
            # Set NDAYS_MAX_CRIT back to zero
            self.NDAYS_RAIN_CRIT = 0


# Weather alert 3: Humidity alert. If RH > RHcrit for x number of consecutive days.
class RHMAXStressThreshold(GenericWeatherAlert):
    """defines weather alert humidity (RH) stress simulation object"""
    FLAG_RHMAX_CRIT = Int(0)
    NDAYS_RHMAX_CRIT = Int(0)
    signal = signals.RHMAX_STRESS

    class Parameters(ParamTemplate):
        """Extra parameters needed in model class"""
        RHMAX_CRIT = List()
        RHMAX_STRESS_DURATION = Int()
        RHMAX_CRIT_BBCH = Instance(list)
        MESSAGE_NO = Int()
        MESSAGE = Unicode()

    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop weather threshold values from crop DB
        """
        self.params = self.Parameters(parameters)

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        
        # Daily average saturated vapour pressure [kPa] from min&max air temperature
        SVAP_TMAX = SatVapourPressure(drv.TMAX)
        SVAP_TMIN = SatVapourPressure(drv.TMIN)
        SVAP = (SVAP_TMAX + SVAP_TMIN) / 2.
        # Relative humidity from SVAP and VAP in [%]
        RH = 100 * np.minimum(hPa2kPa(drv.VAP), SVAP)/SVAP        
        
        # IF (actual BBCH_CURRENT_STAGE equals set_BBCH) AND (RH > RHcrit) THAN set FLAG = 1, otherwise FLAG = 0
        BBCH = self.kiosk["BBCH_CURRENT_STAGE"]
        if BBCH in self.params.RHMAX_CRIT_BBCH:
            index = self.params.RHMAX_CRIT_BBCH.index(BBCH)
            self.FLAG_RHMAX_CRIT = 1 if RH >= self.params.RHMAX_CRIT[index] else 0
        else:
            # Otherwise set FLAG = 0
            self.FLAG_RHMAX_CRIT = 0
        # msg = "%s: RH: %5.3f, flag value: %s, %s" % (day, RH, self.FLAG_RHMAX_CRIT, BBCH)
        # print(msg)
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """

        # First determine if we are within the range where weather data can be trusted
        # Either observed (past) data or a day of the weather forecasting with the range
        # of self.weather_alert_limit
        if (day - datetime.date.today()).days < self.weather_alert_limit:
            valid_weather = True

        # Calculate duration: count number of consecutive days when FLAG = 1
        #  When number of consequtive days equals RHmax_duration than sent message and re-set FLAG to 0
        if self.FLAG_RHMAX_CRIT:
            self.NDAYS_RHMAX_CRIT += int(self.FLAG_RHMAX_CRIT * delt)
        else:
            self.NDAYS_RHMAX_CRIT = 0
        # If duration >= RHMAX_duration than send signal (RH stress alert)
        if self.NDAYS_RHMAX_CRIT >= self.params.RHMAX_STRESS_DURATION and self._valid_alert(day):
            self._send_signal(signal=self.signal, day=(day - datetime.timedelta(days=self.params.RHMAX_STRESS_DURATION)),
                              message_no=self.params.MESSAGE_NO, message=self.params.MESSAGE)
            # Set NDAYS_MAX_CRIT back to zero
            self.NDAYS_RHMAX_CRIT = 0
            

# Weather alert 4: Cold stress alert, if Tmin < Tcrit for x number of consecutive days
class TminStressThreshold(GenericWeatherAlert):
    """defines weather alert cold stress simulation object"""
    FLAG_TMIN_CRIT = Int()
    NDAYS_TMIN_CRIT = Int()
    signal = signals.TMIN_STRESS

    class Parameters(ParamTemplate):
        """Extra parameters needed in model class"""
        TMIN_CRIT = List()
        TMIN_STRESS_DURATION = Int()
        TMIN_CRIT_BBCH = Instance(list)
        MESSAGE_NO = Int()
        MESSAGE = Unicode()

    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop weather threshold values from crop DB
        """
        self.params = self.Parameters(parameters)

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        # IF (actual BBCH_CURRENT_STAGE equals set_BBCH) AND (Tmin < Tcrit) THAN set FLAG = 1, otherwise FLAG = 0
        BBCH = self.kiosk["BBCH_CURRENT_STAGE"]
        if BBCH in self.params.TMIN_CRIT_BBCH:
            index = self.params.TMIN_CRIT_BBCH.index(BBCH)
            TMIN_CRIT = self.params.TMIN_CRIT[index]
            self.FLAG_TMIN_CRIT = 1 if drv.TMIN <= TMIN_CRIT else 0
        else:
            # Otherwise set FLAG = 0
            self.FLAG_TMIN_CRIT = 0
        # msg  = "%s: Tmin: %5.3f, flag value: %s, %s" % (day, drv.TMIN, self.FLAG_TMIN_CRIT, BBCH)
        # print(msg)
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """
        
        # Calculate duration: count number of consecutive days when FLAG = 1
        # When number of consequtive days equals Tmin_duration than sent message and re-set FLAG to 0
        if self.FLAG_TMIN_CRIT:
            self.NDAYS_TMIN_CRIT += int(self.FLAG_TMIN_CRIT * delt)
        else:
            self.NDAYS_TMIN_CRIT = 0
        # IF duration >= TMIN_duration than send signal (TMIN stress alert)
        if self.NDAYS_TMIN_CRIT >= self.params.TMIN_STRESS_DURATION and self._valid_alert(day):
            self._send_signal(signal=self.signal, day=(day - datetime.timedelta(days=self.params.TMIN_STRESS_DURATION)),
                              message_no=self.params.MESSAGE_NO, message=self.params.MESSAGE)
            # Set NDAYS_MAX_CRIT back to zero
            self.NDAYS_TMIN_CRIT = 0
            

# Weather alert 5: Fog alert
class FOGthreshold(GenericWeatherAlert):
    """defines weather alert Fog stress simulation object"""
    FLAG_FOG_CRIT = Int()
    NDAYS_FOG_CRIT = Int()
    signal = signals.FOG_STRESS

    class Parameters(ParamTemplate):
        """Extra parameters needed in model class"""
        UMIN_CRIT = List()
        RHMAX_CRIT = List()
        TMIN_CRIT = List()
        FOG_DURATION = Int()
        CRIT_BBCH = List()
        MESSAGE_NO = Int()
        MESSAGE = Unicode()
        FOG_RELEVANT_MONTHS = List()

    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop weather threshold values from crop DB
        """
        self.params = self.Parameters(parameters)

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """        
        
        # Daily average saturated vapour pressure [kPa] from min&max air temperature
        SVAP_TMAX = SatVapourPressure(drv.TMAX)
        SVAP_TMIN = SatVapourPressure(drv.TMIN)
        SVAP = (SVAP_TMAX + SVAP_TMIN) / 2.
        # Relative humidity from SVAP and VAP in [%]
        RH = 100 * np.minimum(hPa2kPa(drv.VAP), SVAP)/SVAP
        
        # IF (actual BBCH_CURRENT_STAGE equals set_BBCH) AND (Tmin < Tcrit) AND (RH > RHcrit) AND
        # (Wind < Windcrit) THAN set FLAG = 1, otherwise FLAG = 0
        BBCH = self.kiosk["BBCH_CURRENT_STAGE"]
        if BBCH in self.params.CRIT_BBCH and day.month in self.params.FOG_RELEVANT_MONTHS:
            index = self.params.CRIT_BBCH.index(BBCH)
            RHMAX_CRIT = self.params.RHMAX_CRIT[index]
            index = self.params.CRIT_BBCH.index(BBCH)
            UMIN_CRIT = self.params.UMIN_CRIT[index]
            index = self.params.CRIT_BBCH.index(BBCH)
            TMIN_CRIT = self.params.TMIN_CRIT[index]
            self.FLAG_FOG_CRIT = 1 if (RH >= RHMAX_CRIT and
                                       drv.WIND <= UMIN_CRIT and
                                       (int(day.strftime('%j')) > 336 or int(day.strftime('%j')) < 60) and
                                       drv.TMIN <= TMIN_CRIT) else 0
        else:
            # Otherwise set FLAG = 0
            self.FLAG_FOG_CRIT = 0
        # msg  = "%s: RH: %5.3f, Wind: %5.3f, Tmin: %5.3f, flag value: %s, %s" % (day, RH, drv.WIND, drv.TMIN, self.FLAG_FOG_CRIT, BBCH)
        # print(msg)
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param self: this SimulationObject
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """
        
        # Calculate duration: count number of consecutive days when FLAG = 1
        # When number of consequtive days equals FOG_duration than sent message and re-set FLAG to 0
        if self.FLAG_FOG_CRIT:
            self.NDAYS_FOG_CRIT += int(self.FLAG_FOG_CRIT * delt)
        else:
            self.NDAYS_FOG_CRIT = 0
        # IF duration >= FOG_duration than send signal (FOG alert)
        if self.NDAYS_FOG_CRIT >= self.params.FOG_DURATION and self._valid_alert(day):
            self._send_signal(signal=self.signal, day=(day - datetime.timedelta(days=self.params.FOG_DURATION)),
                              message_no=self.params.MESSAGE_NO, message=self.params.MESSAGE)
            # Set NDAYS_MAX_CRIT back to zero
            self.NDAYS_FOG_CRIT = 0
