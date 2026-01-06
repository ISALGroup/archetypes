# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 16:02:14 2025

@author: Antoine
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 12:04:45 2024

@author: Antoine
"""

import pandas as pd
import numpy as np
import csv
import inspect
from archetypes_base import *
allflows = []
processunits = []

flow_dataframe = pd.DataFrame(columns=['name', 'components', 'flow_type',
                                       'temperature', 'pressure',
                                       'composition', 'origin', 'destination',
                                       'mass_flow_rate','elec_flow_rate',
                                       'heat_flow_rate','combustion_energy_content'])




            
MyFlow = Flow(name = 'Logs', components = ['Dry wood', 'Dry bark', 'Water'], flow_type = 'Input flow',
             temperature=25, pressure = 1, composition = [0.35, 0.05, 0.6], origin = None, 
             destination = None, mass_flow_rate = 1000, elec_flow_rate = 0, 
             heat_flow_rate = 0, combustion_energy_content = 0,  is_calc_flow = True, is_shear_stream = False)

MyFlow.attributes['mass_flow_rate']


MyUnit = Unit('MyUnit')
MyUnit.expected_flows_in = ['Logs', 'Electricity (from Debarker)']
MyUnit.expected_flows_out = ['Bark', 'Debarked logs']
MyUnit.coefficients = {'Power per t log' : 8}

def Debarkfunc_logs(log_flow, coefficients):
    log_amount = log_flow.attributes['mass_flow_rate']
    electricity_amount = coefficients['Power per t log'] * log_amount/1000.
    bark_index = log_flow.attributes['components'].index('Dry bark')
    wood_index = log_flow.attributes['components'].index('Dry wood')
    moisture_index = log_flow.attributes['components'].index('Water')
    bark_ratio = log_flow.attributes['composition'][bark_index]
    wood_ratio = log_flow.attributes['composition'][wood_index]
    moisture_ratio = log_flow.attributes['composition'][moisture_index]
    dry_bark_ratio = bark_ratio/(bark_ratio + wood_ratio)
    dry_wood_ratio = wood_ratio/(bark_ratio + wood_ratio)
    wood_flow_amount = dry_wood_ratio * log_amount
    bark_flow_amount = dry_bark_ratio * log_amount
    return [{'name' : 'Electricity (debarker)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_amount, 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Bark', 'components' : ['Dry bark', 'Water'], 'composition': [1-moisture_ratio, moisture_ratio], 'mass_flow_rate' : bark_flow_amount,
                     'flow_type': 'Process stream', 'temperature' : 25, 'pressure':1 , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'name' : 'Debarked logs', 'components' : ['Dry wood', 'Water'], 'composition' : [1-moisture_ratio, moisture_ratio] , 'mass_flow_rate' : wood_flow_amount,
                     'flow_type': 'Process stream', 'temperature' : 25, 'pressure':1 , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False}]

MyUnit.calculations = {'Logs' : Debarkfunc_logs}



processunits.append(MyUnit)
allflows.append(MyFlow)

main(allflows, processunits, f_print = True)
