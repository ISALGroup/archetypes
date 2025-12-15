# -*- coding: utf-8 -*-
"""
Created on Thursday May 12th 8:04:34 2025

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
C_pnacl = 0.881

#########################################UNITS#################################
# Add Electricity requirements  for every unit 
# Unit1: Brine Wells - what percent is going up and what percent is going down?
Unit1 = Unit('Brine Wells')
Unit1.expected_flows_in = ['Brine']
Unit1.expected_flows_out = ['Brine to Aerator', 'Brine to Soda Wash']

Unit1.coefficients = {'Split to Soda Wash': .50}

def Brinewell_func(brine_flow, coeff):
    brine_in = brine_flow.attributes['mass_flow_rate']
    brine_to_soda = brine_in * coeff['Split to Soda Wash']
    brine_to_aerator = brine_in - brine_to_soda
    print('Brine Well')
    return[{'name' : 'Brine to Aerator', 'components' : ['Water', 'Salt'], 'composition' : [1-.26, .26], 'mass_flow_rate' : brine_to_aerator,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Brine to Soda Wash', 'components' : ['Water', 'Salt'], 'composition' : [1-.26, .26], 'mass_flow_rate' : brine_to_soda,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit1.calculations = {'Brine': Brinewell_func}
FlowA = Flow(name='Brine', components = ['Water', 'Salt'], composition = [.74, .26], flow_type = 'input', mass_flow_rate = 100000)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Aerator - Find a air to brine ratio
Unit2 = Unit('Aerator')
Unit2.expected_flows_in = ['Brine to Aerator', 'Air In (Aerator)']
Unit2.expected_flows_out = ['Brine to Chlorine Wash', 'Air Out (Aerator)']

Unit2.coefficients = {'Air to Brine Ratio': 2}

def Aerator_func(brine_flow, coeff):
    brine_in = brine_flow.attributes['mass_flow_rate']
    air_in = brine_in * coeff['Air to Brine Ratio']
    print('Aerator')
    return[{'name' : 'Brine to Chlorine Wash', 'components' : ['Water', 'Salt'], 'composition' : [1-.26, .26], 'mass_flow_rate' : brine_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Air In (Aerator)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Air Out (Aerator)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit2.calculations = {'Brine to Aerator': Aerator_func}

# Unit 3: Chlorine Wash - Find a chlorine ratio
Unit3 = Unit('Chlorine Wash')
Unit3.expected_flows_in = ['Brine to Chlorine Wash', 'Chlorine In']
Unit3.expected_flows_out = ['Brine to Settling Tank', 'Chlorine Out']

Unit3.coefficients = {'Chlorine to Brine': 0.3}

def Chlorinewash_func(brine_flow, coeff):
    brine_in = brine_flow.attributes['mass_flow_rate']
    chlorine_in = brine_in * coeff['Chlorine to Brine']
    print('Chlroine Wash')
    return[{'name' : 'Brine to Settling Tank', 'components' : ['Water', 'Salt'], 'composition' : [1-.26, .26], 'mass_flow_rate' : brine_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Chlorine In', 'components' : ['Chlorine'], 'composition' : [1], 'mass_flow_rate' : chlorine_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Chlorine Our', 'components' : ['Chlorine'], 'composition' : [1], 'mass_flow_rate' : chlorine_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit3.calculations = {'Brine to Chlorine Wash': Chlorinewash_func}

# Unit 4: Soda Wash - Find ratios for caustic soda and soda ash 
Unit4 = Unit('Soda Wash')
Unit4.expected_flows_in = ['Brine to Soda Wash', 'Caustic Soda', 'Soda Ash', 'Electricity (Soda Wash)']
Unit4.expected_flows_out = ['Brine to Settling Tank 2']

Unit4.coefficients = {'Caustic Soda to Brine': 0.3, 'Soda Ash to Brine': 0.2, 'Electricity (kw/kg)': 0.0}

def Sodawash_func(brine_flow, coeff):
    brine_in = brine_flow.attributes['mass_flow_rate']
    caustic_soda_in = brine_in * coeff['Caustic Soda to Brine']
    soda_ash_in = brine_in * coeff['Soda Ash to Brine']
    electricity_in = coeff['Electricity (kw/kg)'] * brine_in
    #update weight percent
    brine_out = brine_in + caustic_soda_in + soda_ash_in
    salt_in = brine_in * (brine_flow.attributes['composition'][brine_flow.attributes['components'].index('Salt')])
    salt_wt = salt_in / brine_out
    other_wt = (caustic_soda_in + soda_ash_in) / brine_out
    water_wt = 1- salt_wt - other_wt
    print('Soda Wash')
    return[{'name' : 'Brine to Settling Tank (2)', 'components' : ['Water', 'Salt', 'Other'], 'composition' : [water_wt, salt_wt, other_wt], 'mass_flow_rate' : brine_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Electricity (Soda Wash)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Caustic Soda', 'components' : ['Caustic Soda'], 'composition' : [1], 'mass_flow_rate' : caustic_soda_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Soda Ash', 'components' : ['Soda Ash'], 'composition' : [1], 'mass_flow_rate' : soda_ash_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit4.calculations = {'Brine to Soda Wash': Sodawash_func}

# Unit 5: Settling Tank - is there more info we can get for percipiation or is what I did about right? 
Unit5 = Unit('Settling Tank')
Unit5.required_calc_flows = 2
Unit5.expected_flows_in = ['Brine to Settling Tank (2)', 'Brine to Settling Tank']
Unit5.expected_flows_out = ['Brine to Feed Tank', 'Percipiates']

Unit5.coefficients = {'Percipiate Rate': .00}

def Settlingtank_func(ablist, coeff):
    soda_wash_flow = ablist[0]
    chlorine_wash_flow = ablist[1]
    soda_wash_in = soda_wash_flow.attributes['mass_flow_rate']
    chlorine_wash_in = chlorine_wash_flow.attributes['mass_flow_rate']
    input_flows = chlorine_wash_in + soda_wash_in 
    others_out = soda_wash_in * (soda_wash_flow.attributes['composition'][soda_wash_flow.attributes['components'].index('Other')])
    output_brine = input_flows - others_out
    print('Settling Tank')
    return[{'name' : 'Brine to MEE', 'components' : ['Water', 'Salt'], 'composition' : [1-.26, .26], 'mass_flow_rate' : output_brine,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Percipiates', 'components' : ['Salts'], 'composition' : [1], 'mass_flow_rate' : others_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit5.calculations = (['Brine to Settling Tank (2)', 'Brine to Settling Tank'], Settlingtank_func)

# Unit 6: Multiple Effect Evaporator - Reach out to Antoine about where the energy goes in the MEE
Unit6 = Unit('Vacuum Pan Evaporators')
Unit6.expected_flows_in = ['Brine to MEE', 'Steam (MEE)', 'Electricity (MEE)']
Unit6.expected_flows_out = ['Condensate (MEE)', 'Salt Slurry']

Unit6.coefficients = {'Steam Economy': 3.4, 'Electricity (kw/kg)': 0.0168, 'Water Slurry wt': 0.08}

def Vacuumpan_func(brine_flow, coeff):
    brine_in = brine_flow.attributes['mass_flow_rate']
    Q_in = brine_flow.attributes['heat_flow_rate']
    salt_in = brine_in * (brine_flow.attributes['composition'][brine_flow.attributes['components'].index('Salt')])
    salt_slurry_out = salt_in /(1 - coeff['Water Slurry wt'])
    water_evaporated = brine_in - salt_slurry_out
    steam_in = water_evaporated / coeff['Steam Economy']
    condensate_out = steam_in + water_evaporated
    electricity_in = coeff['Electricity (kw/kg)'] * brine_in
    Q_steam = steam_in * Hvap
    Q_slurry = Q_steam - Q_in
    print('Vacuumpan')
    return[{'name' : 'Salt Slurry', 'components' : ['Water', 'Salt'], 'composition' : [coeff['Water Slurry wt'], 1-coeff['Water Slurry wt']], 'mass_flow_rate' : salt_slurry_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_slurry},
           {'name' : 'Electricity (MEE)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (MEE)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (MEE)', 'components' : 'Water', 'mass_flow_rate' : condensate_out,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit6.calculations = {'Brine to MEE': Vacuumpan_func}

# Unit 7: Washer -- what is actually happening here, I am slightly confused cus it says its a wash but there is only electricity?
Unit7 = Unit('Washer')
Unit7.expected_flows_in = ['Salt Slurry', 'Electricity (Washer)']
Unit7.expected_flows_out = ['Washed Salt Slurry']

Unit7.coefficients = {'Electricity (kw/kg)': 0.000}

def Washer_func(slurry_flow, coeff):
    slurry_in = slurry_flow.attributes['mass_flow_rate']
    Q_in = slurry_flow.attributes['heat_flow_rate']
    electricity_in = slurry_in * coeff['Electricity (kw/kg)']
    Q_out = 0
    Q_loss = Q_in
    print('Washer')
    return[{'name' : 'Washed Salt Slurry', 'components' : ['Water', 'Salt'], 'composition' : slurry_flow.attributes['composition'], 'mass_flow_rate' : slurry_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Electricity (Washer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]
Unit7.calculations = {'Salt Slurry': Washer_func}

# Unit 8: Rotary Filter
Unit8 = Unit('Rotary Filter')
Unit8.expected_flows_in = ['Washed Salt Slurry', 'Electricity (Filter)']
Unit8.expected_flows_out = ['Salt to Dryer']

Unit8.coefficients = {'Electricity (kw/kg)': 0.2}

def Rotaryfilter_func(salt_flow, coeff):
    salt_in = salt_flow.attributes['mass_flow_rate']
    electricity_in = salt_in * coeff['Electricity (kw/kg)']
    Q_in = salt_flow.attributes['heat_flow_rate']
    print('Rotary')
    return[{'name' : 'Salt to Dryer', 'components' : ['Water', 'Salt'], 'composition' : salt_flow.attributes['composition'], 'mass_flow_rate' : salt_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'Electricity (Filter)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit8.calculations = {'Washed Salt Slurry': Rotaryfilter_func}

# Unit 9: Dryer - Need a unit temp and a steam temp
Unit9 = Unit('Dryer')
Unit9.expected_flows_in = ['Salt to Dryer', 'Electricity (Dryer)', 'Steam (Dryer)']
Unit9.expected_flows_out = ['Dry Salt', 'Condensate (Dryer)']

Unit9.coefficients = {'Electricity (kw/kg)': 0.028, 'Loses': 0.05, 'Outlet Water Content': 0.005, 'Unit Temp': 30}

def Dryer_func(salt_flow, coeff):
    flow_in = salt_flow.attributes['mass_flow_rate']
    salt_in = flow_in * (salt_flow.attributes['composition'][salt_flow.attributes['components'].index('Salt')])
    salt_out = salt_in / (1-coeff['Outlet Water Content'])
    water_evap = flow_in - salt_out
    electricity_in = flow_in * coeff['Electricity (kw/kg)']
    Q_in = salt_flow.attributes['heat_flow_rate']
    Q_water_evap = water_evap * Hvap
    Q_steam = (Q_water_evap - Q_in)/ (1-coeff['Loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['Loses']
    
    print('Dryer')

    return[{'name' : 'Steam (Dryer)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam+water_evap,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Electricity (Dryer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Dry Salt', 'components' : ['Salt', 'Water'], 'composition' : [1- coeff['Outlet Water Content'], coeff['Outlet Water Content']], 'mass_flow_rate': salt_out,
             'flow_type': 'Product', 'temperature' : coeff['Unit Temp'] ,'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap}]

Unit9.calculations = {'Salt to Dryer': Dryer_func}

######################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9]

main(allflows, processunits)

'''
for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)
'''    
    
    
utilities_recap('heat_intensity_salt_2', allflows, processunits)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)
