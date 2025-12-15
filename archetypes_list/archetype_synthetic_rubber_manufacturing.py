'''
Name: Aidan J ONeil 
Date: August 20th, 2025 


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
C_pstyrene = 1.87
C_pbutadiene = 1.47
product_yield = mass_in
C_platex = 2.00


################################################################################# UNITS ###############################################################
# Unit 1: Feed Tank 
Unit1 = Unit('Feed Tank')
Unit1.unit_type = 'Mixer'
Unit1.temperature = ambient_t
Unit1.expected_flows_in = ['Emulsifiers', 'Initiators', 'Monomers', 'Chain Transfer Agents', 'Water (Feed Tank)', 'Electricity (Feed Tank)']
Unit1.expected_flows_out = ['Process Flow 1']
Unit1.coefficients = {'Initiator to Monomer': (53/17857), 'Soap to Monomer': (890/17857), 'Chain to Monomer': (90/17857), 
                      'Water to Monomer': (45915/17857), 'Electricity (kw/kg)': 0.002} 

def Feed_tank_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    emulsifier_in = feed_in * coeff['Soap to Monomer']
    initiator_in = feed_in * coeff['Initiator to Monomer']
    chain_in = feed_in * coeff['Chain to Monomer']
    water_in = feed_in * coeff['Water to Monomer']
    mass_out = feed_in + emulsifier_in + initiator_in + chain_in + water_in 
    water_wt = water_in / mass_out 
    butadiene_wt = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Butadiene')]) / mass_out 
    styrene_wt = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Styrene')]) / mass_out 
    other_wt = 1 - water_wt - butadiene_wt - styrene_wt
    print('Unit 1')
    return[{'name' : 'Process Flow 1', 'components' : ['Water', 'Butadiene', 'Styrene', 'Other'], 'composition' : [water_wt, butadiene_wt, styrene_wt, other_wt], 'mass_flow_rate' : mass_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}, 
            {'name' : 'Electricity (Feed Tank)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
           {'name' : 'Emulsifiers', 'components' : ['Emulsifiers'], 'composition' : [1], 'mass_flow_rate' : emulsifier_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Initiators', 'components' : ['Initiators'], 'composition' : [1], 'mass_flow_rate' : initiator_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Chain Transfer Agents', 'components' : ['Chain Transfer Agents'], 'composition' : [1], 'mass_flow_rate' : chain_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Water (Feed Tank)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
    

Unit1.calculations = {'Monomers': Feed_tank_func}
FlowA = Flow(name = 'Monomers', components = ['Butadiene', 'Styrene'], composition = [.75,.25] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 10: Polymerization Preheater
Unit10 = Unit('Polymerization Preheater')
Unit10.temperature = 50 
Unit10.unit_type = 'Heater'
Unit10.expected_flows_in = ['Recycle Butadiene', 'Recycle Styrene', 'Process Flow 1', 'Steam (Preheater)'] 
Unit10.expected_flows_out = ['Process Stream 2', 'Condensate (Preheater)']
Unit10.coefficients = {'Unit Temp': 50, 'loses': 0.10, 'Steam Temp': 100, 
                       'Butadiene to Mass In': (5735/ 10000 ), 'Styrene to Mass In': (1916/10000 )}

def Polymerization_preheater_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    recycle_butadiene_in = mass_in * coeff['Butadiene to Mass In']
    recycle_styrene_in = mass_in * coeff['Styrene to Mass In']
    mass_out = feed_in + recycle_butadiene_in + recycle_styrene_in
    butadiene_in = recycle_butadiene_in + (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Butadiene')])
    styrene_in = recycle_styrene_in + (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Styrene')])
    water_in = mass_out - butadiene_in - styrene_in
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_wt = water_in / mass_out
    butadiene_wt = butadiene_in/mass_out
    styrene_wt = styrene_in/mass_out
    other_wt = 1 - water_wt - butadiene_wt - styrene_wt
    C_p = (C_pw * water_wt) + (C_pbutadiene * butadiene_wt) + (C_pstyrene * styrene_wt)
    Q_out = C_p * mass_out * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 10')
    return[{'name' : 'Steam (Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Process Flow 2', 'components' : ['Water', 'Butadiene', 'Styrene', 'Other'], 'composition' : [water_wt, butadiene_wt, styrene_wt, other_wt], 'mass_flow_rate' : mass_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Recycle Styrene', 'components' : ['Styrene'], 'composition' : [1], 'mass_flow_rate' : recycle_styrene_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 1},
           {'name' : 'Recycle Butadiene', 'components' : ['Butadiene'], 'composition' : [1], 'mass_flow_rate' : recycle_butadiene_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 1}]
Unit10.calculations = {'Process Flow 1': Polymerization_preheater_func}

# Unit 2: Polymerization Reactor
Unit2 = Unit('Polymerization Reactor')
Unit2.temperature = 50
Unit2.unit_type = 'Reactor'
Unit2.expected_flows_in = ['Process Flow 2', 'Electricity (Reactor)']
Unit2.expected_flows_out = ['Process Flow 3', 'Wasteheat (Reactor)']
Unit2.coefficients = {'Conversion': .7, 'Heat of Polymerization': 71.5, 'Electricity (kw/kg)':0.02}

def Reactor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_in = feed_in *  feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')]
    butadiene_in = feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Butadiene')]
    styrene_in = feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Styrene')]
    latex_out = (butadiene_in + styrene_in) * coeff['Conversion']
    butadiene_out = butadiene_in * (1-coeff['Conversion'])
    styrene_out = styrene_in * (1-coeff['Conversion'])
    latex_wt = latex_out / feed_in 
    styrene_wt = styrene_out/ feed_in 
    butadiene_wt = butadiene_out / feed_in 
    water_wt = water_in / feed_in
    other_wt = 1 - latex_wt - styrene_wt - butadiene_wt - water_wt 
    composition = [latex_wt, styrene_wt, butadiene_wt, water_wt, other_wt]
    print('Unit 2')
    Q_waste = (butadiene_in * coeff['Conversion'] * coeff['Heat of Polymerization'] / 54.09) + (styrene_in * coeff['Conversion'] * coeff['Heat of Polymerization'] / 104.05)
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    return[{'name' : 'Electricity (Reactor)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
           {'name' : 'Process Flow 3', 'components' : ['Latex', 'Styrene', 'Butadiene', 'Water', 'Other'], 'composition' : composition, 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': 50, 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_in},
           {'name' : 'Wasteheat (Reactor)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Wasteheat', 'temperature' : 50,  'In or out' : 'Out', 'elec_flow_rate' : 0, 'heat_flow_rate':Q_waste},
           {'Heat of reaction': Q_waste}]
Unit2.calculations = {'Process Flow 2': Reactor_func}

# Unit 3: Shortstopping - How viscous is this fluid???
Unit3 = Unit('Shortstopping')
Unit3.unit_type = 'Mixer'
Unit3.temperature = 60
Unit3.expected_flows_in = ['Process Flow 3', 'Electricity (Shortstopping)', 'Inhibitors']
Unit3.expected_flows_out = ['Process Flow 4']
Unit3.coefficients = {'Electricity (kw/kg)': .002, 'Inhibitors Ratio': 0.000}

def Shortstopping_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    inhibitors_in = feed_in * coeff['Inhibitors Ratio']
    print('Unit 3')
    return[{'name' : 'Electricity (Shortstopping)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'name' : 'Process Flow 4', 'components' : ['Latex', 'Styrene', 'Butadiene', 'Water', 'Other'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': 60, 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_in}, 
             {'name' : 'Inhibitors', 'components' : ['Inhibitors'], 'composition' : [1], 'mass_flow_rate' : inhibitors_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit3.calculations = {'Process Flow 3': Shortstopping_func}

# Unit 4: Vacuum Distillation 
Unit4 = Unit('Vacuum Distillation')
Unit4.temperature = 70 
Unit4.unit_type = 'Seperator'
Unit4.expected_flows_in = ['Process Flow 4', 'Steam (Vacuum Distillation)']
Unit4.expected_flows_out = ['Process Flow 5', 'Recycle Butadiene', 'Condensate (Vacuum Distillation)', 'Purge (Vacuum Distillation)']
Unit4.coefficients = {'Butadiene to Mass In': (5735/ 17857 ), 'Unit Temp': 70, 'Steam Temp': 100, 'loses':0.10, 'Steam demand (kg/kg)': 0.08}

def Vacuum_distillation_func(feed_flow, coeff): 
    m_steam = coeff['Steam demand (kg/kg)'] *  mass_in
    Q_steam = (m_steam * Hvap) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    butadiene_recycle_out = mass_in * coeff['Butadiene to Mass In']
    butadiene_in = ((feed_flow.attributes['mass_flow_rate']) * 
                    feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Butadiene')])
    butadiene_purge = butadiene_in - butadiene_recycle_out
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_steam - Q_loss  
    feed_in = feed_flow.attributes['mass_flow_rate']
    feed_out = feed_in - butadiene_purge - butadiene_recycle_out
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    styrene_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Styrene')])
    latex_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Latex')])
    water_wt = water_in / feed_out 
    styrene_wt = styrene_in / feed_out 
    latex_wt = latex_in / feed_out 
    other_wt = 1 - water_wt - styrene_wt - latex_wt 
    compositions = [water_wt, styrene_wt, latex_wt, other_wt]
    print('Unit 4')
    return[{'name' : 'Steam (Vacuum Distillation)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Vacuum Distillation)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss + Q_in}, 
             {'name' : 'Process Flow 5', 'components' : ['Water','Styrene','Latex','Other'], 'composition' : compositions, 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_out}, 
             {'name' : 'Recycle Butadiene', 'components' : ['Butadiene'], 'composition' : [1], 'mass_flow_rate' : butadiene_recycle_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 1}, 
             {'name' : 'Purge (Vacuum Distillation)', 'components' : ['Purge'], 'composition' : [1], 'mass_flow_rate' : butadiene_purge,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit4.calculations = {'Process Flow 4': Vacuum_distillation_func}

# Unit 5: Steam Stripping 
Unit5 = Unit('Steam Stripping')
Unit5.temperature = 95 
Unit5.unit_type = 'Seperator'
Unit5.expected_flows_in = ['Process Flow 5', 'Steam (Steam Stripping)']
Unit5.expected_flows_out = ['Process Flow 6', 'Condensate (Steam Stripping)', 'Recycle Styrene', 'Purge (Steam Stripping)']
Unit5.coefficients = {'Styrene to Mass In': (1916/17857), 'Unit Temp': 95, 'Steam Demand (kg/kg)': 0.74, 'Steam Temp': 100, 'loses':0.1}

def Steam_stripping_func(feed_flow, coeff): 
    m_steam = coeff['Steam Demand (kg/kg)'] * mass_in 
    Q_steam = (m_steam * Hvap) / (1-coeff['loses'])
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss 
    feed_in = feed_flow.attributes['mass_flow_rate']
    styrene_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Styrene')])
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    latex_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Latex')])
    feed_out = feed_in - styrene_in
    water_wt = water_in / feed_out 
    latex_wt = latex_in / feed_out 
    other_wt = 1 - water_wt - latex_wt 
    styrene_recycle_out = mass_in * coeff['Styrene to Mass In']
    styrene_purge = styrene_in - styrene_recycle_out
    compositions = [water_wt, latex_wt, other_wt]
    print('Unit 5')
    return[{'name' : 'Steam (Steam Stripping)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Steam Stripping)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Process Flow 6', 'components' : ['Water','Latex','Other'], 'composition' : compositions, 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_out}, 
             {'name' : 'Recycle Styrene', 'components' : ['Styrene'], 'composition' : [1], 'mass_flow_rate' : styrene_recycle_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': 1}, 
             {'name' : 'Purge (Steam Stripping)', 'components' : ['Purge'], 'composition' : [1], 'mass_flow_rate' : styrene_purge,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit5.calculations = {'Process Flow 5': Steam_stripping_func}

# Unit 6: Coagulation 
Unit6 = Unit('Coagulation')
Unit6.temperature = 50 
Unit6.unit_type = 'Seperator'
Unit6.expected_flows_in = ['Process Flow 6', 'Electricity (Coagulation)', 'Coagulation Agents']
Unit6.expected_flows_out = ['Rubber Crumbs', 'Coagulation Liquor', 'Wasteheat (Coagulation)']
Unit6.coefficients = {'Electricity (kw/kg)': 0.002, 'Water Split to Crumbs': (637/2550), 'Unit Temp': 50, 'Coagulation Ratio': 0.000}

def Coagulation_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    latex_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Latex')])
    water_to_crumbs = water_in * coeff['Water Split to Crumbs']
    crumbs_out = water_to_crumbs + latex_in 
    liquor_out = feed_in - crumbs_out 
    water_wt = water_to_crumbs / crumbs_out
    latex_wt = latex_in / crumbs_out
    comp = [water_wt, latex_wt]
    C_p = (water_wt * C_pw) + (latex_wt * C_platex)
    Q_out = C_p * crumbs_out * (coeff['Unit Temp'] - ambient_t)
    Q_waste = Q_in - Q_out 
    electricity_in = coeff['Electricity (kw/kg)'] * mass_in 
    print('Unit 6')
    
    return[{'name' : 'Electricity (Coagulation)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'name' : 'Wasteheat (Coagulation)', 'components' : None, 'heat_flow_rate' : Q_waste,
             'flow_type': 'Wasteheat', 'temperature' : 50,  'In or out' : 'Out', 'elec_flow_rate' : 0}, 
             {'name' : 'Coagulation Agents', 'components' : ['Agents'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'In', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}, 
             {'name' : 'Rubber Crumbs', 'components' : ['Water', 'Latex'], 'composition' : comp, 'mass_flow_rate' : crumbs_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_out}, 
             {'name' : 'Coagulation Liquor', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : liquor_out,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit6.calculations = {'Process Flow 6': Coagulation_func}

# Unit 7: Washing 
Unit7 = Unit('Washer')
Unit7.temperature = ambient_t
Unit7.expected_flows_in = ['Water (Washer)', 'Electricity (Washer)', 'Rubber Crumbs']
Unit7.expected_flows_out = ['Hydrated Crumbs', 'Wastewater (Washer)']
Unit7.coefficients = {'Electricity (kw/kg)': 0.075, 'Water to Crumbs': 2, 'heat loss': .50, 'Moisture Increase': .10}

def Washer_func(feed_flow, coeff): 
    electricity_in = coeff['Electricity (kw/kg)'] * mass_in 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_loss = Q_in * coeff['heat loss']
    Q_out = Q_in - Q_loss 
    water_in = feed_in * coeff['Water to Crumbs']
    feed_out = feed_in * (coeff['Moisture Increase'] + 1)
    water_out = feed_in + water_in - feed_out 
    latex_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Latex')])
    latex_wt = latex_in / feed_out 
    print(latex_wt)
    print('Unit 7')
    return[{'name' : 'Electricity (Washer)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
             {'name' : 'Hydrated Crumbs', 'components' : ['Water', 'Latex'], 'composition' : [1-latex_wt, latex_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_out}, 
             {'Heat loss': Q_loss}, 
             {'name' : 'Water (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}, 
             {'name' : 'Wastewater (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_out,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit7.calculations = {'Rubber Crumbs': Washer_func}

# Unit 8: Dryer 
Unit8 = Unit('Dryer')
Unit8.unit_type = 'Dryer'
Unit8.temperature = 90
Unit8.expected_flows_in = ['Steam (Dryer)', 'Hydrated Crumbs', 'Electricity (Dryer)']
Unit8.expected_flows_out = ['Dry Crumbs', 'Condensate (Dryer)', 'Water Vapor (Dryer)']
Unit8.coefficients = {'Outlet wt': 0.005, 'Unit Temp': 90, 'Electricity (kw/kg)': 0.05, 'loses': 0.05, 
                      'Steam Temp': 100}

def Dryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    solids_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Latex')])
    crumbs_out = solids_in / (1-coeff['Outlet wt'])
    water_evap = feed_in - crumbs_out 
    Q_water_evap = (Hvap * water_evap) + (water_evap * C_pw * (coeff['Unit Temp'] - ambient_t))
    Q_latex = C_platex * crumbs_out * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_water_evap + Q_latex - Q_in)/ (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    electricity_in = coeff['Electricity (kw/kg)'] * mass_in 
    print('Unit 8')
    return[{'name' : 'Electricity (Dryer)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
             {'name' : 'Steam (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
             {'name' : 'Condensate (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
             {'Heat loss': Q_loss}, 
             {'name' : 'Water Vapor (Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Wasteheat', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': Q_water_evap}, 
             {'name' : 'Dry Crumbs', 'components' : ['Water','Latex'], 'composition' : [coeff['Outlet wt'], 1-coeff['Outlet wt']], 'mass_flow_rate' : crumbs_out,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'Set shear': False, 'heat_flow_rate': Q_latex}]
Unit8.calculations = {'Hydrated Crumbs': Dryer_func}

# Unit 9: Finishing and Balling 
Unit9 = Unit('Finisher')
Unit9.temperature = ambient_t
Unit9.expected_flows_in = ['Dry Crumbs', 'Electricity (Finisher)']
Unit9.expected_flows_out = ['Product Rubber']
Unit9.coefficients = {'Electricity (kw/kg)': 0.05}

def Finisher_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('UNit 9')
    return[{'name' : 'Electricity (Finisher)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'Heat loss': Q_in}, 
             {'name' : 'Product Rubber', 'components' : ['Rubber'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'Set shear': False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Dry Crumbs': Finisher_func}

#################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, 
                Unit10]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_synthetic_rubber_2', allflows, processunits)

