# Questions for Yoana:
'''

'''
#  -*- coding: utf-8 -*-
"""
Created on Monday May 19th 09:19:45 am 2025 (Updated: August 8th)

@author: Aidan ONeil
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

# Global Variables
ambient_t = 20
Hvap = 2260
C_pw = 4.186
C_pair = 1.000

#################################################UNITS ########################
# Unit 1: Inspection
Unit1 = Unit('Inspector')
Unit1.expected_flows_in = ['Feed Tomatoes', 'Electricity (Inspector)']
Unit1.expected_flows_out = ['Raw Tomatoes', 'Rejects']

Unit1.coefficients = {'Reject Ratio' : (20/1000), 'Electricity (kw/kg)': (5*2.326)}

def Inspector_func(feed_in, coeff):
    tomatoes_in = feed_in.attributes['mass_flow_rate']
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    rejects_out = tomatoes_in * coeff['Reject Ratio']
    tomatoes_out = tomatoes_in - rejects_out
    print('Unit 1')
    return[{'name' : 'Electricity (Inspector)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Rejects', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : rejects_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Raw Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit1.calculations = {'Feed Tomatoes': Inspector_func}
FlowA = Flow(name = 'Feed Tomatoes', components = ['Tomatoes'], composition = [1], flow_type = 'input', mass_flow_rate = 100000)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Washing
Unit2 = Unit('Washer')
Unit2.expected_flows_in = ['Raw Tomatoes', 'Electricity (Washer)', 'Hot Water (Washer)']
Unit2.expected_flows_out = ['Waste water (Washer)', 'Clean Tomatoes']

Unit2.coefficients = {'Water to Tomatoes Ratio': 3.00, 'Electricity (kw/kg)': (7*2.326), 'Water Temp': ambient_t + 7.5}

def Washing_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    water_in = tomatoes_in * coeff['Water to Tomatoes Ratio']
    Q_in = water_in * C_pw * (coeff['Water Temp'] - ambient_t)
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    print('Unit 2')
    return[{'name' : 'Electricity (Washer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Hot Water (Washer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_in},
           {'name' : 'Waste water (Washer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Waste water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in},
           {'name' : 'Clean Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : tomatoes_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit2.calculations = {'Raw Tomatoes': Washing_func}

# Unit 3: Color Sorting
Unit3 = Unit('Color Sorter')
Unit3.expected_flows_in = ['Clean Tomatoes', 'Electricity (Sorter)']
Unit3.expected_flows_out = ['Green Tomatoes', 'Red Tomatoes']

Unit3.coefficients = {'Green Ratio': 0.05, 'Electricity (kw/kg)': 0.000}

def Colorsorter_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    green_tomatoes_out = tomatoes_in * coeff['Green Ratio']
    red_tomatoes_out = tomatoes_in - green_tomatoes_out
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    print('Unit 3')
    return[{'name' : 'Electricity (Sorter)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Green Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : green_tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Red Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : red_tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit3.calculations = {'Clean Tomatoes': Colorsorter_func}

# Unit 4: Peeling
Unit4 = Unit('Peeler')
Unit4.expected_flows_in = ['Red Tomatoes', 'Electricity (Peeler)', 'Steam (Peeler)']
Unit4.expected_flows_out = ['Peeling Pulp', 'Condensate (Peeler)', 'Tomatoes']

Unit4.coefficients = {'Steam per kg Tomato': 0.15, 'Electricity (kw/kg)': (12 * 2.326), 'Steam Temp': 100.000,
                      'Peel Fraction': 0.08, 'Unit Temp': 0.000, 'C_ptomatoe': 3.517, 'loses': .20}

def Peeler_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    Q_in = tomatoe_flow.attributes['heat_flow_rate']
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    peels_out = tomatoes_in * coeff['Peel Fraction']
    tomatoes_out = tomatoes_in - peels_out
    # Heat Balance
    m_steam = coeff['Steam per kg Tomato']
    Q_steam = m_steam * Hvap
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam - Q_loss
    Q_tomatoes = (tomatoes_out / tomatoes_in) * Q_out
    Q_peels = Q_out - Q_tomatoes
    print('Unit 4')
    return[{'name' : 'Electricity (Peeler)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_tomatoes},
           {'name' : 'Peeling Pulp', 'components' : ['Pulp'], 'composition' :[1], 'mass_flow_rate' : peels_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_peels},
           {'name' : 'Steam (Peeler)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Peeler)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit4.calculations = {'Red Tomatoes': Peeler_func} 

# Unit 5 Sorting
Unit5 = Unit('Sorter')
Unit5.expected_flows_in = ['Tomatoes', 'Electricity (Sorting)']
Unit5.expected_flows_out = ['Unpeeled Tomatoes', 'Peeled Tomatoes']

Unit5.coefficients = {'Reject Ratio': 0.02, 'Electricity (kw/kg)': 0.000}

def Sorting_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    Q_in =  tomatoe_flow.attributes['heat_flow_rate']
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    unpeeled_tomatoes_out = tomatoes_in * coeff['Reject Ratio']
    peeled_tomatoes_out = tomatoes_in - unpeeled_tomatoes_out
    print('Unit 5')
    return[{'name' : 'Electricity (Sorting)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Unpeeled Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : unpeeled_tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Peeled Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : peeled_tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'Heat loss': Q_in}]

Unit5.calculations = {'Tomatoes': Sorting_func}  

# Unit 6: Dicing
Unit6 = Unit('Dicer')
Unit6.expected_flows_in = ['Peeled Tomatoes', 'Electricity (Dicer)']
Unit6.expected_flows_out = ['Dicing Pulp/Juice', 'Diced Tomatoes']

Unit6.coefficients = {'Juice Ratio': .10, 'Electricity (kw/kg)': 0.000}

def Dicer_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    Q_in = tomatoe_flow.attributes['heat_flow_rate']
    juice_out = coeff['Juice Ratio'] * tomatoes_in
    tomatoes_out = tomatoes_in - juice_out
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    Q_tomatoes = (tomatoes_out / tomatoes_in) * Q_in
    Q_juice = Q_in - Q_tomatoes
    print('Unit 6')
    return[{'name' : 'Electricity (Dicer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Dicing Pulp/Juice', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : juice_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_juice},
           {'name' : 'Diced Tomatoes', 'components' : ['Tomatoes'], 'composition' :[1], 'mass_flow_rate' : tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_tomatoes}]

Unit6.calculations = {'Peeled Tomatoes': Dicer_func}
    
# Unit 7: Filling and Can Washing 1
Unit7 = Unit('Filler and Can Washer (1)')
Unit7.expected_flows_in = ['Diced Tomatoes', 'Electricity (Filling 1)', 'Cans (1)', 'Water (Can Washer 1)']
Unit7.expected_flows_out = ['Canned Diced Tomatoes', 'Wastewater (Can Washer 1)']

Unit7.coefficients = {'Can to Tomatoes': .10 , 'Water to Cans': 2.00, 'Electricity (kw/kg)': (10*2.326)}

def Filler_one_func(tomatoe_flow, coeff):
    tomatoes_in = tomatoe_flow.attributes['mass_flow_rate']
    Q_loss = tomatoe_flow.attributes['heat_flow_rate']
    cans_in = tomatoes_in * coeff['Can to Tomatoes']
    water_in = cans_in * coeff['Water to Cans']
    electricity_in = tomatoes_in * coeff['Electricity (kw/kg)']
    tomatoes_out = cans_in + tomatoes_in
    can_wt = cans_in / tomatoes_out
    print('Unit 7')
    return[{'name' : 'Electricity (Filling 1)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss},
            {'name' : 'Water (Can Washer 1)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'name' : 'Waste water (Can Washer 1)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Waste water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
            {'name' : 'Cans (1)', 'components' : ['Cans'], 'composition' :[1], 'mass_flow_rate' : cans_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'name' : 'Canned Diced Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' :[1-can_wt, can_wt], 'mass_flow_rate' : tomatoes_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit7.calculations = {'Diced Tomatoes': Filler_one_func}
            

# Unit 9: Exhausting
Unit9 = Unit('Exhausting')
Unit9.expected_flows_in = ['Canned Diced Tomatoes', 'Steam (Exhausting)', 'Electricity (Exhausting)']
Unit9.expected_flows_out = ['Canned Exhausted Tomatoes', 'Condensate (Exhausting)']

Unit9.coefficients = {'Unit Temp': 90, 'loses': .30, 'c_psteel': 0.5, 'c_ptomato': 3.9,
                      'Steam Temp': 0.00, 'Electricity (kw/kg)': (7*2.326)}

def Exhausting_func(cans_flow, coeff):
    tomatoes_in = (cans_flow.attributes['mass_flow_rate']) * (cans_flow.attributes['composition'][cans_flow.attributes['components'].index('Tomatoes')])
    cans_in = (cans_flow.attributes['mass_flow_rate']) - tomatoes_in
    Q_out = (tomatoes_in * coeff['c_ptomato'] * (coeff['Unit Temp'] - ambient_t)) + (cans_in * coeff['c_psteel'] * (coeff['Unit Temp'] - ambient_t))
    Q_in = cans_flow.attributes['heat_flow_rate']
    electricity_in = (cans_flow.attributes['mass_flow_rate']) * coeff['Electricity (kw/kg)']
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    cans_out = cans_flow.attributes['mass_flow_rate']
    print('Unit 9')
    return[{'name' : 'Electricity (Exhausting)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Steam (Exhausting)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Exhausting)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Canned Exhausted Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' : cans_flow.attributes['composition'], 'mass_flow_rate' : cans_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit9.calculations = {'Canned Diced Tomatoes':Exhausting_func}
           
# Unit 10 Seeling
Unit10 = Unit('Seeling')
Unit10.expected_flows_in = ['Canned Exhausted Tomatoes', 'Electricity (Seeler)']
Unit10.expected_flows_out = ['Sealed Diced Tomatoes']

Unit10.coefficients = {'Electricity (kw/kg)': (10*2.326)}

def Sealing_func(cans_flow, coeff):
    cans_in = cans_flow.attributes['mass_flow_rate']
    electricity_in = cans_in * coeff['Electricity (kw/kg)']
    print('Unit 10')
    return[{'name' : 'Electricity (Seeler)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Sealed Diced Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' : cans_flow.attributes['composition'], 'mass_flow_rate' : cans_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': cans_flow.attributes['heat_flow_rate']}]

Unit10.calculations = {'Canned Exhausted Tomatoes': Sealing_func}
           

# Unit 11: Heat Sterilization 1 
Unit11 = Unit('Heat Sterlization')
Unit11.expected_flows_in = ['Steam (Sterilizer 1)', 'Sealed Diced Tomatoes', 'Electricity (Sterilizer 1)']
Unit11.expected_flows_out = ['Condensate (Sterilizer 1)', 'Sterile Diced Tomatoes']

Unit11.coefficients = {'Steam Temp': 100, 'Unit Temp': 121.0, 'Steam Demand (kJ/kg)': (217 * 2.326), 'Electricity (kw/kg)': 0.000,
                       'loses': 0.10}

def Heatsterilization_one_func(cans_flow, coeff):
    cans_in = cans_flow.attributes['mass_flow_rate']
    electricity_in = cans_in * coeff['Electricity (kw/kg)']
    steel_in = cans_in * (cans_flow.attributes['composition'][cans_flow.attributes['components'].index('Cans')])
    tomatoes_in = cans_in - steel_in
    Q_in = cans_flow.attributes['heat_flow_rate']
    Q_out = cans_in * coeff['Steam Demand (kJ/kg)']
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    print('Unit 11')
    return[{'name' : 'Electricity (Sterilizer 1)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Steam (Sterilizer 1)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Sterilizer 1)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Sterile Diced Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' : cans_flow.attributes['composition'], 'mass_flow_rate' : cans_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit11.calculations = {'Sealed Diced Tomatoes': Heatsterilization_one_func}
    
# Unit 12: Cooler - 25 degrees for cooling water?? 
Unit12 = Unit('Cooler')
Unit12.expected_flows_in = ['Electricity (Cooler)', 'Cooling Water (Cooler)', 'Sterile Diced Tomatoes']
Unit12.expected_flows_out = ['Water (Cooler)', 'Cooled Diced Tomatoes']

Unit12.coefficients = {'Inlet Water Temp': 25.0, 'Outlet Water Temp': 35.0, 'Unit Temp': 40.0, 'C_psteel': .5,
                       'C_ptomatoe': 3.9, 'Electricity (kw/kg)': (7*2.326)}

def Cooler_func(cans_flow, coeff):
    cans_in = cans_flow.attributes['mass_flow_rate']
    steel_in = cans_in * (cans_flow.attributes['composition'][cans_flow.attributes['components'].index('Cans')])
    tomatoes_in = cans_in - steel_in
    Q_in = cans_flow.attributes['heat_flow_rate']
    Q_out = (steel_in * coeff['C_psteel'] * (coeff['Unit Temp'] - ambient_t)) + (tomatoes_in * coeff['C_ptomatoe'] * (coeff['Unit Temp'] - ambient_t))
    Q_cw = Q_out - Q_in
    m_cw = Q_cw / (C_pw * (coeff['Inlet Water Temp'] - coeff['Outlet Water Temp']))
    electricity_in = coeff['Electricity (kw/kg)'] * cans_in
    print('Unit 12')
    return[{'name' : 'Electricity (Cooler)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Cooling Water (Cooler)', 'components' : 'Water', 'mass_flow_rate' : m_cw,
             'flow_type': 'Cooling Water', 'temperature' : coeff['Inlet Water Temp'] ,'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cw},
           {'name' : 'Water (Cooler)', 'components' : 'Water', 'mass_flow_rate' : m_cw,
             'flow_type': 'Water', 'temperature' : coeff['Outlet Water Temp'] ,'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Cooled Diced Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' : cans_flow.attributes['composition'], 'mass_flow_rate' : cans_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit12.calculations = {'Sterile Diced Tomatoes': Cooler_func}            
    
# Unit 13: Packaging 
Unit13 = Unit('Packaging 1')
Unit13.expected_flows_in = ['Cooled Diced Tomatoes', 'Electricity (Packaging 1)']
Unit13.expected_flows_out = ['Product Diced Tomatoes']

Unit13.coefficients = {'Electricity (kw/kg)': (15 *2.326)}

def Packageing_one_func(cans_flow, coeff):
    cans_in = cans_flow.attributes['mass_flow_rate']
    electricity_in = cans_in * coeff['Electricity (kw/kg)']
    Q_in = cans_flow.attributes['heat_flow_rate']
    print('Unit 13')
    return[{'name' : 'Electricity (Packaging 1)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Product Diced Tomatoes', 'components' : ['Tomatoes','Cans'], 'composition' : cans_flow.attributes['composition'], 'mass_flow_rate' : cans_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_in}]

Unit13.calculations = {'Cooled Diced Tomatoes': Packageing_one_func}
           
# Unit 14: Pulping
Unit14 = Unit('Pulping')
Unit14.required_calc_flows = 4
Unit14.expected_flows_in = ['Electricity (Pulping)', 'Green Tomatoes', 'Peeling Pulp', 'Unpeeled Tomatoes', 'Dicing Pulp/Juice']
Unit14.expected_flows_out = ['Tomatoe Pulp', 'Waste (Pulping)']

Unit14.coefficients = {'Electricity (kw/kg)': (7*2.326), 'Waste Ratio': 0.05}

def Pulping_func(ablist, coeff):
    green_tomatoes_in = ablist[0]
    peeling_pulp_in = ablist[1]
    unpeeled_tomatoes_in = ablist[2]
    juice_in = ablist[3]
    Q_in = (green_tomatoes_in.attributes['heat_flow_rate']) + (peeling_pulp_in.attributes['heat_flow_rate']) + (unpeeled_tomatoes_in.attributes['heat_flow_rate']) + (juice_in.attributes['heat_flow_rate'])
    gt_in = green_tomatoes_in.attributes['mass_flow_rate']
    pp_in = peeling_pulp_in.attributes['mass_flow_rate']
    ut_in = unpeeled_tomatoes_in.attributes['mass_flow_rate']
    j_in = juice_in.attributes['mass_flow_rate']
    tomatoe_pulp_in = gt_in + pp_in + ut_in + j_in
    tomatoe_pulp_out = tomatoe_pulp_in * (1-coeff['Waste Ratio'])
    waste_out = tomatoe_pulp_in - tomatoe_pulp_out
    electricity_in = tomatoe_pulp_out * coeff['Electricity (kw/kg)']
    print('Unit 14')
    return[{'name' : 'Electricity (Pulping)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Tomatoe Pulp', 'components' : ['Tomatoes'], 'composition' : [1], 'mass_flow_rate' : tomatoe_pulp_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Waste (Pulping)', 'components' : ['Tomatoes'], 'composition' : [1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_in}]

Unit14.calculations = (['Green Tomatoes', 'Peeling Pulp', 'Unpeeled Tomatoes', 'Dicing Pulp/Juice'], Pulping_func)

# Unit 15: Evaporation - Is this a MEE - What is the unit temp?
Unit15 = Unit('Evaporator')
Unit15.expected_flows_in = ['Tomatoe Pulp', 'Steam (Evaporator)', 'Electricity (Evaporator)']
Unit15.expected_flows_out = ['Puree', 'Juices/Pastes', 'Water (Evaporator)', 'Condensate (Evaporator)']

Unit15.coefficients = {'Inlet Water wt%': .70, 'Outlet Water wt%': .3, 'loses': .25, 'Unit Temp': 90.,
                       'Steam Temp': 0.000, 'Electricity (kw/kg)': 0.000, 'Puree Split': .5, 'C_ptomatoe': 3.9}

def Evaporator_func(pulp_flow, coeff):
    pulp_in = pulp_flow.attributes['mass_flow_rate']
    Q_in = pulp_flow.attributes['heat_flow_rate']
    water_in = pulp_in * coeff['Inlet Water wt%']
    solids_in = pulp_in - water_in
    pulp_out = solids_in / (1- coeff['Outlet Water wt%'])
    water_evap = pulp_in - pulp_out
    electricity_in = pulp_in * coeff['Electricity (kw/kg)']
    Q_water_evap = water_evap * Hvap + (water_evap * C_pw * (100- ambient_t))
    Q_out = (pulp_out * coeff['Outlet Water wt%'] * C_pw * (coeff['Unit Temp'] - ambient_t)) + (pulp_out * (1- coeff['Outlet Water wt%']) * coeff['C_ptomatoe'] * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_out + Q_water_evap - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    puree_out = pulp_out * coeff['Puree Split']
    juice_out = pulp_out - puree_out
    Q_puree = Q_out * coeff['Puree Split']
    Q_juice = Q_out - Q_puree
    print('Unit 15')
    return[{'name' : 'Electricity (Evaporator)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Steam (Evaporator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Evaporator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Water (Evaporator)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': water_evap,
             'flow_type': 'Waste Heat', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap},
           {'name' : 'Puree', 'components' : ['Tomatoes','Water'], 'composition' : [1-coeff['Outlet Water wt%'],coeff['Outlet Water wt%']], 'mass_flow_rate' : puree_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_puree}, 
           {'name' : 'Juices/Pastes', 'components' : ['Tomatoes','Water'], 'composition' : [1-coeff['Outlet Water wt%'],coeff['Outlet Water wt%']], 'mass_flow_rate' : juice_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_juice}]

Unit15.calculations = {'Tomatoe Pulp': Evaporator_func}

# Unit 16: Mixing - I want a lose amount for this 
Unit16 = Unit('Mixer')
Unit16.expected_flows_in = ['Puree', 'Sauce Ingredients', 'Electricity (Mixer)']
Unit16.expected_flows_out = ['Sauce']

Unit16.coefficients = {'Ingredient Add Ratio': .1, 'Electricity (kw/kg)': 0.0000, 'loses': 0.10}

def Mixer_func(puree_flow, coeff):
    puree_in = puree_flow.attributes['mass_flow_rate']
    Q_in = puree_flow.attributes['heat_flow_rate']
    Q_loss = Q_in * coeff['loses']
    Q_out = Q_in - Q_loss
    ingredients_in = puree_in * coeff['Ingredient Add Ratio']
    electricity_in = puree_in * coeff['Electricity (kw/kg)']
    sauce_out = ingredients_in + puree_in
    print('Unit 16')
    return[{'name' : 'Electricity (Mixer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Sauce Ingredients', 'components' : ['Ingredients'], 'composition' : [1], 'mass_flow_rate' : ingredients_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Sauce', 'components' : ['Sauce'], 'composition' : [1], 'mass_flow_rate' : sauce_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit16.calculations = {'Puree': Mixer_func}

# Unit 17: Heat Sterilization 2
Unit17 = Unit('Heat Sterlization (2)')
Unit17.required_calc_flows = 2
Unit17.expected_flows_in = ['Juices/Pastes', 'Sauce', 'Steam (Heat Sterilizator 2)', 'Electricity (Heat Sterilizator 2)']
Unit17.expected_flows_out = ['Condensate (Heat Sterilizator (2)', 'Sterile Juices/Paste']

Unit17.coefficients = {'Steam Temp': 0.000, 'Unit Temp': 121, 'C_ptomatoe': 3.9, 'loses': .25,
                       'Electricity (kw/kg)': 0.0000}

def Heat_Sterilization_two_func(ablist, coeff):
    juice_flow = ablist[0]
    sauce_flow = ablist[1]
    Q_in = (juice_flow.attributes['heat_flow_rate']) + (sauce_flow.attributes['heat_flow_rate'])
    mass_in = (juice_flow.attributes['mass_flow_rate']) + (sauce_flow.attributes['mass_flow_rate'])
    Q_out = mass_in * coeff['C_ptomatoe'] * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap
    electricity_in = mass_in * coeff['Electricity (kw/kg)']
    Q_loss = Q_steam * coeff['loses']
    print('Unit 17')
    return[{'name' : 'Electricity (Heat Sterilizator 2)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Steam (Heat Sterilizator 2)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Heat Sterilizator (2))', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Sterile Juices/Paste', 'components' : ['Sauce'], 'composition' : [1], 'mass_flow_rate' : mass_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit17.calculations = (['Juices/Pastes', 'Sauce'], Heat_Sterilization_two_func)

# Unit 8: Filling and Packaging
Unit8 = Unit('Filling and Packaging')
Unit8.expected_flows_in = ['Sterile Juices/Paste', 'Cans (2)', 'Water (Filling 2)', 'Electricity (Filling and Packaging)']
Unit8.expected_flows_out = ['Waste Water (Filling 2)', 'Canned Other Products']

Unit8.coefficients = {'Can to Tomatoes': .10 , 'Water to Cans': 2.00, 'Electricity (kw/kg)': 0.000}

def Canning_and_packing_func(juice_flow, coeff):
    juice_in = juice_flow.attributes['mass_flow_rate']
    Q_loss = juice_flow.attributes['heat_flow_rate']
    electricity_in = juice_in * coeff['Electricity (kw/kg)'] 
    cans_in = coeff['Can to Tomatoes'] * juice_in
    water_in = coeff['Water to Cans'] * cans_in
    canned_out = cans_in + juice_in
    print('Unit 8')
    return[{'name' : 'Electricity (Filling and Packaging)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Water (Filling 2)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Waste water (Filling 2)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Waste water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
           {'name' : 'Cans (2)', 'components' : ['Cans'], 'composition' :[1], 'mass_flow_rate' : cans_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Canned Other Products', 'components' : ['Canned Sauce'], 'composition' : [1], 'mass_flow_rate' : canned_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit8.calculations = {'Sterile Juices/Paste': Canning_and_packing_func}

########################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit9,
                Unit10, Unit11, Unit12, Unit13, Unit14, Unit15, Unit16, Unit17, Unit8]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)
'''
for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)
    
'''
utilities_recap('heat_intensity_tomatoecanning_4', allflows, processunits)


