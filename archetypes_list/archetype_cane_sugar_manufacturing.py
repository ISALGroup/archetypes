# -*- coding: utf-8 -*-
'''
Name: Aidan J ONeil
Date: 7/30/2025 (last edit: 7/30/2025 9:35:00 am)


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
C_psugar = 1.3
sugar_input = 100000

############################################################################UNITS#########################################################################
# Unit 1: Mingler - There should be steam here no...
Unit1 = Unit('Mingler')
Unit1.expected_flows_in = ['Cane Sugar Feed', 'Syrup', 'Steam (Mingler)']
Unit1.expected_flows_out = ['Sugar Water', 'Condensate (Mingler)']
Unit1.coefficients = {'Syrup to Feed': (1/2.3), 'Syrup sugar wt%': .65, 'Unit Temp': 65.,'loses':0.10,
                      'Steam Temp': 100}

def Mingler_func(feed_flow, coeff):
    sugar_in = feed_flow.attributes['mass_flow_rate']
    syrup_in = sugar_in * coeff['Syrup to Feed']
    sugar_out = sugar_in + syrup_in
    pure_sugar_in = (sugar_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Sugar')]) + (syrup_in * coeff['Syrup sugar wt%'])
    sugar_wt = pure_sugar_in / sugar_out
    # Heat Balance
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = ((sugar_wt * C_psugar) + ((1-sugar_wt) * C_pw)) * sugar_out * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 1')
    return[{'name' : 'Sugar Water', 'components' : ['Sugar', 'Water'], 'composition' : [sugar_wt, 1-sugar_wt], 'mass_flow_rate' : sugar_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Syrup', 'components' : ['Sugar', 'Water'], 'composition' : [coeff['Syrup sugar wt%'], 1-coeff['Syrup sugar wt%']], 'mass_flow_rate' : syrup_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Mingler)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Mingler)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit1.calculations = {'Cane Sugar Feed': Mingler_func}
FlowA = Flow(name = 'Cane Sugar Feed', components = ['Sugar', 'Water'], composition = [.98, .02], flow_type = 'input', mass_flow_rate = sugar_input)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Mixer
Unit2 = Unit('Mixer')
Unit2.expected_flows_in = ['Sugar Water', 'Electricity (Mixer)']
Unit2.expected_flows_out = ['Magma']
Unit2.coefficients = {'Electricity (kw/kg)': 0.00}

def Mixer_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_out = feed_flow.attributes['heat_flow_rate']
    print('Unit 2')
    return[{'name' : 'Electricity (Mixer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Magma', 'components' : ['Sugar', 'Water'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit2.calculations = {'Sugar Water': Mixer_func}

# Unit 3: Centrifuge - check solids wt% update here
Unit3 = Unit('Centrifuge')
Unit3.expected_flows_in = ['Magma', 'Electricity (Centrifuge)']
Unit3.expected_flows_out = ['Molasses', 'Washed Sugar']
Unit3.coefficients = {'Molasses percent': 0.12, 'Electricity (kw/kg)': 0.00, 'Molasses solids wt': .65}

def Centrifuge_func(magma_flow, coeff):
    magma_in = magma_flow.attributes['mass_flow_rate']
    solids_in = magma_in * (magma_flow.attributes['composition'][magma_flow.attributes['components'].index('Sugar')])
    Q_in = magma_flow.attributes['heat_flow_rate']
    molasses_out = magma_in * coeff['Molasses percent']
    washed_sugar_out = magma_in - molasses_out
    molasses_solids_out = molasses_out * coeff['Molasses solids wt']
    sugar_solids_out = solids_in - molasses_solids_out
    washed_sugar_wt = sugar_solids_out / washed_sugar_out
    Q_sugar = Q_in * (washed_sugar_out / magma_in)
    Q_molasses = Q_in - Q_sugar
    electricity_in = coeff['Electricity (kw/kg)'] * magma_in
    print('Unit 3')
    return[{'name' : 'Electricity (Centrifuge)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Washed Sugar', 'components' : ['Sugar', 'Water'], 'composition' : [washed_sugar_wt, 1-washed_sugar_wt], 'mass_flow_rate' : washed_sugar_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_sugar},
           {'name' : 'Molasses', 'components' : ['Sugar', 'Water'], 'composition' : [coeff['Molasses solids wt'], 1-coeff['Molasses solids wt']], 'mass_flow_rate' : molasses_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_molasses}]
Unit3.calculations = {'Magma': Centrifuge_func}
    
# Unit 4: ReMelter
Unit4 = Unit('ReMelter')
Unit4.expected_flows_in = ['Molasses', 'Steam (ReMelter)']
Unit4.expected_flows_out = ['Melted Molasses', 'Condensate (ReMelter)']
Unit4.coefficients = {'Steam Temp': 100, 'Unit Temp': 75, 'loses': .10}

def ReMelter_func(molasses_flow, coeff):
    molasses_in = molasses_flow.attributes['mass_flow_rate']
    Q_in = molasses_flow.attributes['heat_flow_rate']
    c_p = (((molasses_flow.attributes['composition'][molasses_flow.attributes['components'].index('Sugar')]) * C_psugar) +
           ((molasses_flow.attributes['composition'][molasses_flow.attributes['components'].index('Water')]) * C_pw))
    Q_out = molasses_in * c_p * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 4')
    return[{'name' : 'Steam (ReMelter)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (ReMelter)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Melted Molasses', 'components' : ['Sugar', 'Water'], 'composition' : molasses_flow.attributes['composition'], 'mass_flow_rate' : molasses_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Molasses': ReMelter_func}

# Unit 5: Premelter - Talk about the premelter!!
Unit5 = Unit('Premelter')
Unit5.expected_flows_in = ['Washed Sugar', 'Sweet Water', 'Steam (Premelter)']
Unit5.expected_flows_out = ['Codensate (Premelter)', 'Melted Sugar']
Unit5.coefficients = {'Unit Temp': 75, 'Steam Temp': 100, 'loses': 0.1, 'Sweet Water to Sugar': (601.9/7000),
                      'C_psweetwater': 4.0, 'Sweet Water Temp': 60, 'Melting Ratio': 0.19, 'HFus_sugar': 134.4}

def Premelter_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    sweet_water_in = sugar_input * coeff['Sweet Water to Sugar']
    melted_sugar_out = sweet_water_in + sugar_in
    Q_sugar = sugar_in * C_psugar * (coeff['Unit Temp'] - ambient_t)
    Q_melting = (sugar_in * coeff['Melting Ratio']) * coeff['HFus_sugar']
    Q_sweetwater = sweet_water_in * coeff['C_psweetwater'] * (coeff['Sweet Water Temp'] - ambient_t)
    Q_steam = (Q_melting + Q_sugar - (Q_in + Q_sweetwater)) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 5')
    return[{'name' : 'Steam (Premelter)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Premelter)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Melted Sugar', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate' : melted_sugar_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature':coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': (Q_melting + Q_sugar)},
           {'name' : 'Sweet Water', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : sweet_water_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature':coeff['Sweet Water Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_sweetwater, 'Set shear': True}]
Unit5.calculations = {'Washed Sugar': Premelter_func}
    
# Unit 6: Melter
Unit6 = Unit('Melter')
Unit6.required_calc_flows = 2
Unit6.expected_flows_in = ['Melted Molasses', 'Melted Sugar']
Unit6.expected_flows_out = ['Sugar to Clarifier']
Unit6.coefficients = {}

def Melter_func(ablist, coeff):
    molasses_flow = ablist[0]
    sugar_flow = ablist[1]
    Q_in = (sugar_flow.attributes['heat_flow_rate']) + (molasses_flow.attributes['heat_flow_rate'])
    mass_in = (sugar_flow.attributes['mass_flow_rate']) + (molasses_flow.attributes['mass_flow_rate'])
    print('Unit 6')
    return[{'name' : 'Sugar to Clarifier', 'components' : ['Sugar', 'Water'], 'composition' : [.681, .319], 'mass_flow_rate' :mass_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': 75, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit6.calculations = (['Melted Molasses', 'Melted Sugar'], Melter_func)

# Unit 7: Clarification
Unit7 = Unit('Clarification')
Unit7.expected_flows_in = ['Sugar to Clarifier', 'Phosphoric Acid', 'Lime', 'Steam (Clarifier)']
Unit7.expected_flows_out = ['Mud', 'Clarified Sugar', 'Condensate (Clarifier)']
Unit7.coefficients = {'Unit Temp': 80, 'Steam Temp': 100, 'Lime Ratio': 0.0025, 'Phosphoric Acid Ratio': 0.0015, 'Percipitates Ratio': (230.8/13800),
                      'loses':0.10}

def Clarification_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    h2po4_in = sugar_in * coeff['Phosphoric Acid Ratio']
    lime_in = sugar_in * coeff['Lime Ratio']
    mass_in = sugar_in + h2po4_in + lime_in
    mud_out = mass_in * coeff['Percipitates Ratio']
    sugar_out = mass_in - mud_out
    Q_out = mass_in * 2.8 * (coeff['Unit Temp'] - ambient_t)
    Q_out_mud = Q_out * (mud_out / mass_in)
    Q_out_sugar = Q_out - Q_out_mud
    Q_steam = (Q_out - Q_in) / (1-coeff['loses']) 
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    # Updating the water weight percentage
    water_in = (sugar_flow.attributes['composition'][sugar_flow.attributes['components'].index('Water')]) * sugar_in
    water_out = water_in - (mud_out * .75)
    water_out_wt = water_out / sugar_out
    sugar_wt = 1 - water_out_wt
    print('Unit 7')
    return[{'name' : 'Phosphoric Acid', 'components' : ['H2PO4'], 'composition' : [1], 'mass_flow_rate' :h2po4_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Lime', 'components' : ['Lime'], 'composition' : [1], 'mass_flow_rate' :lime_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Clarifier)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Clarifier)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Mud', 'components' : ['Waste', 'Water'], 'composition' : [.25, .75], 'mass_flow_rate' :mud_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out_mud},
           {'name' : 'Clarified Sugar', 'components' : ['Sugar', 'Water'], 'composition' : [sugar_wt, water_out_wt], 'mass_flow_rate': sugar_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out_sugar}]
Unit7.calculations = {'Sugar to Clarifier': Clarification_func}
    
# Unit 8: Decolorization
Unit8 = Unit('Decolorization')
Unit8.expected_flows_in = ['Clarified Sugar', 'Adsorbent']
Unit8.expected_flows_out = ['Used Adsorbent', 'Clear Sugar']
Unit8.coefficients = {'Adsorbent Ratio': 0.10}

def Decolorization_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    adsorbent_in = sugar_in * coeff['Adsorbent Ratio']
    print('Unit 8')
    return[{'name' : 'Clean Sugar', 'components' : ['Sugar', 'Water'], 'composition' : sugar_flow.attributes['composition'], 'mass_flow_rate': sugar_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': 80, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'Adsorbent', 'components' : ['GAC'], 'composition' : [1], 'mass_flow_rate': adsorbent_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Used Adsorbent', 'components' : ['GAC'], 'composition' : [1], 'mass_flow_rate': adsorbent_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Clarified Sugar': Decolorization_func}
    
# Unit 9: Heater
Unit9 = Unit('Heater')
Unit9.expected_flows_in = ['Clean Sugar', 'Steam (Heater)']
Unit9.expected_flows_out = ['Hot Sugar', 'Condensate (Heater)']
Unit9.coefficients = {'Steam Temp': 120, 'Unit Temp': 115, 'loses':0.1}

def Heater_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    C_p = 2.8
    Q_out = sugar_in * C_p * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 9')
    return[{'name' : 'Steam (Heater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Heater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Hot Sugar', 'components' : ['Sugar', 'Water'], 'composition' : sugar_flow.attributes['composition'], 'mass_flow_rate': sugar_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit9.calculations = {'Clean Sugar': Heater_func}
           
# Unit 10: Evaporators - does this evaporate everything
Unit10 = Unit('Evaporators')
Unit10.expected_flows_in = ['Hot Sugar', 'Steam (Evaporators)']
Unit10.expected_flows_out = ['Rock Sugar', 'Condensate (Evaporators)']
Unit10.coefficients = {'Effect': 2.5, 'Steam Temp': 120, 'Unit Temp': 100}

def Evaporators_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    water_in = sugar_in * (sugar_flow.attributes['composition'][sugar_flow.attributes['components'].index('Water')])
    m_steam = water_in / coeff['Effect']
    Q_steam = m_steam * Hvap
    Q_in = sugar_flow.attributes['heat_flow_rate']
    print('Unit 10')
    breakpoint()
    return[{'name' : 'Steam (Evaporators)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam+water_in,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Rock Sugar', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate': (sugar_in-water_in),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit10.calculations = {'Hot Sugar': Evaporators_func}

# Unit 11: Vacuum Pans - what is happening here
Unit11 = Unit('Vacuum Pans')
Unit11.expected_flows_in = ['Rock Sugar', 'Hot Water (Vacuum Pans)']
Unit11.expected_flows_out = ['Massecuite']
Unit11.coefficients = {'Unit Temp': 60, 'Water to Sugar': 0.5 }

def Vacuum_pans_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    water_in = coeff['Water to Sugar'] * sugar_in
    unit_temp = coeff['Unit Temp']
    print('Unit 11')
    return[{'name' : 'Massecuite', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate': (sugar_in + water_in),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
            {'name' : 'Hot Water (Vacuum Pans)', 'components' : 'Water', 'mass_flow_rate' : water_in,
             'flow_type': 'Steam', 'temperature': unit_temp, 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit11.calculations = {'Rock Sugar': Vacuum_pans_func}
           
# Unit 12: Centrifuge 2 - What is happening here
Unit12 = Unit('Centrifuge 2')
Unit12.expected_flows_in = ['Massecuite', 'Electricity (Centrifuge 2)']
Unit12.expected_flows_out = ['Processed Massecuite']
Unit12.coefficients = {'Electricity (kw/kg)': 0.0000}

def Centrifuge_two_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    electricity_in = sugar_in * coeff['Electricity (kw/kg)']
    Q_in = sugar_flow.attributes['heat_flow_rate'] 
    print('Unit 12')
    return[{'name' : 'Processed Massecuite', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate': sugar_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'Electricity (Centrifuge 2)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit12.calculations = {'Massecuite': Centrifuge_two_func}
           
# Unit 13: Water Wash - Is this where sweet water comes from...
Unit13 = Unit('Water Wash')
Unit13.expected_flows_in = ['Processed Massecuite', 'Warm Water (Water Wash)']
Unit13.expected_flows_out = ['Sweet Water', 'Cleaned Sugar']
Unit13.coefficients = {'Water to Sugar': (601.9/7000), 'Molasses Removed': 0.015, 'Water Temp': 60, 'C_psweetwater':4.000}

def Water_wash_func(sugar_flow, coeff):
    sugar_in = sugar_flow.attributes['mass_flow_rate']
    Q_in = sugar_flow.attributes['heat_flow_rate']
    water_out = coeff['Water to Sugar'] * sugar_input
    sugar_out = sugar_in * (1- coeff['Molasses Removed'])
    water_in = (water_out + sugar_out) - sugar_in
    Q_sweetwater = water_out * coeff['C_psweetwater'] * (coeff['Water Temp'] - ambient_t)
    Q_water_in = water_in * C_pw * (coeff['Water Temp'] - ambient_t)
    Q_out = sugar_in * C_psugar * (coeff['Water Temp'] - ambient_t)
    Q_loss = Q_in + Q_water_in - Q_sweetwater - Q_out
    print('Unit 13')
    
    return[{'name' : 'Warm Water (Water Wash)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': water_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_water_in},
           {'name' : 'Sweet Water', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': water_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_sweetwater, 'Set shear': True},
           {'name' : 'Cleaned Sugar', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate': sugar_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'Heat loss': Q_loss}]
Unit13.calculations = {'Processed Massecuite': Water_wash_func}
           
# Unit 14: Refined Sugar Drying
Unit14 = Unit('Refined Sugar Drying')
Unit14.expected_flows_in = ['Steam (Sugar Drying)', 'Cleaned Sugar']
Unit14.expected_flows_out = ['Condensate (Sugar Drying)', 'Product Sugar']
Unit14.coefficients = {'Steam Temp': 110, 'Unit Temp': 75, 'loses': 0.10, 'inlet water wt': 0.005, 'outlet water wt': 0.0003}

def Refined_sugar_dryer_func(sugar_flow, coeff):
    pure_sugar_in = (sugar_flow.attributes['mass_flow_rate']) * (1- coeff['inlet water wt'])
    Q_in = sugar_flow.attributes['heat_flow_rate']
    product_sugar_out = pure_sugar_in / (1-coeff['outlet water wt'])
    water_evap = (sugar_flow.attributes['mass_flow_rate']) - product_sugar_out
    Q_water_evap = water_evap * (((100 - ambient_t) * C_pw) + Hvap)
    Q_sugar = C_psugar * product_sugar_out * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_sugar - Q_in)/ (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 14')
    return[{'name' : 'Steam (Sugar Drying)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Sugar Drying)', 'components' : 'Water', 'mass_flow_rate' : m_steam+water_evap,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water_evap},
           {'Heat loss': Q_loss},
           {'name' : 'Product Sugar', 'components' : ['Sugar'], 'composition' : [1], 'mass_flow_rate': product_sugar_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_sugar}]
Unit14.calculations = {'Cleaned Sugar': Refined_sugar_dryer_func}
    
# Skip unit 15: because we will assume everything just cools in the air

# Unit 16: Screens and 16 for now

########################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8,
                Unit9, Unit10, Unit11, Unit12, Unit13, Unit14]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    print(flow)

utilities_recap('heat_intensity_cane_sugar_2', allflows, processunits)


