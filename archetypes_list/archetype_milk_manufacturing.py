'''
Name: Aidan J ONeil
Date: 8/05/2025 10:00:00
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
milk_amount = 1000
C_pw = 4.186
Hvap = 2257
C_pmilk = 3.94
Q_milk_in = 0
C_pair = 1.0000

#####################################################UNITS######################################

# Unit 1: Preheater 
Unit1 = Unit('Preheater')
Unit1.expected_flows_in = ['Feed Milk', 'Steam (Preheater)']
Unit1.expected_flows_out = ['Condensate (Preheater)', 'Hot Milk']
Unit1.coefficients = {'Unit Temp': ambient_t, 'Steam temp': 100, 'loses':0.10}

def Preheater_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate'] 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in)/ (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses'] 
    m_steam = Q_steam / Hvap 
    print('Unit 1') 
    return[{'name' : 'Steam (Preheater)', 'components': 'Water', 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Hot Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}]
Unit1.calculations = {'Feed Milk': Preheater_func}

FlowA = Flow(name='Feed Milk', components = ['Milk'], composition = [1], flow_type = 'input', mass_flow_rate = milk_amount, heat_flow_rate=Q_milk_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Clarification 
Unit2 = Unit('Clarification')
Unit2.expected_flows_in = ['Hot Milk', 'Electricity (Clarification)']
Unit2.expected_flows_out = ['Clarified Milk']
Unit2.coefficients = {'Electricity (kw/kg)': 0.0068}

def Clarfication_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    electricity_in = milk_in * coeff['Electricity (kw/kg)']
    print('Unit 2')
    return[{'name' : 'Electricity (Clarification)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Clarified Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process', 'heat_flow_rate' : Q_in ,'In or out' : 'Out', 'Set calc' : True}]
Unit2.calculations = {'Hot Milk': Clarfication_func}

# Unit 3: Pasteurization 
Unit3 = Unit('Pasteurization')
Unit3.expected_flows_in = ['Clarified Milk', 'Steam (Pastuerization)']
Unit3.expected_flows_out = ['Pastuerized Milk', 'Condensate (Pastuerization)']
Unit3.coefficients = {'Unit Temp': 67, 'Steam Temp': 100, 'loses':0.05}

def Pastuerization_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp']- ambient_t)
    Q_steam = (Q_out - Q_in)/ (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 3')
    return[{'name' : 'Steam (Pastuerization)', 'components': 'Water', 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Pastuerization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Pastuerized Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process', 'heat_flow_rate' : Q_out ,'In or out' : 'Out', 'Set calc' : True}]
Unit3.calculations = {'Clarified Milk': Pastuerization_func}

# Unit 4: Cooler 
Unit4 = Unit('Cooler')
Unit4.expected_flows_in = ['Pastuerized Milk', 'Chilling (Cooler)'] 
Unit4.expected_flows_out = ['Cooled Milk']
Unit4.coefficients = {'Unit Temp': 70} 

def Cooler_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate'] 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 4') 
    return[{'name' : 'Cooled Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Chilling (Cooler)', 
            'flow_type': 'Chilling', 'heat_flow_rate' : Q_chilling,'In or out' : 'In', 'Set calc' : False, 'Set shear': False}]
Unit4.calculations = {'Pastuerized Milk':Cooler_func}

# Unit 5: Evaporator - Is there anything behind the 27% evaporation rate 
Unit5 = Unit('Evaporator')
Unit5.expected_flows_in = ['Cooled Milk', 'Steam (Evaporator)']
Unit5.expected_flows_out = ['Milk to Homogenizer', 'Condensate (Evaporator)', 'Water Vapor (Evaporator)']
Unit5.coefficients = {'Water wt In': 0.87, 'Water wt Out': .72, 'Steam Effect (kg/kg)': 0.13, 'Steam Temp': 120, 'Unit Temp': 110, 'loses': 0.10}

def Evaporator_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    water_in = milk_in * coeff['Water wt In']
    solids_in = milk_in - water_in
    milk_out = solids_in / (1-coeff['Water wt Out'])
    water_evap = milk_in - milk_out 
    Q_in = milk_flow.attributes['heat_flow_rate']
    m_steam = water_evap * coeff['Steam Effect (kg/kg)']
    Q_steam = m_steam * Hvap
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp']- ambient_t)
    Q_loss = Q_steam * coeff['loses']
    Q_water_evap = Q_in + Q_steam - Q_out - Q_loss
    print('Unit 5')
    return[{'name' : 'Steam (Evaporator)', 'components': 'Water', 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Water Vapor (Evaporator)', 'components' : ['Water'], 'composition':  [1], 'mass_flow_rate' : water_evap,
            'flow_type': 'Waste heat', 'heat_flow_rate' : Q_water_evap,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}, 
            {'name' : 'Milk to Homogenizer', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}]
Unit5.calculations = {'Cooled Milk': Evaporator_func}

# Unit 6: Homogenization - is there sector level split? 
Unit6 = Unit('Homogenization')
Unit6.expected_flows_in = ['Milk to Homogenizer', 'Electricity (Homogenizer)']
Unit6.expected_flows_out = ['Milk to Dried Milk', 'Product Milk', 'Milk to Condensed Milk' ]
Unit6.coefficients = {'Product Milk Split': 0.0, 'Dried Milk Split': .54, 'Electricity (kw/kg)': 0.0054}

def Homogenization_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    product_milk_out = milk_in * coeff['Product Milk Split']
    dried_milk_out = milk_in * coeff['Dried Milk Split']
    condensed_milk_out = milk_in - product_milk_out - dried_milk_out 
    Q_prod = Q_in * coeff['Product Milk Split']
    Q_dried = Q_in * coeff['Dried Milk Split']
    Q_condensed = Q_in - Q_prod - Q_dried 
    electricity_in = milk_in * coeff['Electricity (kw/kg)']
    print('Unit 6')
    return[{'name' : 'Electricity (Homogenizer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Milk to Dried Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : dried_milk_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_dried,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Milk to Condensed Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : condensed_milk_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_condensed,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Product Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : product_milk_out,
            'flow_type': 'Product', 'heat_flow_rate' : Q_prod,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}]
Unit6.calculations = {'Milk to Homogenizer': Homogenization_func}

# Unit 7: Dryer - We need accurate weight percentages on this unit or percentages like the other unit 
Unit7 = Unit('Dryer')
Unit7.expected_flows_in = ['Milk to Dried Milk', 'Fuel (Dryer)', 'Air (Dryer)']
Unit7.expected_flows_out = ['Dried Milk', 'Exhaust (Dryer)']
Unit7.coefficients = {'Unit Temp': 100, 'Fuel HHV': 5200, 'Air Ratio': 3.0, 'loses':0.10, 'Inlet water wt': .72, 'Outlet water wt': 0.03, 
                      "Steam Demand (kJ/kg)": 2670}

def Dryer_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    air_in = milk_in * coeff['Air Ratio']
    water_in = milk_in * coeff['Inlet water wt'] 
    solids_in = milk_in - water_in 
    milk_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = milk_in - milk_out 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_fuel = coeff['Steam Demand (kJ/kg)'] * milk_out 
    Q_loss = Q_fuel * coeff['loses']
    Q_milk = Q_in + Q_fuel - Q_loss
    m_fuel = Q_fuel / coeff['Fuel HHV']
    print('Unit 7')
    
    return[{'name' : 'Fuel (Dryer)', 'components': 'Fuel', 'mass_flow_rate': m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel}, 
            {'name' : 'Air (Dryer)', 'components': 'Air', 'mass_flow_rate': air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Exhaust (Dryer)', 'components': 'Air', 'mass_flow_rate': air_in + m_fuel + water_evap,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Dried Milk', 'components': 'Milk', 'mass_flow_rate': milk_out,
             'flow_type': 'Process Stream', 'Temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_milk}, 
            {'Heat loss': Q_loss}]
Unit7.calculations = {'Milk to Dried Milk': Dryer_func}

# Unit 8: Evaporative Cooling - I don't really know what is happening in this unit, need more info
Unit8 = Unit('Evaporative Cooling')
Unit8.expected_flows_in = ['Dried Milk', 'Chilling (Evaporative Cooling)']
Unit8.expected_flows_out = ['Cooled Dried Milk', 'Water (Evaporative Cooling)']
Unit8.coefficients = {'Unit Temp': 18, 'Evaporation Rate': 0.01}

def Evaporative_cooling_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    water_out = milk_in * coeff['Evaporation Rate']
    milk_out = milk_in - water_out 
    Q_water = water_out * Hvap 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_out * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_cooling = (Q_water + Q_out - Q_in)
    print('Unit 8')
    return[{'name' : 'Chilling (Evaporative Cooling)', 
            'flow_type': 'Chilling', 'heat_flow_rate' : Q_cooling,'In or out' : 'In', 'Set calc' : False, 'Set shear': False}, 
          {'name' : 'Cooled Dried Milk', 'components': 'Milk', 'composition': [1], 'mass_flow_rate': milk_out,
             'flow_type': 'Process Stream', 'Temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
          {'name' : 'Water (Evaporative Cooling)', 'components': 'Water', 'composition': [1], 'mass_flow_rate': water_out,
             'flow_type': 'Water', 'Temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water}]
Unit8.calculations = {'Dried Milk': Evaporative_cooling_func}

# Unit 9: Seperation/Sifting 
Unit9 = Unit('Seperation/Sifting')
Unit9.expected_flows_in = ['Cooled Dried Milk']
Unit9.expected_flows_out = ['Product Dried Milk', 'Waste (Seperation)']
Unit9.coefficients = {'Waste Ratio': 0.01}

def Seperator_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    waste_out = milk_in * coeff['Waste Ratio']
    milk_out = milk_in - waste_out 
    Q_in = milk_flow.attributes['heat_flow_rate']
    print('Unit 9')
    return[{'name' : 'Product Dried Milk', 'components': 'Milk', 'composition': [1], 'mass_flow_rate': milk_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in}, 
          {'name' : 'Waste (Seperation)', 'components': 'Waste', 'composition': [1], 'mass_flow_rate': waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Cooled Dried Milk': Seperator_func}

# Unit 10: Cooling (2) 
Unit10 = Unit('Cooling (2)')
Unit10.expected_flows_in = ['Milk to Condensed Milk', 'Chilling (Cooler 2)']
Unit10.expected_flows_out = ['Cooled Condensed Milk']
Unit10.coefficients = {'Unit Temp': 20} 

def Cooler_two_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate'] 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 10') 
    return[{'name' : 'Cooled Condensed Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Chilling (Cooler 2)', 
            'flow_type': 'Chilling', 'heat_flow_rate' : Q_chilling,'In or out' : 'In', 'Set calc' : False, 'Set shear': False}]
Unit10.calculations = {'Milk to Condensed Milk': Cooler_two_func}

# Unit 11: Canning 
Unit11 = Unit('Canning')
Unit11.expected_flows_in = ['Cooled Condensed Milk', 'Empty Cans', 'Steam (Canning)', 'Electricity (Canning)']
Unit11.expected_flows_out = ['Codnesate (Canning)', 'Canned Condensed Milk']
Unit11.coefficients = {'Unit Temp': 25, 'Steam Temp': 50, 'loses': .01, 'Can weight per milk': 0.00, 'Electricity (kw/kg)': 0.018}

def Canning_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    cans_in = coeff['Can weight per milk'] * milk_in 
    cans_out = milk_in + cans_in 
    Q_out = cans_out * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    electricity_in = milk_in * coeff['Electricity (kw/kg)']
    print('Unit 11')
    return[{'name' : 'Steam (Canning)', 'components': 'Water', 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Canning)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Empty Cans', 'components' : ['Cans'], 'composition':  [1], 'mass_flow_rate' : cans_in,
            'flow_type': 'Process stream', 'heat_flow_rate' : 0,'In or out' : 'In', 'Set calc' : False, 'Set shear': False}, 
           {'name' : 'Canned Condensed Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : cans_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False},
           {'name' : 'Electricity (Canning)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit11.calculations = {'Cooled Condensed Milk': Canning_func}

# Unit 12: Sterilization 
Unit12 = Unit('Sterilization')
Unit12.expected_flows_in = ['Canned Condensed Milk', 'Steam (Sterilization)']
Unit12.expected_flows_out = ['Sterile Condensed Milk', 'Condensate (Sterilization)']
Unit12.coefficients = {'Unit Temp': 110, 'Steam Temp': 120, 'loses': 0.10, 'Steam Demand (kJ/kg)': 115}

def Sterilization_func(milk_flow, coeff): 
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_steam = milk_in * coeff['Steam Demand (kJ/kg)']
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss
    m_steam = Q_steam / Hvap 
    print('Unit 12')
    return[{'name' : 'Steam (Sterilization)', 'components': 'Water', 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Sterilization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Sterile Condensed Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False},
           {'Heat loss': Q_loss}]
Unit12.calculations = {'Canned Condensed Milk': Sterilization_func}

# Unit 13: Cooling (4)  
Unit13 = Unit('Cooling (3)')
Unit13.expected_flows_in = ['Sterile Condensed Milk', 'Chilling (Cooler 3)']
Unit13.expected_flows_out = ['Product Condensed Milk']
Unit13.coefficients = {'Unit Temp': 20. }

def Cooler_3_func(milk_flow, coeff):
    milk_in = milk_flow.attributes['mass_flow_rate'] 
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 13') 
    return[{'name' : 'Product Condensed Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Product', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}, 
            {'name' : 'Chilling (Cooler 3)', 
            'flow_type': 'Chilling', 'heat_flow_rate' : Q_chilling,'In or out' : 'In', 'Set calc' : False, 'Set shear': False}]
Unit13.calculations = {'Sterile Condensed Milk': Cooler_3_func}

#########################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8,
                Unit9, Unit10, Unit11, Unit12, Unit13]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_dried_milk_manufacturing_7', allflows, processunits)
