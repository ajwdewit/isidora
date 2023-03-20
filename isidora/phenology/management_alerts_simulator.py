# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Jappe Franke (jappe.franke@wur.nl), Allard de Wit (allard.dewit@wur.nl),
# Wouter Meijninger (wouter.meijninger@wur.nl) November 2017
"""Main model for managing crop management alerts
"""

import datetime

from pcse.traitlets import Instance
from pcse.base_classes import SimulationObject, ParamTemplate
from pcse.decorators import prepare_rates, prepare_states
from . import signals


# Generic Management advisories
class ManagementRules(SimulationObject):
    """defines management alerts simulation object"""
    processed_message_ids = []
    
    class Parameters(ParamTemplate):
        """Extra parameters needed in management model class"""
        MANAGEMENT_ALERTS = Instance(list)
        
    def initialize(self, day, kiosk, parameters): 
        """Initializes the SimulationObject with given parametervalues.
        
        :param self: this SimulationObject
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parameters: dict including alert parameter values (from `dataproviders.get_management_alerts`)
           under the dictionary key 'MANAGEMENT_ALERTS'
        """
        self.processed_message_ids = []     
        self.params = self.Parameters(parameters)
    
    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param self: this SimulationObject
        :param day: current day of pcse simulation
        :param drv: dict with drivers
        """
        pass
            
    @prepare_states
    def integrate(self, day, delt=1.0):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        """
        
        # Read list management alerts from database
        for rule in self.params.MANAGEMENT_ALERTS:
            if rule.BBCH_code == self.kiosk["BBCH_CURRENT_STAGE"]:
                # Check if management message has not been sent before
                if rule.message_no not in self.processed_message_ids:
                    self.processed_message_ids.append(rule.message_no)
                    # Day_of_message_sending = day - datetime.timedelta(days = rule.offset_days)
                    day_of_message_sending = day + datetime.timedelta(days = rule.offset_days)
                    # Send message
                    self._send_signal(day=day,
                                      signal=signals.MANAGEMENT_EVENT, 
                                      crop_no=rule.crop_no, 
                                      variety_no=rule.variety_no, 
                                      message_no=rule.message_no, 
                                      mday=day_of_message_sending, 
                                      message=rule.management_msg)