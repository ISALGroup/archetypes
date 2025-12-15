'''
Name: Aidan J ONeil
Date: 7/31/2025 1:40:00
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
diary_amount = 1000
C_pw = 4.186
Hvap = 2257
C_pmilk = 3.93
feed_milk_in = 10000
t_feed_milk = 7
Q_milk_in = feed_milk_in * C_pmilk * (t_feed_milk - ambient_t)


##############################################################UNITS################################################################
# Unit 1: Centrifuge
Unit1 = Unit('Centrifuge')
Unit1.expected_flows_in = ['Feed Milk', 'Electricity (Centrifuge)']
Unit1.expected_flows_out = ['Waste (Centrifuge)', 'Raw Milk']
Unit1.coefficients = {'Waste Ratio': 0.01, 'Electricity (kw/kg)': 0.00}

def Centrifuge_func_1(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    waste_out = feed_in * coeff['Waste Ratio']
    feed_out = feed_in - waste_out 
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = (feed_out / feed_in) * Q_in
    Q_waste = Q_in - Q_out
    print('Unit 1')
    return[{'name' : 'Electricity (Centrifuge)', 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Raw Milk', 'components' : ['Milk'], 'composition': [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process Stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Waste (Centrifuge)', 'components' : ['Waste'], 'composition': [1], 'mass_flow_rate' : waste_out,
            'flow_type': 'Waste', 'heat_flow_rate' : Q_waste,'In or out' : 'Out', 'Set calc' : False}]
Unit1.calculations = {'Feed Milk': Centrifuge_func_1}

FlowA = Flow(name = 'Feed Milk', components = ['Milk'], composition = [1], flow_type = 'input', mass_flow_rate = 100000)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Heat Exchanger
Unit2 = Unit('Heat Exchanger')
Unit2.expected_flows_in = ['Raw Milk']
Unit2.expected_flows_out = ['Chilled Milk', 'Waste Heat (Heat Exchanger 1)']
Unit2.coefficients = {'Outlet temp': 4.0}

def Heat_exchanger_func_1(milk_flow, coeff):
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Outlet temp'] - ambient_t)
    Q_waste = Q_in - Q_out
    print('Unit 2')
    return[{'name' : 'Chilled Milk', 'components' : ['Milk'], 'composition': [1], 'mass_flow_rate' : milk_in,
            'flow_type': 'Process Stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True},
           {'Heat loss': Q_waste}]
Unit2.calculations = {'Raw Milk': Heat_exchanger_func_1}

# Unit 3: Centrifuge 2
Unit3 = Unit('Centrifuge 2')
Unit3.expected_flows_in = ['Chilled Milk', 'Electricity (Centrifuge 2)']
Unit3.expected_flows_out = ['Waste (Centrifuge 2)', 'Process Milk 1']
Unit3.coefficients = {'Waste Ratio': 0.01, 'Electricity (kw/kg)': 0.00}

def Centrifuge_func_2(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    waste_out = feed_in * coeff['Waste Ratio']
    feed_out = feed_in - waste_out 
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = (feed_out / feed_in) * Q_in
    Q_waste = Q_in - Q_out
    print('Unit 3')
    return[{'name' : 'Electricity (Centrifuge 2)', 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Process Milk 1', 'components' : ['Milk'], 'composition': [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process Stream', 'heat_flow_rate' : Q_out,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Waste (Centrifuge 2)', 'components' : ['Waste'], 'composition': [1], 'mass_flow_rate' : waste_out,
            'flow_type': 'Waste', 'heat_flow_rate' : Q_waste,'In or out' : 'Out', 'Set calc' : False}]
Unit3.calculations = {'Chilled Milk': Centrifuge_func_2}

# Unit 5: Pasteurization
Unit5 = Unit('Pasteurization')
Unit5.expected_flows_in = ['Process Milk 1', 'Electricity (Pasteurization)', 'Steam (Pasteurization)']
Unit5.expected_flows_out = ['Pasteurized Milk']
Unit5.coefficients = {'Unit Temp': 72.0, 'Steam Temp': 100, 'loses':0.10, 'Electricity (kw/kg)':0.00}

def Pasteurization_func(milk_flow, coeff):
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    m_steam = Q_steam / Hvap
    electricity_in = milk_in * coeff['Electricity (kw/kg)']
    Q_loss = Q_steam * coeff['loses'] 
    print('Unit 5')
    return[{'name' : 'Steam (Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Electricity (Pasteurization)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Pasteurized Milk', 'components' : ['Milk'], 'composition' : [1], 'mass_flow_rate' : milk_in,
             'flow_type': 'Process Stream', 'temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit5.calculations = {'Process Milk 1': Pasteurization_func}

# Unit 6: Cooler
Unit6 = Unit('Cooler')
Unit6.expected_flows_in = ['Pasteurized Milk', 'Chilling Demand (Cooler)']
Unit6.expected_flows_out = ['Cooled Pasteurized Milk']
Unit6.coefficients = {'Unit Temp': 31}

def Cooler_func(milk_flow, coeff):
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate']
    Q_out = milk_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = (-1) * (Q_in - Q_out)
    print('Unit 6')
    return[{'name' : 'Cooled Pasteurized Milk', 'components' : ['Milk'], 'composition' : [1], 'mass_flow_rate' : milk_in,
             'flow_type': 'Process Stream', 'temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Chilling Demand (Cooler)',
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit6.calculations = {'Pasteurized Milk':Cooler_func}

# Unit 7: Make Vats
Unit7 = Unit('Make Vats')
Unit7.expected_flows_in = ['Cooled Pasteurized Milk', 'Rennet', 'Electricity (Make Vats)', 'Steam (Make Vats)']
Unit7.expected_flows_out = ['Curds', 'Liquid Whey', 'Condensate (Make Vats)']
Unit7.coefficients = {'Rennet to Milk': (0.004/10.3), 'Electricity (kw/kg)': 0.00, 'Whey percent out': .86,
                      'Unit Temp': ((39 + 55)/2), 'Steam Temp': 100, 'loses': 0.10}

def Make_vat_func(milk_flow, coeff):
    milk_in = milk_flow.attributes['mass_flow_rate']
    Q_in = milk_flow.attributes['heat_flow_rate'] 
    rennet_in = milk_in * coeff['Rennet to Milk']
    milk_in = rennet_in + milk_in
    whey_out = milk_in * coeff['Whey percent out']
    curds_out = milk_in - whey_out 
    electricity_in = milk_in * coeff['Electricity (kw/kg)']
    # Energy Balance
    C_pwhey = 3.925
    C_pcurds = 2.5
    Q_curds_out = C_pcurds * curds_out * (coeff['Unit Temp'] - ambient_t)
    Q_whey_out = C_pwhey * whey_out * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_curds_out + Q_whey_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 7')
    return[{'name' : 'Curds', 'components' : ['Curds'], 'composition' : [1], 'mass_flow_rate' : curds_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_curds_out},
           {'name' : 'Liquid Whey', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : whey_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_whey_out},
           {'name' : 'Electricity (Make Vats)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Rennet', 'components' : ['Milk'], 'composition' : [1], 'mass_flow_rate' : rennet_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'heat_flow_rate': 0},
           {'name' : 'Steam (Make Vats)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Make Vats)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]
Unit7.calculations = {'Cooled Pasteurized Milk': Make_vat_func}
           
# Unit 8: Draining/Cheddaring
Unit8 = Unit('Draining/Cheddaring')
Unit8.expected_flows_in = ['Salt', 'Curds']
Unit8.expected_flows_out = ['Salty Whey', 'Salted Cheese']
Unit8.coefficients = {'Salt to Cheese': (0.015/1.43), 'Whey out percent': .30}

def Cheddering_func(cheese_flow, coeff):
    cheese_in = cheese_flow.attributes['mass_flow_rate']
    salt_in = cheese_in * coeff['Salt to Cheese']
    salted_whey_out = (salt_in + cheese_in) * coeff['Whey out percent']
    salted_cheese_out = (salt_in + cheese_in) - salted_whey_out
    print('Unit 8')
    return[{'name' : 'Salted Cheese', 'components' : ['Curds'], 'composition' : [1], 'mass_flow_rate' : salted_cheese_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': cheese_flow.attributes['heat_flow_rate']},
           {'name' : 'Salty Whey', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : salted_whey_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': 0},
           {'name' : 'Salt', 'components' : ['Salt'], 'composition' : [1], 'mass_flow_rate' : salt_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc': False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Curds': Cheddering_func}
           
# Unit 9: Mechanical Cutter
Unit9 = Unit('Mechanical Cutter')
Unit9.expected_flows_in = ['Salted Cheese', 'Electricity (Cutter)']
Unit9.expected_flows_out = ['Warm Cheese']
Unit9.coefficients = {'Electricity (kw/kg)': 0.000}

def Mechanical_cutter_func(cheese_flow, coeff):
    cheese_in = cheese_flow.attributes['mass_flow_rate']
    electricity_in = cheese_in * coeff['Electricity (kw/kg)']
    print('Unit 9')
    return[{'name' : 'Electricity (Cutter)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Warm Cheese', 'components' : ['Cheese'], 'composition' : [1], 'mass_flow_rate' : cheese_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': cheese_flow.attributes['heat_flow_rate']}]
Unit9.calculations = {'Salted Cheese': Mechanical_cutter_func}

# Unit 10: Cold Storage
Unit10 = Unit('Cold Storage')
Unit10.expected_flows_in = ['Warm Cheese', 'Chilling Demand (Cold Storage)']
Unit10.expected_flows_out = ['Product Cheese']
Unit10.coefficients = {'Unit Temp': ((4+25)/2)}

def Cold_storage_func(cheese_flow, coeff):
    cheese_in = cheese_flow.attributes['mass_flow_rate']
    Q_in = cheese_flow.attributes['heat_flow_rate']
    C_pcheese = 2.77
    Q_out = cheese_in * C_pcheese * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in
    print('Unit 10')
    return[{'name' : 'Product Cheese', 'components' : ['Cheese'], 'composition' : [1], 'mass_flow_rate' : cheese_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': False, 'heat_flow_rate': Q_out},
           {'name' : 'Chilling Demand (Cold Storage)',
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit10.calculations = {'Warm Cheese': Cold_storage_func}
           
# Unit 11: Whey Pasteurization
Unit11 = Unit('Whey Pasteurization')
Unit11.required_calc_flows = 2
Unit11.expected_flows_in = ['Salty Whey', 'Liquid Whey', 'Electricity (Whey Pasteurization)', 'Steam (Whey Pasteurization)']
Unit11.expected_flows_out = ['Pasteurized Whey', 'Codensate (Whey Pasteurization)']
Unit11.coefficients = {'Unit Temp': 72, 'Steam Temp': 100, 'loses': 0.10, 'Electricity (kw/kg)': 0.000}

def Whey_pasteurization_func(ablist, coeff):
    salt_whey_flow = ablist[0]
    whey_flow = ablist[1]
    whey_in = (salt_whey_flow.attributes['mass_flow_rate']) + (whey_flow.attributes['mass_flow_rate'])
    Q_in = (salt_whey_flow.attributes['heat_flow_rate']) + (whey_flow.attributes['heat_flow_rate'])
    C_pwhey = 3.925
    Q_out = whey_in * C_pwhey * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    electricity_in = whey_in * coeff['Electricity (kw/kg)'] 
    print('Unit 11')
    return[{'name' : 'Steam (Whey Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Whey Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Electricity (Whey Pasteurization)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Pastuerized Whey', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : whey_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': Q_out}]
Unit11.calculations = (['Salty Whey', 'Liquid Whey'], Whey_pasteurization_func)
           
# Unit 12: Centrifuge 3
Unit12 = Unit('Centrifuge 3')
Unit12.expected_flows_in =['Pastuerized Whey', 'Electricity (Centrifuge 3)']
Unit12.expected_flows_out = ['Whey Cream', 'Whey to Osmosis']
Unit12.coefficients = {'Electricity (kw/kg)': 0.000, 'Whey Cream Split': 0.25}

def Centrifuge_separator_func(whey_flow,coeff):
    whey_in = whey_flow.attributes['mass_flow_rate']
    electricity_in = whey_in * coeff['Electricity (kw/kg)']
    cream_out = whey_in * coeff['Whey Cream Split']
    whey_to_ro = whey_in - cream_out
    Q_in = whey_flow.attributes['heat_flow_rate']
    print('Unit 12')
    return[{'name' : 'Electricity (Centrifuge 3)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Whey to Osmosis', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : whey_to_ro,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': Q_in},
           {'name' : 'Whey Cream', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : cream_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': False, 'heat_flow_rate': 0}]
Unit12.calculations = {'Pastuerized Whey': Centrifuge_separator_func}

# Unit 13: Reverse Osmosis
Unit13 = Unit('Reverse Osmosis')
Unit13.expected_flows_in = ['Electricity (Reverse Osmosis)', 'Whey to Osmosis']
Unit13.expected_flows_out = ['Water (Reverse Osmosis)', 'Whey to Evaporator']
Unit13.coefficients = {'Electricity (kw/kg)': 0.000, 'Water out Ratio':.25}

def Reverse_osmosis_func(whey_flow, coeff):
    whey_in = whey_flow.attributes['mass_flow_rate']
    electricity_in = whey_in * coeff['Electricity (kw/kg)']
    water_out = whey_in * coeff['Water out Ratio']
    whey_out = whey_in - water_out
    Q_loss = whey_flow.attributes['heat_flow_rate']
    print('Unit 13')
    return[{'name' : 'Electricity (Reverse Osmosis)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Whey to Evaporator', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : whey_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Water (Reverse Osmosis)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_out,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': False, 'heat_flow_rate': 0}]
Unit13.calculations = {'Whey to Osmosis': Reverse_osmosis_func}

# Unit 14: Whey Evaporation
Unit14 = Unit('Whey Evaporation')
Unit14.expected_flows_in = ['Steam (Whey Evaporator)', 'Electricity (Whey Evaporator)', 'Whey to Evaporator']
Unit14.expected_flows_out = ['Water Exhaust (Whey Evaporator)', 'Condensate (Whey Evaporator)', 'Wet Whey']
Unit14.coefficients = {'Steam Temp': 100, 'Unit Temp': 70, 'Water wt In': .935, 'Water wt Out': .50,
                       'loses': 0.10, 'Electricity (kw/kg)': 0.000, 'C_pwhey': 1.45}

def Whey_evaporator_func(whey_flow, coeff):
    whey_in = whey_flow.attributes['mass_flow_rate']
    water_evaporated = whey_in * (coeff['Water wt In'] - coeff['Water wt Out'])
    whey_out = whey_in - water_evaporated
    Q_in = whey_flow.attributes['heat_flow_rate']
    Q_evap = (water_evaporated * C_pw * (100 - ambient_t)) + (water_evaporated * Hvap)
    Q_out = whey_out * coeff['C_pwhey'] * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_evap + Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    electricity_in = whey_in * coeff['Electricity (kw/kg)']
    print('Unit 14')
    return[{'name' : 'Electricity (Whey Evaporator)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Whey Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Whey Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Water Exhaust (Whey Evaporator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evaporated,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': False, 'heat_flow_rate': Q_evap},
           {'name' : 'Wet Whey', 'components' : ['Whey'], 'composition' : [1], 'mass_flow_rate' : whey_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc': True, 'heat_flow_rate': Q_out}]

Unit14.calculations = {'Whey to Evaporator':Whey_evaporator_func}
           
# Unit 15: Whey Spray Drying
Unit15 = Unit('Whey Spray Drying')
Unit15.expected_flows_in = ['Wet Whey', 'Fuel (Whey Spray Dryer)']
Unit15.expected_flows_out = ['Water (Spray Dryer)', 'Dry Whey']
Unit15.coefficients = {'Heat Demand (kJ/kg)': 11628, 'Fuel HHV': 5200, 'loses': 0.10, 'Water Out': (.96 - .5)}

def Whey_spray_dryer_func(whey_flow, coeff):
    whey_in = whey_flow.attributes['mass_flow_rate']
    water_out = whey_in * coeff['Water Out']
    whey_out = whey_in - water_out
    Q_in = whey_flow.attributes['heat_flow_rate']
    Q_fuel = (whey_in * coeff['Heat Demand (kJ/kg)']) / (1- coeff['loses'])
    m_fuel = Q_fuel / coeff['Fuel HHV']
    Q_loss = Q_fuel * coeff['loses']
    Q_out = Q_fuel + Q_in - Q_loss
    print('Unit 15')
    return[{'name' : 'Fuel (Whey Spray Dryer)', 'components' : 'Fuel', 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Water (Spray Dryer)', 'components' : 'Water', 'mass_flow_rate' : water_out + m_fuel,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Dry Whey', 'components' : 'Whey', 'mass_flow_rate' : whey_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out}]
Unit15.calculations = {'Wet Whey': Whey_spray_dryer_func}
    
######################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit5, Unit6, Unit7, Unit8,
                Unit9, Unit10, Unit11, Unit12, Unit13, Unit14, Unit15]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)
    

utilities_recap('heat_intensity_cheese_3', allflows, processunits)

