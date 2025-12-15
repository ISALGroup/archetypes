'''
Name: Aidan J ONeil 
Date: 9/15/2025

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
grain_input = 1000
C_pw = 4.21
Hvap = 2260
C_psolids = 1.6
C_pair = 1.00

######################################################################### UNITS ################################################################
# Unit 1: Grain Cleaning 
Unit1 = Unit('Grain Cleaning')
Unit1.temperature = ambient_t
Unit1.unit_type = '' 
Unit1.expected_flows_in = ['Feed Grain', 'Electricity (Cleaning)', 'Compressed Air (Cleaning)']
Unit1.expected_flows_out = ['Waste Grain', 'Grain to Miller']
Unit1.coefficients = {'Electricity (kw/kg)': 0.000, 'Compressed Air Ratio': 0.000, 'Waste Rate': .03}

def Cleaning_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = feed_in * coeff['Waste Rate']
    feed_out = feed_in - waste_out
    electricity_in = coeff['Electricity (kw/kg)'] * feed_in 
    print('Unit 1')
    return[{'name' : 'Electricity (Cleaning)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Waste Grain', 'components' : ['Grain'], 'composition' :[1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Grain to Miller', 'components' : ['Grain'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Compressed Air (Cleaning)', 'components' : ['Air'], 'composition' :[1], 'mass_flow_rate' : 0,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit1.calculations = {'Feed Grain': Cleaning_func}
FlowA = Flow(name = 'Feed Grain', components = ['Grain'], composition = [1], flow_type = 'input', mass_flow_rate = grain_input)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Miller 
Unit2 = Unit('Miller')
Unit2.temperature = ambient_t 
Unit2.unit_type = 'Mechanical Process'
Unit2.expected_flows_in = ['Grain to Miller', 'Electricity (Miller)']
Unit2.expected_flows_out = ['Grain to Mixer', 'Bran/Husk']
Unit2.coefficients = {'Electricity (kw/kg)': 0.00, 'Waste Rate': 0.02}

def Miller_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = coeff['Waste Rate'] * feed_in 
    feed_out = feed_in - waste_out 
    electricity_in = coeff['Electricity (kw/kg)'] * feed_in 
    print('Unit 2')
    return[{'name' : 'Electricity (Miller)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Bran/Husk', 'components' : ['Grain'], 'composition' :[1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Grain to Mixer', 'components' : ['Grain'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit2.calculations = {'Grain to Miller': Miller_func}

# Unit 3: Mixer 
Unit3 = Unit('Mixer')
Unit3.temperature = 75
Unit3.unit_type = 'Mixer'
Unit3.expected_flows_in = ['Grain to Mixer', 'Steam (Mixer)', 'Syrup']
Unit3.expected_flows_out = ['Grain to Cooker', 'Condensate (Mixer)']
Unit3.coefficients = {'Unit Temp': Unit3.temperature, 'Steam Temp': 100, 'loses': 0.05, 'Syrup Ratio': (1200/9506), 'Syrup water wt%': .30, 'Grain water wt%': .12}

def Mixer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    syrup_in = feed_in * coeff['Syrup Ratio']
    feed_out = feed_in + syrup_in 
    water_in = (syrup_in * coeff['Syrup water wt%']) + (feed_in * coeff['Grain water wt%'])
    solids_in = feed_out - water_in 
    solids_wt = solids_in / feed_out 
    Q_out = (water_in * C_pw * (coeff['Unit Temp'] - ambient_t)) + (solids_in * C_psolids * (coeff['Unit Temp'] - ambient_t))
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 3')
    return[{'name' : 'Steam (Mixer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Mixer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Syrup', 'components' : ['Solids', 'Water'], 'composition' :[1-coeff['Syrup water wt%'], coeff['Syrup water wt%']], 'mass_flow_rate' : syrup_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Grain to Cooker', 'components' : ['Solids', 'Water'], 'composition' :[solids_wt, 1-solids_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit3.calculations = {'Grain to Mixer': Mixer_func}
    
# Unit 4: Cooker 
Unit4 = Unit('Cooker')
Unit4.temperature = 120
Unit4.unit_type = ''
Unit4.expected_flows_in = ['Steam (Cooker)', 'Grain to Cooker']
Unit4.expected_flows_out = ['Cooked Grain']
Unit4.coefficients = {'Steam Temp': (Unit4.temperature + 10), 'Unit Temp': Unit4.temperature}

def Cooker_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Solids')]) * C_psolids * (coeff['Unit Temp'] - ambient_t)
    Q_out = Q_in + Q_steam 
    m_steam = Q_steam / Hvap 
    water_out = m_steam + (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')]) 
    water_wt = water_out / (feed_in + m_steam)
    print('Unit 4')
    return[{'name' : 'Steam (Cooker)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam}, 
            {'name' : 'Cooked Grain', 'components' : ['Solids', 'Water'], 'composition' :[1-water_wt, water_wt], 'mass_flow_rate' : m_steam + feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Grain to Cooker': Cooker_func}

# Unit 5: Delumper 
Unit5 = Unit('Delumper')
Unit5.temperature = 95
Unit5.unit_type = 'Mechanical Process'
Unit5.expected_flows_in = ['Cooked Grain', 'Electricity (Delumper)']
Unit5.expected_flows_out = ['Delumped Grain']
Unit5.coefficients = {'Unit Temp': Unit5.temperature, 'Electricity (kw/kg)': 0.000}

def Delumper_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_wt = (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    C_pflow = (C_pw * water_wt) + (C_psolids * (1-water_wt))
    Q_out = C_pflow * feed_in * (coeff['Unit Temp'] - ambient_t)
    Q_loss = Q_in - Q_out 
    electricity_in = coeff['Electricity (kw/kg)'] * feed_in 
    print('Unit 5')
    return[{'name' : 'Electricity (Delumper)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Delumped Grain', 'components' : ['Solids', 'Water'], 'composition' :[1-water_wt, water_wt], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'Heat loss': Q_loss}]
Unit5.calculations = {'Cooked Grain': Delumper_func}

# Unit 6: Dryer 
Unit6 = Unit('Dryer')
Unit6.temperature = 100 
Unit6.unit_type = 'Seperator'
Unit6.expected_flows_in = ['Delumped Grain', 'Fuel (Dryer)', 'Air (Dryer)']
Unit6.expected_flows_out = ['Dry Grain', 'Exhaust (Dryer)']
Unit6.coefficients = {'Outlet water wt': 0.05, 'Fuel HHV': 5200, 'Air Ratio': 3.00, 'loses': 0.10, 'Exhaust percentage': 0.25, 
                      'Unit Temp': Unit6.temperature} 

def Dryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    m_air = coeff['Air Ratio'] * feed_in
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_in = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    solids_in = feed_in - water_in
    feed_out = (solids_in / (1-coeff['Outlet water wt']))
    water_evap = feed_in - feed_out 
    Q_water_evap = water_evap * Hvap 
    Q_solids = feed_out * C_psolids * (coeff['Unit Temp'] - ambient_t)
    Q_air = (feed_in * coeff['Air Ratio'] * coeff['Exhaust percentage']) * C_pair * (coeff['Unit Temp'] - ambient_t)
    Q_fuel = (Q_water_evap + Q_solids + Q_air - Q_in) / (1- coeff['loses'])
    Q_loss = Q_fuel * coeff['loses']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    print('Unit 6')
    return[{'name' : 'Air (Dryer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_air,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 0},
           {'name' : 'Fuel (Dryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Exhaust (Dryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel + m_air + water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap+Q_air, 'temperature': (Unit6.temperature + 10)},
           {'Heat loss': Q_loss}, 
           {'name' : 'Dry Grain', 'components' : ['Solids', 'Water'], 'composition' :[1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_solids}]
Unit6.calculations = {'Delumped Grain': Dryer_func}

# Unit 7: Cooler 
Unit7 = Unit('Cooler')
Unit7.temperature = ambient_t 
Unit7.unit_type = ' '
Unit7.expected_flows_in = ['Dry Grain']
Unit7.expected_flows_out = ['Cereal']
Unit7.coefficients = {}

def Cooler_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 7')
    return[{'name' : 'Cereal', 'components' : ['Cereal'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_in}]
Unit7.calculations = {'Dry Grain': Cooler_func}

# Unit 8: Flaker 
Unit8 = Unit('Flaker')
Unit8.temperature = ambient_t
Unit8.unit_type = 'Mechanical Process'
Unit8.expected_flows_in = ['Cereal', 'Electricity (Flaker)']
Unit8.expected_flows_out = ['Flakes']
Unit8.coefficients = {'Electricity (kw/kg)': 0.000}

def Flaker_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 8')
    return[{'name' : 'Flakes', 'components' : ['Cereal'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Electricity (Flaker)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Cereal': Flaker_func}

# Unit 9: Toaster 
Unit9 = Unit('Toaster')
Unit9.temperature = 105
Unit9.unit_type = 'Seperator'
Unit9.expected_flows_in = ['Flakes', 'Steam (Toaster)']
Unit9.expected_flows_out = ['Toasted Flakes', 'Condensate (Toaster)', 'Exhaust (Toaster)']
Unit9.coefficients = {'Inlet water wt': 0.05, 'Outlet water wt': 0.025, 'Steam Temp': (Unit9.temperature + 10), 'Unit Temp': Unit9.temperature, 
                      'loses':0.05}

def Toaster_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    solids_in = (1- coeff['Inlet water wt']) * feed_in 
    feed_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = feed_in - feed_out 
    Q_water_evap = water_evap * Hvap 
    Q_solids = feed_out * C_psolids * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_solids - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 9')
    return[{'name' : 'Steam (Toaster)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Toaster)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Toasted Flakes', 'components' : ['Cereal'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_solids}, 
            {'name' : 'Exhaust (Toaster)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Wasteheat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap}]
Unit9.calculations = {'Flakes': Toaster_func}

# Unit 10: Coating 
Unit10 = Unit('Coating')
Unit10.temperature = 80 
Unit10.unit_type = 'Mixer'
Unit10.expected_flows_in = ['Toasted Flakes', 'Steam (Coating)', 'Coating Syrup']
Unit10.expected_flows_out = ['Hot Cereal', 'Condensate (Coating)']
Unit10.coefficients = {'Steam Temp': 100, 'Unit Temp': Unit10.temperature, 'loses': .10, 'Syrup ratio': 0.05}

def Coating_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    syrup_in = coeff['Syrup ratio'] * feed_in 
    feed_out = feed_in + syrup_in 
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_syrup = syrup_in * ((C_pw * .15) + (C_psolids * (1-.15))) * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_syrup) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap 
    Q_loss = Q_steam * coeff['loses']
    print('Unit 10')
    return[{'name' : 'Steam (Coating)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Coating)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Coating Syrup', 'components' : ['Syrup'], 'composition' :[1], 'mass_flow_rate' : syrup_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Hot Cereal', 'components' : ['Cereal'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in + Q_syrup}]
Unit10.calculations = {'Toasted Flakes': Coating_func}

# Unit 11: Cooler 2
Unit11 = Unit('Cooler 2')
Unit11.temperature = ambient_t 
Unit11.unit_type = ' '
Unit11.expected_flows_in = ['Hot Cereal']
Unit11.expected_flows_out = ['Product Cereal']
Unit11.coefficients = {}

def Cooler_two_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 11')
    return[{'name' : 'Product Cereal', 'components' : ['Cereal'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_in}]
Unit11.calculations = {'Hot Cereal': Cooler_two_func}

###############################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8,
                Unit9, Unit10, Unit11]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

#utilities_recap('heat_intensity_cereal_manufacturing', allflows, processunits)

for flow in allflows:
    print(flow)
