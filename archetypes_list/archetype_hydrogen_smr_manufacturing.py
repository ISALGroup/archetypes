'''
Name: Aidan ONeil 
Date: August 25th, 2025 

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
C_pch4 = 1.
air_in = mass_in * 15
furance_temp = 800
C_ph2 = 14.3
C_pco2 = 0.826
C_psteam = 2.03
kg_product = (5270/10000) * mass_in

############################################################################ UNITS ###########################################################################
# Unit 1: Desulfurizer 
Unit1 = Unit('Desulfurizer')
Unit1.temperature = ambient_t
Unit1.unit_type = 'Seperator'
Unit1.expected_flows_in = ['Feed Natural Gas']
Unit1.expected_flows_out = ['Sulfur', 'Process Flow 1']
Unit1.coefficients = {'Sulfur wt': 0.0001}

def Desulfurization_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    sulfur_out = feed_in * coeff['Sulfur wt']
    feed_out = feed_in - sulfur_out 
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 1')
    return[{'name' : 'Process Flow 1', 'components' : ['Natural Gas'], 'composition' : [1], 'mass_flow_rate' : feed_out,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'Sulfur', 'components' : ['Sulfur'], 'composition' : [1], 'mass_flow_rate' : sulfur_out,
           'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit1.calculations = {'Feed Natural Gas': Desulfurization_func}
FlowA = Flow(name = 'Feed Natural Gas', components = ['Natural Gas'], composition = [1] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Heat Exchanger 
Unit2 = Unit('Heat Exchanger')
Unit2.temperature = 500 
Unit2.unit_type = ''
Unit2.expected_flows_in = ['Process Flow 1', 'Hot Stack']
Unit2.expected_flows_out = ['Process Flow 2', 'Stack Out ']
Unit2.coefficients = {'Unit Temp': 500, 'Exhaust Temp In': furance_temp} 

def Heat_exchanger_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_stack_in = air_in * C_pair * (furance_temp - ambient_t)
    stack_in = air_in
    Q_out = feed_in * C_pch4 * (coeff['Unit Temp'] - ambient_t)
    Q_stack_out = Q_stack_in + Q_in - Q_out 
    exhaust_temp = (Q_stack_out / (C_pair * stack_in)) + ambient_t
    print(exhaust_temp)
    print('Unit 2')
    return[{'name' : 'Process Flow 2', 'components' : ['Natural Gas'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'name' : 'Hot Stack', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : stack_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Exhaust Temp In'], 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': Q_stack_in}, 
             {'name' : 'Stack Out', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : stack_in,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': exhaust_temp, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_stack_out}]
Unit2.calculations = {'Process Flow 1': Heat_exchanger_func}

# Unit 3: Furance - Is there a way to link this to our arhetype framework, where we are demonstrating if something is ratio or equation based 
Unit3 = Unit('Furance')
Unit3.temperature = furance_temp 
Unit3.unit_type = ''
Unit3.expected_flows_in = ['Process Flow 2', 'Steam (Furance)', 'Fuel (Furance)', 'Air (Furance)']
Unit3.expected_flows_out = ['Process Flow 3', 'Hot Stack', 'Spent Fuel (Furance)']
Unit3.coefficients = {'Unit Temp': furance_temp, 'Steam Temp': 810, 'loses': 0.10, 'Fuel Demand (kJ/kg)': 61538, 'Steam Demand (kJ/kg)': 11538, 'Fuel HHV': 5200} 

def Furance_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = kg_product * coeff['Steam Demand (kJ/kg)']
    m_steam = Q_steam / Hvap 
    m_air = air_in 
    Q_air_out = m_air * C_pair * (coeff['Unit Temp'] - ambient_t)
    Q_fuel = mass_in * coeff['Fuel Demand (kJ/kg)']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    Q_loss = Q_fuel * coeff['loses']
    Q_out = (Q_steam + Q_in + Q_fuel - Q_air_out - Q_loss)
    # Component Adjustment 
    feed_out = feed_in + m_steam 
    h2_wt = .176 
    co_wt = 1- h2_wt
    print('Unit 3')
    return[{'name' : 'Process Flow 3', 'components' : ['H2', 'CO'], 'composition' : [h2_wt, co_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Hot Stack', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_air,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': furance_temp, 'In or out' : 'Out', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': Q_air_out},
           {'name' : 'Steam (Furance)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Air (Furance)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_air,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 0},
           {'name' : 'Fuel (Furance)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Spent Fuel (Furance)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0, 'combustion_energy_content': 0},
           {'Heat loss': Q_loss}]
Unit3.calculations = {'Process Flow 2': Furance_func}

# Unit 4: Steam Injection Cooling - (how is this cooling is the heat transfering from the feed to the steam)
Unit4 = Unit('Steam Injection Cooling')
Unit4.temperature = 400 # calculate a temperature
Unit4.unit_type = 'Mixer'
Unit4.expected_flows_in = ['Steam (Steam Injection)', 'Process Flow 3']
Unit4.expected_flows_out = ['Process Flow 4']
Unit4.coefficients = {'Steam Demand (kj/kg)': 30769, 'Steam Temp': 100, 'Unit Temp': 400}

def Steam_injection_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = coeff['Steam Demand (kj/kg)'] * kg_product
    Q_out = Q_steam + Q_in 
    m_steam = Q_steam / Hvap 
    feed_out = feed_in + m_steam 
    water_wt = m_steam / feed_out 
    co_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('CO')])
    co_wt = co_in / feed_out 
    h2_wt = 1 - co_wt - water_wt 
    print('Unit 4')
    return[{'name' : 'Steam (Steam Injection)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam}, 
             {'name' : 'Process Flow 4', 'components' : ['H2', 'CO', 'H20'], 'composition' : [h2_wt, co_wt, water_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Process Flow 3': Steam_injection_func}

# Unit 5: CO Converter - Update 
Unit5 = Unit('CO Converter')
Unit5.temperature = 400 # calculate 
Unit5.unit_type = 'Seperator'
Unit5.expected_flows_in = ['Steam (CO Converter)', 'Process Flow 4']
Unit5.expected_flows_out = ['Process Flow 5']
Unit5.coefficients = {'Steam Demand (kj/kg)': 3076, 'Steam Temp': 100, 'Unit Temp': 400}

def CO_converter_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = kg_product * coeff['Steam Demand (kj/kg)']
    m_steam = Q_steam / Hvap 
    feed_out = feed_in + m_steam
    co_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('CO')])
    water_in = (feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('H20')])) + m_steam
    water_wt = water_in / feed_out
    co_wt = co_in / feed_out 
    h2_wt = 1 - co_wt - water_wt 
    Q_out = Q_steam + Q_in 
    print('Unit 5')
    return[{'name' : 'Steam (CO Converter)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Process Flow 5', 'components' : ['H2', 'CO', 'H20'], 'composition' : [h2_wt, co_wt, water_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit5.calculations = {'Process Flow 4': CO_converter_func}

# Unit 6: Cooler 
Unit6 = Unit('Cooler')
Unit6.temperature = 40 
Unit6.unit_type = 'Seperator'
Unit6.expected_flows_in = ['Process Flow 5']
Unit6.expected_flows_out = ['Condensate (Cooler)', 'Process Stream 6']
Unit6.coefficients = {'Unit Temp': 40}

def Cooler_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_out = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('H20')])
    feed_out = feed_in - water_out
    h2_wt = .176 
    co2_wt = 1 - h2_wt
    C_p = (h2_wt * C_ph2) + (co2_wt * C_pco2)
    Q_out = feed_out * C_p * (coeff['Unit Temp'] - ambient_t)
    Q_loss = Q_in - Q_out
    print('Unit 6')
    return[{'name' : 'Process Flow 6', 'components' : ['H2', 'CO2'], 'composition' : [h2_wt, co2_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'name' : 'Condensate (Cooler)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_out,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'Heat loss': Q_loss}]
Unit6.calculations = {'Process Flow 5': Cooler_func}

# Unit 7: CO2 Absorber - Need more accurate unit temperatures, what is doing the seperating here
Unit7 = Unit('CO2 Absorber')
Unit7.temperature = 200
Unit7.unit_type = 'Seperator'
Unit7.expected_flows_in = ['Process Flow 6']
Unit7.expected_flows_out = ['Product CO2', 'Low Pressure Hydrogen']
Unit7.coefficients = {'Unit Temp': 200} 

def CO2_absorber_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    co2_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('CO2')])
    feed_out = feed_in - co2_in 
    Q_loss = Q_in 
    print('Unit 7')
    return[{'name' : 'Product CO2', 'components' : ['CO2'], 'composition' : [1], 'mass_flow_rate' : co2_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Low Pressure Hydrogen', 'components' : ['H2'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
             {'Heat loss': Q_loss}]
Unit7.calculations = {'Process Flow 6': CO2_absorber_func}

# Unit 8: Compressor 
Unit8 = Unit('Compressor')
Unit8.temperature = ambient_t 
Unit8.unit_type = ''
Unit8.expected_flows_in = ['Low Pressure Hydrogen', 'Electricity (Compressor)']
Unit8.expected_flows_out = ['Product Hydrogen']
Unit8.coefficients = {'P out': 20, 'Electricity (kw/kg)': 384}

def Compressor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = mass_in * coeff['Electricity (kw/kg)']
    print('Unit9')
    return[{'name' : 'Electricity (Compressor)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'name' : 'Product Hydrogen', 'components' : ['H2'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'pressure': coeff['P out'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Low Pressure Hydrogen': Compressor_func}

################################################################################################################################################

processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_hydrogen_smr_6', allflows, processunits)
