'''
Name: Aidan J ONeil 
Date: August 8th, 2025 


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
feed_amount = 1000
C_pw = 4.186
Hvap = 2257
C_pair = 1.000
high_pressure_recycle = (221.0/100) * feed_amount 
low_pressure_recycle = (2.18/100) * feed_amount
C_pethylene = 1.5048

######################################################### UNITS #################################################################################
# Unit 1: Feed Mixer  
Unit1 = Unit('Feed Mixer')
Unit1.expected_flows_in = ['Feed', 'Cooled Low Pressure Ethylene']
Unit1.expected_flows_out = ['Reaction Feed 1']
Unit1.coefficients = {}

def Feed_mixer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate'] 
    recycle_in  = low_pressure_recycle
    mass_in = feed_in + recycle_in
    # Heat Balance
    print('Unit 1')
    return[{'name' : 'Reaction Feed 1', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : mass_in,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':1 , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':1}, 
            {'name' : 'Cooled Low Pressure Ethylene', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : low_pressure_recycle,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':1 , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : True, 'heat_flow_rate':1}]

Unit1.calculations = {'Feed': Feed_mixer_func}
FlowA = Flow(name='Feed', components = ['Feed'], composition = [1], flow_type = 'input', mass_flow_rate = feed_amount)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Compressor - Check this pressure out
Unit2 = Unit('Feed Compressor')
Unit2.expected_flows_in = ['Reaction Feed 1', 'Electricity (Feed Compressor)']
Unit2.expected_flows_out = ['Compressed Feed 2']
Unit2.coefficients = {'Electricity (kw/kg)': 0.000}

def Feed_compressor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    p_in = feed_flow.attributes['pressure']
    p_out = 1600
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 2')
    return[{'name' : 'Compressed Feed 2', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':p_out , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':Q_in},
            {'name' : 'Electricity (Feed Compressor)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Reaction Feed 1': Feed_compressor_func}

# Unit 3: Recycle Mixer - Update iniators need
Unit3 = Unit('Recycle Mixer')
Unit3.expected_flows_in = ['Initiators', 'Compressed Feed 2', 'Cooled High Pressure Ethylene']
Unit3.expected_flows_out = ['Reaction Feed 3']
Unit3.coefficients = {'Initiators Ratio': 0.01}

def Recycle_mixer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    recycle_in = high_pressure_recycle
    mass_in = recycle_in + feed_in
    initiators_in = mass_in * coeff['Initiators Ratio']
    mass_out = mass_in + initiators_in 
    p_in = feed_flow.attributes['pressure']
    print('Unit 3')
    return[{'name' : 'Initiators', 'components' : ['Initiator'], 'composition' : [1], 'mass_flow_rate' : initiators_in,
            'flow_type': 'Process flow', 'pressure':p_in , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':-2}, 
            {'name' : 'Reaction Feed 3', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : mass_out,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':1 , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':0}, 
            {'name' : 'Cooled High Pressure Ethylene', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : high_pressure_recycle,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':1 , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : True, 'heat_flow_rate':1}]
Unit3.calculations = {'Compressed Feed 2': Recycle_mixer_func}

# Unit 4: Compressor 2 
Unit4 = Unit('Compressor 2')
Unit4.expected_flows_in = ['Reaction Feed 3', 'Electricity (Compressor 2)']
Unit4.expected_flows_out = ['Compressed Feed 4']
Unit4.coefficients = {'Electricity (kw/kg)': 0.0000}

def Compressor_two_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    p_in = feed_flow.attributes['pressure']
    p_out = 3200
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 4')
    return[{'name' : 'Compressed Feed 4', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':p_out , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':0},
            {'name' : 'Electricity (Compressor 2)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit4.calculations = {'Reaction Feed 3': Compressor_two_func}

# Unit 6: Preheater - Look into the heat demand 
Unit6 = Unit('Pre-Heater')
Unit6.expected_flows_in = ['Compressed Feed 4', 'Comonomer', 'Steam (Preheater)']
Unit6.expected_flows_out = ['Hot Feed 5', 'Condensate (Preheater)']
Unit6.coefficients = {'Unit Temp': 70, 'Steam Temp': 100, 'loses': 0.100, 'Comonomer Ratio': 0.01}

def Pre_heater_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    comonomer_in = coeff['Comonomer Ratio'] * feed_in
    feed_out = feed_in + comonomer_in
    # Q
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pethylene * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    
    print('Unit 6')
    return[{'name' : 'Hot Feed 5', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure':feed_flow.attributes['pressure'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':Q_out},
           {'name' : 'Comonomer', 'components' : ['Initiator'], 'composition' : [1], 'mass_flow_rate' : comonomer_in,
            'flow_type': 'Process flow' , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0},
           {'name' : 'Steam (Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]
Unit6.calculations = {'Compressed Feed 4': Pre_heater_func}

# Unit 7: Reactor 
Unit7 = Unit('Reactor')
Unit7.expected_flows_in = ['Hot Feed 5', 'Oxygen']
Unit7.expected_flows_out = ['Reactor Output', 'Oxygen Out', 'Waste Heat (Reactor)']
Unit7.coefficients = {'Yield': .3, 'Byproduct Yield': 0.1, 'Unit Temp': 100, 'Heat of Rxn': 3.34, 'loses':0.10,
                      'Oxygen Ratio': (.25/39600), 'P_out': 2300}

def Reactor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    oxygen_in = feed_in * coeff['Oxygen Ratio']
    polyethylene_out = feed_in * coeff['Yield']
    byproducts_out = feed_in * coeff['Byproduct Yield']
    ethylene_out = feed_in - polyethylene_out - byproducts_out
    polyethlene_wt = coeff['Yield']
    other_wt = coeff['Byproduct Yield']
    ethylene_wt = 1 - polyethlene_wt - other_wt
    # Q
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_rxn = feed_in * coeff['Heat of Rxn'] * coeff['Yield']
    Q_out = feed_in * C_pethylene * (coeff['Unit Temp'] - ambient_t)
    Q_waste = Q_in + Q_rxn - Q_out
    print('Unit 7')
    return[{'name' : 'Reactor Output', 'components' : ['Ethylene', 'Polyethylene', 'Other'], 'composition' : [ethylene_wt, polyethlene_wt, other_wt], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['P_out'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate': Q_out},
           {'name' : 'Oxygen', 'components' : ['O2'], 'composition' : [1], 'mass_flow_rate' : oxygen_in ,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['P_out'] , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0},
           {'name' : 'Oxygen Out', 'components' : ['O2'], 'composition' : [1], 'mass_flow_rate' : oxygen_in ,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['P_out'] , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0},
           {'name': 'Waste Heat (Reactor)',
            'flow_type': 'Waste Heat', 'temperature': coeff['Unit Temp'], 'In or out': 'Out', 'Set calc': False, 'heat_flow_rate': Q_waste},
           {'Heat of reaction': Q_rxn}]
Unit7.calculations = {'Hot Feed 5': Reactor_func}

# Unit 8: High Pressure Seperator 
Unit8 = Unit('High Pressure Seperator')
Unit8.expected_flows_in = ['Reactor Output', 'Steam (High Pressure Seperator)']
Unit8.expected_flows_out = ['Product Flow 1', 'Ethylene Recycle 1', 'Condensate (High Pressure Seperator)']
Unit8.coefficients = {'Unit Pressure': 2300, 'Unit Temp': 100, 'Seperation': .95, 'Steam Temp': 120}

def High_pressure_seperator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    polyethylene_out = (feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Polyethylene')])) / (coeff['Seperation'])
    recycle_out = feed_in - polyethylene_out
    # Q
    Q_in = feed_flow.attributes['heat_flow_rate']
    H_vap = 492
    Q_vaporization = recycle_out * H_vap
    Q_steam = Q_vaporization
    m_steam = Q_steam / Hvap 
    Q_out_recycle = Q_vaporization + Q_in
    Q_out_prod = 0 
    print('Unit 8')
    return[{'name' : 'Product Flow 1', 'components' : ['Ethylene', 'Polyethylene', 'Other'], 'composition' : [.025, .95, .025], 'mass_flow_rate' : polyethylene_out,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['Unit Pressure'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':Q_out_prod}, 
           {'name' : 'Ethylene Recycle 1', 'components' : ['Ethylene', 'Polyethylene', 'Other'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : recycle_out,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['Unit Pressure'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':Q_out_recycle},
           {'name' : 'Steam (High Pressure Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (High Pressure Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Reactor Output': High_pressure_seperator_func}

# Unit 9: Low Pressure Seperator 
Unit9 = Unit('Low Pressure Seperator')
Unit9.expected_flows_in = ['Product Flow 1', 'Steam (Low Pressure Seperator)']
Unit9.expected_flows_out = ['Ethylene Recycle 2', 'Polyethylene', 'Condensate (Low Pressure Seperator)']
Unit9.coefficients = {'Purity': 0.999, 'Unit Temp': 100, 'Unit Pressure': 1.5, 'Steam Temp': 110}

def Low_pressure_seperator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    polyethylene_out = (feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Polyethylene')])) / (coeff['Purity'])
    recycle_out = feed_in - polyethylene_out
    # Q
    Q_in = feed_flow.attributes['heat_flow_rate']
    H_vap = .4813
    Q_vaporization = recycle_out * H_vap
    Q_steam = Q_vaporization - Q_in
    m_steam = Q_steam / Hvap
    Q_out = Q_vaporization 
    print('Unit 9')
    return[{'name' : 'Polyethylene', 'components' : ['Polyethylene', 'Other'], 'composition' : [coeff['Purity'], 1-coeff['Purity']], 'mass_flow_rate' : polyethylene_out,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['Unit Pressure'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':0}, 
            {'name' : 'Ethylene Recycle 2', 'components' : ['Ethylene', 'Polyethylene', 'Other'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : recycle_out,
            'flow_type': 'Process flow', 'temperature' : coeff['Unit Temp'], 'pressure': coeff['Unit Pressure'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False, 'heat_flow_rate':Q_vaporization},
           {'name' : 'Steam (Low Pressure Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Low Pressure Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Product Flow 1': Low_pressure_seperator_func}

# Unit 12: Pelletizing/Dryer
Unit12 = Unit('Pelletizer')
Unit12.expected_flows_in = ['Polyethylene']
Unit12.expected_flows_out = ['Pellets']
Unit12.coefficients = {'Unit Temp': 100, }

def Pelletizer_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 12')
    return[{'name' : 'Pellets', 'components' : ['Pellets'], 'composition' : [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Product', 'temperature' : coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0}]
Unit12.calculations = {'Polyethylene': Pelletizer_func}     

# Unit 10: Ethylene Cooler (1)
Unit10 = Unit('Ethylene Cooler (1)')
Unit10.expected_flows_in = ['Ethylene Recycle 1', 'Chilling Demand (Cooler 1)']
Unit10.expected_flows_out = ['Cooled High Pressure Ethylene', 'Wax Waste 1']
Unit10.coefficients = {'P_out': 3200, 'T_out': ambient_t}

def Ethylene_cooler_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    ethylene_out = high_pressure_recycle
    waste_out = feed_in - ethylene_out
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = 1
    Q_cooling = Q_out - Q_in
    print('Unit 10')
    return[{'name' : 'Wax Waste 1', 'components' : ['Wax'], 'composition' : [1], 'mass_flow_rate' : waste_out,
            'flow_type': 'Waste', 'temperature' : coeff['T_out'], 'pressure': coeff['P_out'] , 'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0},
           {'name' : 'Cooled High Pressure Ethylene', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : high_pressure_recycle,
            'flow_type': 'Process flow', 'temperature' : coeff['T_out'], 'pressure': coeff['P_out'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : True, 'heat_flow_rate':1},
           {'name' : 'Chilling Demand (Cooler 1)', 'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cooling}]
Unit10.calculations = {'Ethylene Recycle 1': Ethylene_cooler_func}

# Unit 11: Ethylene Cooler (2)
Unit11 = Unit('Ethylene Cooler (2)')
Unit11.expected_flows_in = ['Ethylene Recycle 2', 'Chilling Demand (Cooler 2)']
Unit11.expected_flows_out = ['Cooled Low Pressure Ethylene', 'Wax Waste 2']
Unit11.coefficients = {'P_out': 1.5, 'T_out': ambient_t}

def Ethylene_cooler_2_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    ethylene_out = low_pressure_recycle
    waste_out = feed_in - ethylene_out 
    print('Unit 11')
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = 1
    Q_chilling = Q_out - Q_in 
    return[{'name' : 'Wax Waste 2', 'components' : ['Wax'], 'composition' : [1], 'mass_flow_rate' : waste_out,
            'flow_type': 'Waste', 'temperature' : coeff['T_out'], 'pressure': coeff['P_out'] , 'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False, 'heat_flow_rate':0}, 
            {'name' : 'Cooled Low Pressure Ethylene', 'components' : ['Ethylene'], 'composition' : [1], 'mass_flow_rate' : low_pressure_recycle,
            'flow_type': 'Process flow', 'temperature' : coeff['T_out'], 'pressure': coeff['P_out'] , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : True, 'heat_flow_rate':1},
           {'name' : 'Chilling Demand (Cooler 2)', 'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit11.calculations = {'Ethylene Recycle 2': Ethylene_cooler_2_func}

#################################################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit6, Unit7, Unit8, Unit9, Unit10, Unit11,
                Unit12]

main(allflows, processunits)


for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

    
utilities_recap('heat_intensity_polyethylene_3', allflows, processunits)


for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)
