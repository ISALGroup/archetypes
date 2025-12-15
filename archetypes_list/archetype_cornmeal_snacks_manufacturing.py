'''
Name: Aidan ONeil 
Date: September 22nd, 2025 


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

## Global variables
ambient_t = 20
material_in = 1000
C_pw = 4.186
Hvap = 2257
C_pair = 1.00 
C_pcorn_meal = 1.9
C_pfried_corn = 1.8 
C_pveg_oil = 2.05

################################################################################ UNITS ################################################################################
# Unit 1: Prep  
Unit1 = Unit('Batter Mixer')
Unit1.temperature = ambient_t 
Unit1.unit_type = 'Mechanical Process'
Unit1.expected_flows_in = ['Fresh Feed', 'Water (Batter Mixer)', 'Electricity (Batter Mixer)']
Unit1.expected_flows_out = ['Batter']
Unit1.coefficients = {'Electricity (kw/kg)': 0.01, 'Outlet water wt': .50}

def Batter_mixer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    solids_in = feed_in - water_in 
    feed_out = solids_in / (1- coeff['Outlet water wt'])
    water_in = feed_out - feed_in 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 1')
    return[{'name' : 'Electricity (Batter Mixer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Batter', 'components' : ['Solids', 'Water'], 'composition' : [1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
             {'name' : 'Water (Batter Mixer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit1.calculations = {'Fresh Feed': Batter_mixer_func}

FlowA = Flow(name='Fresh Feed', components = ['Solids', 'Water'], composition = [.88, .12], flow_type = 'input', mass_flow_rate = material_in, heat_flow_rate=0)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Extruder
Unit2 = Unit('Extruder')
Unit2.temperature = 120 
Unit2.unit_type = ''
Unit2.expected_flows_in = ['Batter', 'Steam (Extruder)', 'Electricity (Extruder)']
Unit2.expected_flows_out = ['Collets', 'Condensate (Extruder)', 'Waste (Extruder)']
Unit2.coefficients = {'Electricity (kw/kg)': 0.000, 'Steam Temp': (Unit2.temperature + 10), 'Unit Temp': Unit2.temperature, 'loses': .10, 
                      'Moisture lose': (917/3000)}

def Extruder_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    solids_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Solids')])
    moisture_loss = feed_in * coeff['Moisture lose']
    feed_out = feed_in - moisture_loss 
    solids_wt = solids_in / feed_out
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    C_P = (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')] * C_pw) + (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Solids')] * C_pcorn_meal)
    Q_out = feed_out * C_P * (coeff['Unit Temp'] - ambient_t)
    Q_water = moisture_loss * Hvap 
    Q_steam = (Q_out + Q_water - Q_in)/ (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 2')
    return[{'name' : 'Steam (Extruder)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Extruder)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Collets', 'components' : ['Solids', 'Water'], 'composition' : [solids_wt, 1-solids_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Waste (Extruder)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : moisture_loss,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water}, 
            {'name' : 'Electricity (Extruder)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Batter': Extruder_func}

# Unit 3: Fryer
Unit3 = Unit('Fryer')
Unit3.temperature = 180 
Unit3.unit_type = 'Splitter'
Unit3.expected_flows_in = ['Fuel (Fryer)', 'Oil', 'Collets', 'Electricity (Fryer)']
Unit3.expected_flows_out = ['Exhaust (Fryer)', 'Corn Chips']
Unit3.coefficients = {'Solid wt out': .60, 'Oil wt out': .38, 'Fuel HHV': 5200, 'Electricity (kw/kg)': 0.01, 'loses': 0.3, 
                      'Fuel Demand (kJ/kg)': 1700}
def Fryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_out_wt = 1- coeff['Solid wt out'] - coeff['Oil wt out']
    solids_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Solids')])
    feed_out = solids_in / coeff['Solid wt out']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    water_loss = water_in - (feed_out * water_out_wt)
    oil_in = feed_out * coeff['Oil wt out']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_fuel = feed_out * coeff['Fuel Demand (kJ/kg)'] 
    Q_loss = coeff['loses'] * Q_fuel
    Q_water = water_loss * Hvap 
    Q_out = Q_fuel + Q_in - Q_loss - Q_water
    m_fuel = Q_fuel / coeff['Fuel HHV']
    electricity_in = feed_out * coeff['Electricity (kw/kg)']
    print('Unit 3')
    return[{'name' : 'Fuel (Fryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel}, 
            {'name' : 'Exhaust (Fryer)', 'components' : ['Exhaust'], 'composition' : [1], 'mass_flow_rate' : m_fuel+water_loss,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water, 'combustion_energy_content': 0}, 
            {'Heat loss': Q_loss}, 
            {'name' : 'Electricity (Fryer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Corn Chips', 'components' : ['Solids', 'Water', 'Oil'], 'composition' : [coeff['Solid wt out'], water_out_wt, coeff['Oil wt out']], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit3.calculations = {'Collets': Fryer_func}

# Unit 4: Finishing and Packaging 
Unit4 = Unit('Finishing and Packaging')
Unit4.temperature = ambient_t
Unit4.unit_type = 'Mechanical Process'
Unit4.expected_flows_in = ['Corn Chips', 'Electricity (Finishing)', 'Seasoning']
Unit4.expected_flows_out = ['Product']
Unit4.coefficients = {'Electricity (kw/kg)': 0.019, 'Seasoning rate': 0.00}

def Finishing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    seasoning_in = coeff['Seasoning rate'] * feed_in
    feed_out = feed_in + seasoning_in 
    electricity_in = coeff['Electricity (kw/kg)'] * feed_in 
    Q_loss = feed_flow.attributes['heat_flow_rate']
    print('Unit 4')
    return[{'name' : 'Product', 'components' : ['Product'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}, 
            {'name' : 'Electricity (Finishing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Seasoning', 'components' : ['Seasoning'], 'composition' : [1], 'mass_flow_rate' : seasoning_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit4.calculations = {'Corn Chips': Finishing_func}

#######################################################################################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_corn_cnakcs', allflows, processunits)