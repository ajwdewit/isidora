# -*- coding: utf-8 -*-
# Copyright Alterra, Wageningen-UR
# Jappe Franke (jappe.franke@wur.nl), Allard de Wit (allard.dewit@wur.nl), November 2017
"""Houses webservice code in main and sets up and runs PCSE crop model
"""

import datetime as dt

import config
from pcse.traitlets import Float, AfgenTrait, Instance, List, Integer
from pcse.base_classes import (SimulationObject, ParamTemplate, RatesTemplate, StatesTemplate, ParameterProvider)
from pcse.decorators import prepare_rates, prepare_states
from pcse import signals
from pcse.util import daylength, limit


class GenericBBCHPhenology(SimulationObject):
    """defines geobis phenology simulation object"""

    _PHENO_TF = AfgenTrait

    class Parameters(ParamTemplate):
        """Extra parameters needed in pcse model class"""
        PHENO_TBASE = Float()
        PHENO_TOPT1 = Float()
        PHENO_TOPT2 = Float()
        PHENO_TMAX = Float()
        PHENO_DLC = Float()
        PHENO_DLO = Float()
        PHENO_IDSL  = Integer()
        BBCH_CODES = List()
        BBCH_TSUMS = List()

    class StateVariables(StatesTemplate):
        """Development stage state variables class"""
        DVS = Float()
        BBCH_CURRENT_STAGE = Instance(str)
        BBCH_TARGET_TSUM = Float()

        # Collection of bbch dates @ ∑TU(°Cd)
        BBCH_DATES = List()
        # Set day of crop maturity explicitly
        DATE_OF_CROP_MATURITY = Instance(dt.date)

    class RateVariables(RatesTemplate):
        """Development rate variables class"""
        DVR = Float()
        RF_PHOTO = Float()

    def initialize(self, day, kiosk, parametervalues):
        """Initializes the SimulationObject with given parametervalues.
        
        :param day: start date of the simulation
        :param kiosk: variable kiosk of this PCSE instance
        :param parametervalues: dict with crop parameter values
        """
        
        BBCH_CODES = []
        BBCH_TSUMS = []
        
        # Looping over parameter values
        for name, value in parametervalues.items():
            if name.startswith("BBCH"):
                BBCH_CODES.append(name)
                BBCH_TSUMS.append(value)
       
        parametervalues.set_override("BBCH_CODES", BBCH_CODES, check=False)
        parametervalues.set_override("BBCH_TSUMS", BBCH_TSUMS, check=False)
        
        self.params = self.Parameters(parametervalues)
        self.rates = self.RateVariables(kiosk)

        # Generate temperature function from cardinal temperatures
        p = self.params
        Tfunc = [p.PHENO_TBASE,0.,
                 p.PHENO_TOPT1, (p.PHENO_TOPT1 - p.PHENO_TBASE),
                 p.PHENO_TOPT2, (p.PHENO_TOPT1 - p.PHENO_TBASE),
                 p.PHENO_TMAX, 0.]
        self._PHENO_TF = Tfunc

        bbch_current_stage = self.params.BBCH_CODES.pop(0)
        # Pop list twice for correct length!!
        bbch_current_tsum = self.params.BBCH_TSUMS.pop(0)
        bbch_current_tsum = self.params.BBCH_TSUMS.pop(0)

        bbch_dates = ['{"day":"%s","bbch":"%s","t_sum":%s}' % \
                      (day.strftime('%Y-%m-%d'), bbch_current_stage, 0.)]
        self.states = self.StateVariables(kiosk, DVS=0., BBCH_DATES=bbch_dates,
                                          BBCH_CURRENT_STAGE=bbch_current_stage,
                                          BBCH_TARGET_TSUM=bbch_current_tsum,
                                          DATE_OF_CROP_MATURITY=None,
                                          publish=["DVS", "BBCH_CURRENT_STAGE"])

    @prepare_rates
    def calc_rates(self, day, drv):
        """Calculate the rates of change given the current states and driving
        variables (drv).
        
        :param day: current day of pcse simulation
        :param drv: dict with drivers(temperature)   
        """
        p = self.params
        r = self.rates

        # Reduction factor for photoperiod
        r.RF_PHOTO = 1.0
        if p.PHENO_IDSL >= 1:
            DAYLP = daylength(day, drv.LAT)
            r.RF_PHOTO = limit(0., 1., (DAYLP - p.PHENO_DLC) / (p.PHENO_DLO - p.PHENO_DLC))

        # Effective temperature from piecewise linear function based on cardinal temperatures
        # and daily average temperature (drv.TEMP)
        Teff = self._PHENO_TF(drv.TEMP)
        self.rates.DVR = Teff * r.RF_PHOTO

    @prepare_states
    def integrate(self, day, delt=1):
        """Integrate the rates of change on the current state variables multiplied by the time-step
        
        :param self: this SimulationObject
        :param day: current day of pcse simulation
        :param delt: integer for calculating every delt days; in this case 1
        
        BBCH and ∑TU data from Agronomy Research 10 (1–2), 283–294, 2012::
        
            Table 1. Mean values and standard deviation of the plastochron interval (PI) 
            (°Ch node-1) and hourly thermal unit accumulated (∑TU)  (°Ch) for  different  phenological stages of melon  cultivars 
            expressed through the BBCH Code. S – sowing; E –emergence; 5th L – fifth leaf.         
    
            BBCH Code            01–10                10–15                     > 15                      71
            Thermal Time(∑TU)    PI (S–E)(°Ch n-1)    PI (E–5th L) (°Ch n-1)    PI (> 5th L) (°Ch n-1)    PI (Fruit Setting) (°Ch n-1)
            ‘DRT’                1,935 ±177          3,322 ±513               588    ±16                  27,432 ±944
            ‘Honey Max’          1,935 ±177          3,746 ±578               625    ±17                  sd
            ‘Sundew’             2,337 ±213          2,073 ±320               625    ±17                  29,956 ±1031
            ‘Fila’               2,222 ±203          3,986 ±615               625    ±19                  sd
            
            ‘Ruidera’            1,801 ±164          3,196 ±493               668    ±18                  28,069 ±966
          
            SumTd/n ‘Ruidera’    75.04 ±6.83         133.17 ±20.54            27.83  ±0.75                1169.54 ±40.25
            SumTd   ‘Ruidera’    75.04 ±6.83         208.21 ±27.37            236.04 ±28.12               1405.58 ±68.37
    
            
            b1 = ["BBCH 01-10",75.04]
            b2 = ["BBCH 10-15",208.21]
            b3 = ["BBCH >15",236.04]
            b4 = ["BBCH 71",1405.58]
        
        Regarding the Bitter Gourd Plant of GEOBIS Pilot:
            •    01 Seed Sowing on: From 02/03/2016 to 02/04/2016 (Its depends farmers to farmers)
            •    10 Seedling emergence : 4/5 days after sowing - From 06th - 7th March to 06th - 7th April 
            •    15 4/5 true leaf development: 15-20 days after sowing – From 17th - 22nd March to 17th - 22nd April 
            •    21 Plant vining : 25-30 days after sowing -  From 27th March – 2nd April to 27th April -  2nd May
            •    61 Estimated Date of Days of flowering: 45-50 days after sowing - From 17th April – 22nd April  or 17th May – 22nd May
            •    71 Estimated date of Days of 1st Harvest: 55-60 days after sowing - From 27th April – 2nd May to 27th May – 2nd June
            •    89 Estimated date of last Harvest: 50-60 days after first harvest - 17th June-27th June to 17th July – 27th July.     
        
        Parameter values for bitter gourd for BBCH::
        
            bbch_table= [
              [0,"BBCH_01",0.0,"seed sowing"],
              [1,"BBCH_10",54.7,"seedling emergence"],
              [2,"BBCH_15",182.3,"5th leaf"],
              [3,"BBCH_21",289.6,"first vining"],
              [4,"BBCH_61",510.7,"first flowering"],
              [5,"BBCH_81",612.1,"first harvest"],
              [6,"BBCH_89",1328.2,"last harvest"]
            ]
        """
        # Calculate states and rates
        self.states.DVS += self.rates.DVR * delt
        
        if self.states.DVS >= self.states.BBCH_TARGET_TSUM:
            if self.params.BBCH_TSUMS:
                self.states.BBCH_CURRENT_STAGE = self.params.BBCH_CODES.pop(0)
                self.states.BBCH_TARGET_TSUM = self.params.BBCH_TSUMS.pop(0)
            else:
                self.states.BBCH_CURRENT_STAGE = self.params.BBCH_CODES.pop(0)
                self._send_signal(signal=signals.crop_finish, day=day)
                self._send_signal(signals.terminate)

            self.states.BBCH_DATES.append('{"day":"%s","bbch":"%s","t_sum":%s}' %
                                          (day.strftime('%Y-%m-%d'),self.states.BBCH_CURRENT_STAGE,
                                           str(round(self.states.DVS,1))))        
        # Update all state variables of this and any sub-SimulationObjects
        self.touch()      
                                      
    @prepare_states
    def finalize(self, day):
        """do some final calculations when the simulation is finishing.
        
        :param self: this SimulationObject
        :param day: current day of pcse simulation
        """
        self.states.DATE_OF_CROP_MATURITY = day
        

def ejson(e):
    """returns errors as a json string
    
    :param e: string error message
    :returns string: json string
    """
    return '{"error":"%s"}' %e

