# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Wouter Meijninger (wouter.meijninger@wur.nl), Jappe Franke (jappe.franke@wur.nl),
# Allard de Wit (allard.dewit@wur.nl), January 2018
"""Defines the top-level simulator that integrates the phenology, management alerts and weather alerts.
"""
from pcse.base_classes import SimulationObject, StatesTemplate
from pcse.traitlets import AfgenTrait, Instance, List

from .phenology_simulator import GenericBBCHPhenology
from .management_alerts_simulator import ManagementRules
from .weather_alerts_simulator import WeatherAlerts
from . import signals

   
class MainSimulator(SimulationObject):
    """Defines the top-level simulator that integrates the phenology, management alerts and weather alerts.
    """
    phenology = Instance(SimulationObject)
    management = Instance(SimulationObject)
    weatheralert = Instance(SimulationObject)
    
    class StateVariables(StatesTemplate):
        """Development stage state variables class"""
        WEATHER_MESSAGES = List()
        MANAGEMENT_MESSAGES = List()
    
    def initialize(self, day, kiosk, parameters):
        """Initializes the SimulationObject with given parametervalues.
        
        :param self: this SimulationObject
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parameters: ParameterProvider object
        """
        
        self._connect_signal(self._on_TMAX_STRESS, signal=signals.TMAX_STRESS)
        self._connect_signal(self._on_RAIN_STRESS, signal=signals.RAIN_STRESS)
        self._connect_signal(self._on_RH_STRESS, signal=signals.RHMAX_STRESS)
        self._connect_signal(self._on_TMIN_STRESS, signal=signals.TMIN_STRESS)
        self._connect_signal(self._on_FOG_STRESS, signal=signals.FOG_STRESS)
        
        self._connect_signal(self._on_MANAGEMENT_EVENT, signal=signals.MANAGEMENT_EVENT)
        self.states = self.StateVariables(kiosk, WEATHER_MESSAGES=[], MANAGEMENT_MESSAGES=[])

        self.phenology = GenericBBCHPhenology(day, kiosk, parameters)
        self.management = ManagementRules(day, kiosk, parameters)
        self.weatheralert = WeatherAlerts(day, kiosk, parameters)
        
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        self.phenology.calc_rates(day, drv)
        self.management.calc_rates(day, drv)
        self.weatheralert.calc_rates(day, drv)
        
    def integrate(self, day, delt=1):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """
        self.phenology.integrate(day, delt)
        self.management.integrate(day, delt)
        self.weatheralert.integrate(day, delt)
    
    # Weather alerts
    def _on_TMAX_STRESS(self, day=None, signal=None, crop_no=None,
                        variety_no=None, message_no=None,
                        mday=None, message=None):
        self.states.WEATHER_MESSAGES.append(day.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
            
    def _on_RAIN_STRESS(self, day=None, signal=None, crop_no=None,
                        variety_no=None, message_no=None,
                        mday=None, message=None):
        self.states.WEATHER_MESSAGES.append(day.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
        
    def _on_RH_STRESS(self, day=None, signal=None, crop_no=None,
                        variety_no=None, message_no=None,
                        mday=None, message=None):
        self.states.WEATHER_MESSAGES.append(day.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
    
    def _on_TMIN_STRESS(self, day=None, signal=None, crop_no=None,
                        variety_no=None, message_no=None,
                        mday=None, message=None):
        self.states.WEATHER_MESSAGES.append(day.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
        
    def _on_FOG_STRESS(self, day=None, signal=None, crop_no=None,
                        variety_no=None, message_no=None,
                        mday=None, message=None):
        self.states.WEATHER_MESSAGES.append(day.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
    
    # Management alerts
    def _on_MANAGEMENT_EVENT(self, day=None, signal=None, crop_no=None, 
                                      variety_no=None, message_no=None, 
                                      mday=None, message=None):
        # Send management message to JSON output
        self.states.MANAGEMENT_MESSAGES.append(mday.strftime('{"day":"%Y-%m-%d",') + '"msg_id":'+'"'+str(message_no)+'",' + '"msg":' + '"'+message+'"}')
