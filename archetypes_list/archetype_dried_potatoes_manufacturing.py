'''
Name: Aidan J ONeil 
Date: 8/26/205 


'''

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
# Global Variables
ambient_t = 20
Hvap = 2260
C_pw = 4.186
C_pair = 1.000
mass_in = 10000
C_ppotatoe = 3.8

################################################################################## UNITS ###############################################################
# Unit 1: Washer
Unit1 = Unit('Washer')
Unit1.temperature = ambient_t 
Unit1.unit_type = ''
Unit1.expected_flows_in = ['Water (Washer)', 'Feed Potatoes']
Unit1.expected_flows_out = ['Wastewater (Washer)', 'Clean Potatoes']
Unit1.coefficients = {'Water Amount': .65} 

def Washer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    water_in = potatoes_in * coeff['Water Amount']
    print('Unit 1')
    return[{'name' : 'Water (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Wastewater (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Clean Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit1.calculations = {'Feed Potatoes': Washer_func}
FlowA = Flow(name = 'Feed Potatoes', components = ['Potatoes'], composition = [1] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Steam Preheater
Unit2 = Unit('Steam Preheater')
Unit2.temperature = ambient_t 
Unit2.unit_type = 'Seperator'
Unit2.expected_flows_in = ['Clean Potatoes', 'Steam (Steam Preheater)']
Unit2.expected_flows_out = ['Peeled Potatoes', 'Condensate (Steam Preheater)', 'Peels']
Unit2.coefficients = {'Peel wt': .07314, 'Unit Temp': 100, 'Steam Temp': 100, 'loses': .10, 'Potatoe temp raise': 5}

def Steam_preheater_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    peels_in = potatoes_in * coeff['Peel wt']
    potatoes_out = potatoes_in - peels_in
    Q_peels = peels_in * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_potatoes = potatoes_out * C_ppotatoe * coeff['Potatoe temp raise']
    Q_steam = (Q_peels + Q_potatoes) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 2')
    return[{'name' : 'Peeled Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t+ coeff['Potatoe temp raise'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_potatoes},
            {'name' : 'Peels', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : peels_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_peels}, 
             {'name' : 'Steam (Steam Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Steam Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}]
Unit2.calculations = {'Clean Potatoes': Steam_preheater_func}

# Unit 3: Scrubber
Unit3 = Unit('Scrubber')
Unit3.temperature = ambient_t 
Unit3.unit_type = ''
Unit3.expected_flows_in = ['Water (Scrubber)', 'Peeled Potatoes']
Unit3.expected_flows_out = ['Wastewater (Scrubber)', 'Scrubbed Potatoes']
Unit3.coefficients = {'Water Amount': (1/9.26)} 

def Scrubber_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    water_in = potatoes_in * coeff['Water Amount']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 3')
    return[{'name' : 'Water (Scrubber)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Wastewater (Scrubber)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Scrubbed Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
             {'Heat loss': Q_in}]
Unit3.calculations = {'Peeled Potatoes': Scrubber_func}

# Unit 4: Slicer
Unit4 = Unit('Slicer')
Unit4.temperature = ambient_t
Unit4.unit_type = ''
Unit4.expected_flows_in = ['Scrubbed Potatoes']
Unit4.expected_flows_out = ['Sliced Potatoes']
Unit4.coefficients = {}

def Slicer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 4')
    return[{'name' : 'Sliced Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit4.calculations = {'Scrubbed Potatoes': Slicer_func}

# Unit 5: Precooker
Unit5 = Unit('Precooker')
Unit5.temperature = 70 
Unit5.unit_type = ''
Unit5.expected_flows_in = ['Hot Water (Precooker)', 'Sliced Potatoes']
Unit5.expected_flows_out = ['Water (Precooker)', 'Blanched Potatoes']
Unit5.coefficients = {'Unit Temp':70, 'Hot Water temp': 80, 'loses': 0.10}

def Precooker_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_out = potatoes_in * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_hw = (Q_out - Q_in) / (1-coeff['loses'])
    m_hw = Q_hw / (C_pw * (coeff['Hot Water temp'] - ambient_t))
    Q_loss = Q_hw * coeff['loses']
    print('Unit 5')
    return[{'name' : 'Hot Water (Precooker)', 'components' : 'Water', 'mass_flow_rate' : m_hw,
             'flow_type': 'Steam', 'Temperature': coeff['Hot Water temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_hw},
             {'name' : 'Water (Precooker)', 'components' : 'Water', 'mass_flow_rate' : m_hw,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Blanched Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit5.calculations = {'Sliced Potatoes': Precooker_func}

# Unit 6: Cooler
Unit6 = Unit('Cooler')
Unit6.temperature = 25
Unit6.unit_type = ''
Unit6.expected_flows_in = ['Chilling (Cooler)', 'Blanched Potatoes']
Unit6.expected_flows_out = ['Cooled Potatoes']
Unit6.coefficients = {'Unit Temp': 25}

def Cooler_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_out = potatoes_in * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 6')
    return[{'name' : 'Cooled Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'name' : 'Chilling (Cooler)', 'components' : None, 'composition' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit6.calculations = {'Blanched Potatoes': Cooler_func}

# Unit 7: Cooker
Unit7 = Unit('Cooker')
Unit7.temperature = 75 
Unit7.unit_type = ''
Unit7.expected_flows_in = ['Cooled Potatoes', 'Steam (Cooker)']
Unit7.expected_flows_out = ['Potatoes to Ricer', 'Potatoes to Mixer', 'Condensate (Cooker)']
Unit7.coefficients = {'Unit Temp': 75, 'Steam Temp': 100, 'loses': 0.10, 'Ricer Split': .5}

def Cooker_func(potatoe_flow, coeff): 
    potatoe_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_out = potatoe_in * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    potatoe_to_ricer = potatoe_in * coeff['Ricer Split']
    Q_ricer = Q_out * coeff['Ricer Split']
    potatoe_to_mixer = potatoe_in - potatoe_to_ricer
    Q_mixer = Q_out - Q_ricer
    print('unit 7')
    return[{'name' : 'Steam (Cooker)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Cooker)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Potatoes to Ricer', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoe_to_ricer,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_ricer}, 
             {'name' : 'Potatoes to Mixer', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoe_to_mixer,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_mixer}]
Unit7.calculations = {'Cooled Potatoes': Cooker_func}

# Unit 8: Ricer
Unit8 = Unit('Ricer')
Unit8.temperature = Unit7.temperature
Unit8.unit_type = ''
Unit8.expected_flows_in = ['Potatoes to Ricer']
Unit8.expected_flows_out = ['Riced Potatoes']
Unit8.coefficients = {} 

def Ricer_func(potatoe_flow, coeff): 
    potatoe_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 8')
    return[{'name' : 'Riced Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoe_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': Unit7.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit8.calculations = {'Potatoes to Ricer': Ricer_func}

# Unit 9: Drum Dryer - 
Unit9 = Unit('Drum Dryer')
Unit9.temperature = 100
Unit9.unit_type = ''
Unit9.expected_flows_in = ['Riced Potatoes', 'Steam (Drum Dryer)']
Unit9.expected_flows_out = ['Dry Riced Potatoes', 'Condensate (Drum Dryer)', 'Exhaust (Drum Dryer)']
Unit9.coefficients = {'Inlet water wt': .78, 'Outlet water wt': 0.08, 'Unit Temp': 100, 'loses': 0.10, 'Steam Temp': 110} 

def Drum_dryer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    water_in = potatoes_in * coeff['Inlet water wt']
    solids_in = potatoes_in - water_in 
    potatoes_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = potatoes_in - potatoes_out
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_water_evap = (water_evap * Hvap) + (water_evap * C_pw * (100 - ambient_t))
    Q_solids = potatoes_out * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_solids - Q_in ) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap 
    Q_loss = Q_steam * coeff['loses']
    print('Unit 9')
    return[{'name' : 'Steam (Drum Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Drum Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Dry Riced Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_solids}, 
             {'name' : 'Exhaust (Drum Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap}]
Unit9.calculations = {'Riced Potatoes': Drum_dryer_func}

# Unit 10: Grinding and Milling
Unit10 = Unit('Grinding and Milling')
Unit10.unit_type = ''
Unit10.expected_flows_in = ['Dry Riced Potatoes', 'Electricity (Grinding)']
Unit10.expected_flows_out = ['Potatoe Flakes']
Unit10.coefficients = {'Electricity (kw/kg)': 0.1}

def Miller_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate'] 
    electricity_in = potatoes_in * coeff['Electricity (kw/kg)']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 10')
    return[{'name' : 'Electricity (Grinding)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'name' : 'Potatoe Flakes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in}]
Unit10.calculations = {'Dry Riced Potatoes': Miller_func}

# Unit 12: Mixer
Unit12 = Unit('Mixer')
Unit12.temperature = Unit7.temperature
Unit12.unit_type = 'Mixer'
Unit12.expected_flows_in = ['Potatoes to Mixer']
Unit12.expected_flows_out = ['Mixed Potatoe']
Unit12.coefficients = {}

def Mixer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 12')
    return[{'name' : 'Mixed Potatoe', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_in,
             'flow_type': 'Product Stream', 'elec_flow_rate' : 0, 'temperature': Unit7.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit12.calculations = {'Potatoes to Mixer': Mixer_func}

# Unit 13: Conditioner
Unit13 = Unit('Conditioner')
Unit13.temperature = Unit12.temperature 
Unit13.unit_type = ''
Unit13.expected_flows_in = ['Mixed Potatoe', 'Electricity (Conditioner)']
Unit13.expected_flows_out = ['Conditioned Potatoes']
Unit13.coefficients = {'Electricity (kw/kg)': .003}

def Conditioner_func(potatoe_flow, coeff): 
    potatoe_in = potatoe_flow.attributes['mass_flow_rate']
    electricity_in = potatoe_in * coeff['Electricity (kw/kg)']
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    print('Unit 13')
    return[{'name' : 'Conditioned Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoe_in,
             'flow_type': 'Product Stream', 'elec_flow_rate' : 0, 'temperature': Unit12.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}, 
             {'name' : 'Electricity (Conditioner)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}]
Unit13.calculations = {'Mixed Potatoe': Conditioner_func}

# Unit 14: Pre-Dryer
Unit14 = Unit('Pre-Dryer')
Unit14.temperature = 100
Unit14.unit_type = ''
Unit14.expected_flows_in = ['Conditioned Potatoes', 'Steam (Pre Dryer)']
Unit14.expected_flows_out = ['Dry Granule Potatoes', 'Condensate (Pre Dryer)', 'Exhaust (Pre Dryer)']
Unit14.coefficients = {'Inlet water wt': .78, 'Outlet water wt': 0.20, 'Unit Temp': 100, 'loses': 0.10, 'Steam Temp': 110} 

def Pre_dryer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    water_in = potatoes_in * coeff['Inlet water wt']
    solids_in = potatoes_in - water_in 
    potatoes_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = potatoes_in - potatoes_out
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_water_evap = (water_evap * Hvap) + (water_evap * C_pw * (100 - ambient_t))
    Q_solids = potatoes_out * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_solids - Q_in ) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap 
    Q_loss = Q_steam * coeff['loses']
    print('Unit 14')
    return[{'name' : 'Steam (Pre Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Pre Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Dry Granule Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_solids}, 
             {'name' : 'Exhaust (Pre Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap}]
Unit14.calculations = {'Conditioned Potatoes': Pre_dryer_func}

# Unit 15: Sifter
Unit15 = Unit('Sifter')
Unit15.temperature = Unit14.temperature
Unit15.unit_type = ''
Unit15.expected_flows_in = ['Dry Granule Potatoes']
Unit15.expected_flows_out = ['Sifted Potatoes']
Unit15.coefficients = {}

def Sifter_func(potatoe_flow, coeff): 
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    potatoe_in = potatoe_flow.attributes['mass_flow_rate']
    print('Unit 15')
    return[{'name' : 'Sifted Potatoes', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoe_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': Unit14.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit15.calculations = {'Dry Granule Potatoes': Sifter_func}

# Unit 16: Dryer
Unit16 = Unit('Dryer')
Unit16.temperature = 100 
Unit16.unit_type = ''
Unit16.expected_flows_in = ['Sifted Potatoes', 'Steam (Dryer)']
Unit16.expected_flows_out = ['Product Granules', 'Condensate (Dryer)', 'Exhaust (Dryer)']
Unit16.coefficients = {'Inlet water wt': .20, 'Outlet water wt': 0.09, 'Unit Temp': 100, 'loses': 0.10, 'Steam Temp': 110} 

def Dryer_func(potatoe_flow, coeff): 
    potatoes_in = potatoe_flow.attributes['mass_flow_rate']
    water_in = potatoes_in * coeff['Inlet water wt']
    solids_in = potatoes_in - water_in 
    potatoes_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = potatoes_in - potatoes_out
    Q_in = potatoe_flow.attributes['heat_flow_rate']
    Q_water_evap = (water_evap * Hvap) + (water_evap * C_pw * (100 - ambient_t))
    Q_solids = potatoes_out * C_ppotatoe * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_solids - Q_in ) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap 
    Q_loss = Q_steam * coeff['loses']
    print('Unit 16')
    return[{'name' : 'Steam (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Product Granules', 'components' : ['Potatoe'], 'composition' : [1], 'mass_flow_rate' : potatoes_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_solids}, 
             {'name' : 'Exhaust (Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap}]
Unit16.calculations = {'Sifted Potatoes': Dryer_func}

#####################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, 
                Unit10, Unit12, Unit13, Unit14, Unit15, Unit16]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
        print(flow)

#utilities_recap('heat_intensity_potatoes', allflows, processunits)

###################################################