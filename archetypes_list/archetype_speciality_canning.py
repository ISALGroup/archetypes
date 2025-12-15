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
material_input = 1000
C_pw = 4.21
Hvap = 2260
material_yield = (806/1000)
material_out = material_yield * material_input

############################################################### UNITS ##############################################################
# Unit 1: Inspection 
Unit1 = Unit('Inspection and Grading')
Unit1.temperature = ambient_t 
Unit1.unit_type = ''
Unit1.expected_flows_in = ['Raw Feed', 'Electricity (Inspector)']
Unit1.expected_flows_out = ['Process Flow 1', 'Rejects']
Unit1.coefficients = {'Reject Ratio' : (20/1000), 'Electricity (kw/kg)': (59.5)}

def Inspector_func(feed_in, coeff):
    material_in = feed_in.attributes['mass_flow_rate']
    electricity_in = material_out * coeff['Electricity (kw/kg)']
    rejects_out = material_in * coeff['Reject Ratio']
    feed_out = material_in - rejects_out
    print('Unit 1')
    return[{'name' : 'Electricity (Inspector)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Rejects', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : rejects_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Process Flow 1', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit1.calculations = {'Raw Feed': Inspector_func}
FlowA = Flow(name = 'Raw Feed', components = ['Material'], composition = [1], flow_type = 'input', mass_flow_rate = material_input)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Washing 
Unit2 = Unit('Washing')
Unit2.temperature = 45.0   
Unit2.unit_type = ''
Unit2.expected_flows_in = ['Process Flow 1', 'Electricity (Washing)', 'Hot Water (Washing)']
Unit2.expected_flows_out = ['Process Flow 2', 'Wastewater (Washing)']
Unit2.coefficients = {'Hot Water Demand (kJ/kg)': 354.1, 'Electricity (kw/kg)': 74.4, 'loses': 0.10, 'Water Temp': (Unit2.temperature + 10)}

def Washing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (material_out * coeff['Hot Water Demand (kJ/kg)']) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss 
    electrcity_in = feed_in * coeff['Electricity (kw/kg)']
    m_hw = Q_steam / (C_pw * (coeff['Water Temp'] - ambient_t))
    print('Unit 2')
    return[{'name' : 'Electricity (Washing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electrcity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Hot Water (Washing)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_hw,
             'flow_type': 'Steam', 'Temperature': coeff['Water Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Wastewater (Washing)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_hw,
             'flow_type': 'Wastewater', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Process Flow 2', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit2.calculations = {'Process Flow 1': Washing_func}

# Unit 3: Cutting and Slicing 
Unit3 = Unit('Cutting and Slicing')
Unit3.temperature = ambient_t  
Unit3.unit_type = 'Mechanical Process'
Unit3.expected_flows_in = ['Process Flow 2', 'Electricity (Cutting)']
Unit3.expected_flows_out = ['Cut Material', 'Waste (Cutting)']
Unit3.coefficients = {'Waste Rate': 0.005, 'Electricity (kw/kg)': 126.5}

def Cutting_and_slicing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    waste_out = feed_in * coeff['Waste Rate']
    feed_out = feed_in - waste_out
    print('Unit 3') 
    return[{'name' : 'Electricity (Cutting)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss}, 
            {'name' : 'Cut Material', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Waste (Cutting)', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit3.calculations = {'Process Flow 2': Cutting_and_slicing_func}

# Unit 4: Scalding and Blanching 
Unit4 = Unit('Scalding and Blanching')
Unit4.temperature = 91.5   
Unit4.unit_type = ''
Unit4.expected_flows_in = ['Cut Material', 'Steam (Scalding)', 'Electricity (Scalding)']
Unit4.expected_flows_out = ['Scalded Material', 'Condensate (Scalding)', 'Waste (Scalding)']
Unit4.coefficients = {'Steam Demand (kJ/kg)': 173, 'loses': 0.10, 'Waste rate': 0.01, 'Electricity (kw/kg)': 37.2, 'Steam Temp': 100}

def Scalding_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = feed_in * coeff['Waste rate']
    feed_out = feed_in - waste_out
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (material_out * coeff['Steam Demand (kJ/kg)']) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss
    m_steam = Q_steam / Hvap
    electricity_in = coeff['Electricity (kw/kg)'] * material_out
    print('Unit 4')
    return[{'name' : 'Steam (Scalding)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Scalding)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Waste (Scalding)', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Scalded Material', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'name' : 'Electricity (Scalding)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit4.calculations = {'Cut Material': Scalding_func}

# Unit 5: Peeling 
Unit5 = Unit('Peeling and Pulping')
Unit5.temperature = ambient_t   
Unit5.unit_type = 'Seperator'
Unit5.expected_flows_in = ['Scalded Material', 'Electricity (Peeling)'] 
Unit5.expected_flows_out = ['Pulped Material', 'Waste (Peeling)']
Unit5.coefficients = {'Waste rate': 0.09, 'Electricity (kw/kg)': 148.8}

def Peeling_and_pulping_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = feed_in * coeff['Waste rate']
    feed_out = feed_in - waste_out 
    Q_loss = feed_flow.attributes['heat_flow_rate']
    electrcity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 5')
    return[{'name' : 'Electricity (Peeling)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electrcity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss}, 
            {'name' : 'Waste (Peeling)', 'components' : ['Peels'], 'composition' :[1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Pulped Material', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit5.calculations = {'Scalded Material': Peeling_and_pulping_func}

# Unit 7: Cooker 
Unit7 = Unit('Cooker')
Unit7.temperature = 95.0  
Unit7.unit_type = ''
Unit7.expected_flows_in = ['Pulped Material', 'Steam (Cooker)']
Unit7.expected_flows_out = ['Cooked Material', 'Condensate (Cooker)']
Unit7.coefficients = {'Steam Demand (kJ/kg)': 326.9, 'loses': 0.10, 'Steam Temp': (Unit7.temperature + 10)}

def Cooker_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (material_out * coeff['Steam Demand (kJ/kg)'])/ (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss 
    m_steam = Q_steam / Hvap 
    print('Unit 7')
    return[{'name' : 'Steam (Cooker)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Cooker)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Cooked Material', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit7.calculations = {'Pulped Material': Cooker_func}

# Unit 8: Concentrator - I would like this to be a steam economy unit in the future
Unit8 = Unit('Concentrator')
Unit8.temperature = 67.5   
Unit8.unit_type = ''
Unit8.expected_flows_in = ['Cooked Material', 'Steam (Concentrator)', 'Electricity (Concentrator)']
Unit8.expected_flows_out = ['Concentrate', 'Condensate (Concentrator)']
Unit8.coefficients = {'Steam Demand (kJ/kg)': 697.4, 'loses': 0.10, 'Water evap rate': 0.10, 'Electricity (kw/kg)': 74.4, 'Steam Temp': 100}

def Concentrator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_evap = feed_in * coeff['Water evap rate']
    feed_out = feed_in - water_evap
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (coeff['Steam Demand (kJ/kg)'] * material_out) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss 
    m_steam = Q_steam / Hvap
    electricity_in = coeff['Electricity (kw/kg)'] * material_out
    print('Unit 8')
    return[{'name' : 'Steam (Concentrator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Concentrator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam+water_evap,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Concentrate', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Electricity (Concentrator)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Cooked Material': Concentrator_func}

# Unit 9: Cooling and Washing 
Unit9 = Unit('Cooling and Washing')
Unit9.temperature = ambient_t   
Unit9.unit_type = ''
Unit9.expected_flows_in = ['Concentrate', 'Water (Cooler/Washer)', 'Electricity (Cooler/Washer)']
Unit9.expected_flows_out = ['Hot Wastewater (Cooler/Washer)', 'Cool Concentrate']
Unit9.coefficients = {'Electricity (kw/kg)': 74.4, 'Water ratio': 2.0}

def Cooler_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_in = feed_in * coeff['Water ratio']
    electricity_in = material_out * coeff['Electricity (kw/kg)']
    print('Unit 9')
    return[{'name' : 'Electricity (Cooler/Washer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Cool Concentrate', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Water (Cooler/Washer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'name' : 'Hot Wastewater (Cooler/Washer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Waste Water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in}]
Unit9.calculations = {'Concentrate': Cooler_func}

# Unit 10: Brine Heater - Is this only heating the brine or is it heating the brine and the material 
Unit10 = Unit('Brine Heater')
Unit10.temperature = 87.5   
Unit10.unit_type = ''
Unit10.expected_flows_in = ['Brine', 'Cool Concentrate', 'Steam (Brine Heater)']
Unit10.expected_flows_out = ['Brine and Material', 'Condensate (Brine Heater)']
Unit10.coefficients = {'Steam Demand (kJ/kg)': 163.5, 'Steam Temp': 100, 'loses':0.10, 'Brine ratio': (38.4/767.6)} 

def Brine_heater_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    brine_in = coeff['Brine ratio'] * feed_in  
    feed_out = brine_in + feed_in 
    Q_steam = (material_out * coeff['Steam Demand (kJ/kg)']) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss 
    m_steam = Q_steam / Hvap 
    print('Unit 10')
    return[{'name' : 'Steam (Brine Heater)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Brine Heater)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Brine and Material', 'components' : ['Material'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Brine', 'components' : ['Brine'], 'composition' :[1], 'mass_flow_rate' : brine_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit10.calculations = {'Cool Concentrate': Brine_heater_func}
   
# Unit 11: Packing 
Unit11 = Unit('Packing')
Unit11.temperature = ambient_t
Unit11.unit_type = 'Mechanical Process'
Unit11.expected_flows_in = ['Brine and Material', 'Electricity (Packing)']
Unit11.expected_flows_out = ['Packed Material']
Unit11.coefficients = {'Electricity (kw/kg)': 39.4}

def Packing_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    print('Unit 11')
    return [{'name': 'Electricity (Packing)', 'mass_flow_rate': 0,
             'flow_type': 'Electricity', 'elec_flow_rate': electricity_in, 'In or out': 'In',
             'Set calc': False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss},
            {'name': 'Packed Material', 'components': ['Material'], 'composition': [1], 'mass_flow_rate': feed_in,
             'flow_type': 'Process Stream', 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': 0}]
Unit11.calculations = {'Brine and Material': Packing_func}

# Unit 12: Exhasting 
Unit12 = Unit('Exhasting')
Unit12.temperature = 87.5  
Unit12.unit_type = ''
Unit12.expected_flows_in = ['Packed Material', 'Steam (Exhausting)']
Unit12.expected_flows_out = ['Exhausted Material', 'Condensate (Exhausting)']
Unit12.coefficients = {'Steam Demand (kJ/kg)': 163.5, 'loses': 0.10, 'Steam Temp': 100}

def Exhausting_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (feed_in * coeff['Steam Demand (kJ/kg)']) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss
    m_steam = Q_steam / Hvap
    print('Unit 12')
    return [{'name': 'Steam (Exhausting)', 'components': ['Water'], 'composition': [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out': 'In', 'Set calc': False, 'heat_flow_rate': Q_steam},
            {'name': 'Condensate (Exhausting)', 'components': ['Water'], 'composition': [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out': 'Out', 'Set calc': False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss},
            {'name': 'Exhausted Material', 'components': ['Material'], 'composition': [1], 'mass_flow_rate': feed_in,
             'flow_type': 'Process Stream', 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': Q_out}]
Unit12.calculations = {'Packed Material': Exhausting_func} 

# Unit 13: Sealing 
Unit13 = Unit('Sealing')
Unit13.temperature = 87.5  
Unit13.unit_type = 'Mechanical Process'
Unit13.expected_flows_in = ['Exhausted Material', 'Electricity (Sealing)']
Unit13.expected_flows_out = ['Sealed Material']
Unit13.coefficients = {'Electricity (kw/kg)': 74.4}

def Sealing_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 13')
    return [{'name': 'Electricity (Sealing)', 'mass_flow_rate': 0,
             'flow_type': 'Electricity', 'elec_flow_rate': electricity_in, 'In or out': 'In',
             'Set calc': False, 'heat_flow_rate': 0},
            {'name': 'Sealed Material', 'components': ['Material'], 'composition': [1], 'mass_flow_rate': feed_in,
             'flow_type': 'Process Stream', 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': Q_in}]
Unit13.calculations = {'Exhausted Material': Sealing_func} 

# Unit 14: Retort 
Unit14 = Unit('Retort')
Unit14.temperature = 110.5 
Unit14.unit_type = ''
Unit14.expected_flows_in = ['Sealed Material', 'Steam (Retort)']
Unit14.expected_flows_out = ['Sterilized Material', 'Condensate (Retort)']
Unit14.coefficients = {'Steam Demand (kJ/kg)': 232.2, 'loses': 0.10, 'Steam Temp': 120}

def Retort_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = (feed_in * coeff['Steam Demand (kJ/kg)']) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss
    m_steam = Q_steam / Hvap
    print('Unit 14')
    return [{'name': 'Steam (Retort)', 'components': ['Water'], 'composition': [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out': 'In', 'Set calc': False, 'heat_flow_rate': Q_steam},
            {'name': 'Condensate (Retort)', 'components': ['Water'], 'composition': [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out': 'Out', 'Set calc': False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss},
            {'name': 'Sterilized Material', 'components': ['Material'], 'composition': [1], 'mass_flow_rate': feed_in,
             'flow_type': 'Process Stream', 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': Q_out}]
Unit14.calculations = {'Sealed Material': Retort_func}

# Unit 15: Cooling (2) 
Unit15 = Unit('Cooling (2)')
Unit15.temperature = 30.0   
Unit15.unit_type = ''
Unit15.expected_flows_in = ['Sterilized Material', 'Electricity (Cooling)']
Unit15.expected_flows_out = ['Cooled Material']
Unit15.coefficients = {'Electricity (kw/kg)': 74.4}

def Cooling_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    print('Unit 15')
    return [{'name': 'Electricity (Cooling)', 'mass_flow_rate': 0,
             'flow_type': 'Electricity', 'elec_flow_rate': electricity_in, 'In or out': 'In',
             'Set calc': False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss},
            {'name': 'Cooled Material', 'components': ['Material'], 'composition': [1], 'mass_flow_rate': feed_in,
             'flow_type': 'Product', 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': 0}]
Unit15.calculations = {'Sterilized Material': Cooling_func}

#################################################################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit7, Unit8,
                Unit9, Unit10, Unit11, Unit12, Unit13, Unit14, Unit15]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

utilities_recap('utility_recap_speciality_canning', allflows, processunits)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

