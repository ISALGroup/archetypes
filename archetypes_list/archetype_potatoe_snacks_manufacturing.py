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
C_ppotatoes = 3.45
C_poil = 2.05 
C_ppotatoe_chips = 1.75
product_yield = (2143/7073)
product_out = product_yield * material_in

################################################################################ UNITS ################################################################################
# Unit 1: Prep  
Unit1 = Unit('Prep')
Unit1.temperature = ambient_t 
Unit1.unit_type = 'Mechanical Process'
Unit1.expected_flows_in = ['Fresh Feed', 'Hot Water (Prep)', 'Electricity (Prep)']
Unit1.expected_flows_out = ['Potatoe Slices', 'Wastewater (Prep)']
Unit1.coefficients = {'Electricity (kw/kg)': 0.01, 'Hot Water Demand (kJ/kg)': 950, 'Peel wt': .10, 'loses': 0.10, 'Hot Water temp': 60}

def Prep_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    peels_out = feed_in * coeff['Peel wt']
    feed_out = feed_in - peels_out 
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_hot_water = product_out * coeff['Hot Water Demand (kJ/kg)'] / (1-coeff['loses'])
    Q_loss = Q_hot_water * coeff['loses']
    Q_out = Q_hot_water + Q_in - Q_loss 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    water_in = Q_hot_water / (C_pw * (coeff['Hot Water temp'] - ambient_t))
    print('Unit 1')
    return[{'name' : 'Electricity (Prep)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Potatoe Slices', 'components' : ['Solids', 'Water'], 'composition' : [.20, .80], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'name' : 'Hot Water (Prep)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature': coeff['Hot Water temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_hot_water}, 
            {'name' : 'Wastewater (Prep)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in + peels_out,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'Heat loss': Q_loss}]
Unit1.calculations = {'Fresh Feed': Prep_func}

FlowA = Flow(name='Fresh Feed', components = ['Solids', 'Water'], composition = [.20, .80], flow_type = 'input', mass_flow_rate = material_in, heat_flow_rate=0)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Air Dryer
Unit2 = Unit('Air Dryer')
Unit2.temperature = 32
Unit2.unit_type = ''
Unit2.expected_flows_in = ['Potatoe Slices', 'Fuel (Air Dryer)', 'Electricity (Air Dryer)', 'Air (Air Dryer)']
Unit2.expected_flows_out = ['Chips', 'Exhaust (Air Dryer)']
Unit2.coefficients = {'Electricity (kw/kg)': 0.005, 'Fuel HHV': 5200, 'Unit Temp': Unit2.temperature, 'loses': .10, 
                      'Moisture lose': (3215/6430), 'Fuel Demand (kJ/kg)': 20, 'Air Rate': 2.00}

def Air_Dryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    moisture_loss = coeff['Moisture lose'] * feed_in
    feed_out = feed_in - moisture_loss
    air_in = feed_in * coeff['Air Rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_fuel = (coeff['Fuel Demand (kJ/kg)'] * product_out) / (1-coeff['loses'])
    Q_loss = Q_fuel * coeff['loses']
    Q_exhaust = air_in * C_pair * (coeff['Unit Temp'] - ambient_t)
    Q_out = Q_fuel + Q_in - Q_loss - Q_exhaust
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    print('Unit 2')
    return[{'name' : 'Fuel (Air Dryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel}, 
            {'name' : 'Exhaust (Air Dryer)', 'components' : ['Exhaust'], 'composition' : [1], 'mass_flow_rate' : m_fuel+moisture_loss+air_in,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_exhaust, 'combustion_energy_content': 0}, 
            {'name' : 'Air (Air Dryer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0, 'combustion_energy_content': 0},
            {'Heat loss': Q_loss}, 
            {'name' : 'Chips', 'components' : ['Solids', "Water"], 'composition' : [.40, .60], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Electricity (Air Dryer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Potatoe Slices': Air_Dryer_func}

# Unit 3: Fryer
Unit3 = Unit('Fryer')
Unit3.temperature = 180 
Unit3.unit_type = 'Splitter'
Unit3.expected_flows_in = ['Fuel (Fryer)', 'Oil', 'Chips', 'Electricity (Fryer)']
Unit3.expected_flows_out = ['Exhaust (Fryer)', 'Fried Chips']
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
            {'name' : 'Fried Chips', 'components' : ['Solids', 'Water', 'Oil'], 'composition' : [coeff['Solid wt out'], water_out_wt, coeff['Oil wt out']], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit3.calculations = {'Chips': Fryer_func}

# Unit 4: Finishing and Packaging 
Unit4 = Unit('Finishing and Packaging')
Unit4.temperature = ambient_t
Unit4.unit_type = 'Mechanical Process'
Unit4.expected_flows_in = ['Fried Chips', 'Electricity (Finishing)', 'Seasoning']
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
Unit4.calculations = {'Fried Chips': Finishing_func}

#######################################################################################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_potatoe_snacks', allflows, processunits)