# -*- coding: utf-8 -*-
"""
Created on Friday July 25th 12:04:34 2025

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
C_pnaphtha = 2.3
C_pc2h4 = 1.53
C_pc3h6 = 1.67
C_pbutenes = 1.65
C_pbtx = 1.70
C_ph2 = 14.30
C_pch4 = 2.22
C_pfueloil = 2.1
C_pgasoil = 2.0
C_pcoke = 0.71
yield_ethylene = .32


# Some kind of if statements above where if the flow is named something, its chemical properies can be specified above
mass_in = 10000
mass_ethylene = yield_ethylene * mass_in 
components_in = ['Naphtha']
composition_in = [1]

############################################### Units ########################################################
# Unit 1: Feed Preheat
Unit1 = Unit('Feed Preheater')
Unit1.expected_flows_in = ['Feed', 'Steam (Feed Preheater)']
Unit1.expected_flows_out = ['Preheated Feed', 'Condensate (Feed Preheater)']
Unit1.coefficients = {'loses': .10, 'Unit Temp': 250., 'Steam Temp': 260}

def Feed_preheater_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    c_p = C_pnaphtha 
    Q_out = feed_in * c_p * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 1')
    return[{'name' : 'Steam (Feed Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Feed Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Preheated Feed', 'components' : feed_flow.attributes['components'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
    

Unit1.calculations = {'Feed': Feed_preheater_func}
FlowA = Flow(name = 'Feed', components = components_in, composition = composition_in , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Steam Cracking - Steam now needs to include temperature above vaporization
# What is the temp and pressure of the super heated steam 
Unit2 = Unit('Steam Cracking')
Unit2.expected_flows_in = ['Super Heated Steam (Steam Cracking)', 'Preheated Feed', 'Fuel (Steam Cracking)', 'Air (Steam Cracking)']
Unit2.expected_flows_out = ['Cracked Gas Mixture', 'Exhaust (Steam Cracking)', 'Coke']
Unit2.coefficients = {'Unit Temp': 850., 'loses': .10, 'Cracking Split': [.32, .15, .10, .10, .04, .08, .06, .10, .05], 'Steam Temp': 177, 'Steam Demand (kJ/kg)': 1182,
                      'Steam Pressure': 1, 'Fuel Demand (kj/kg)': 20119, 'Fuel HHV': 5200, 'Air Ratio': 3, 'Exhaust Temp': 900}

def Steam_cracking_unit(feed_flow, coeff):
    Q_in = feed_flow.attributes['heat_flow_rate']
    feed_in = feed_flow.attributes['mass_flow_rate']

    c_p = (coeff['Cracking Split'][0] * C_pc2h4 + coeff['Cracking Split'][1] * C_pc3h6 + coeff['Cracking Split'][2] * C_pbutenes + coeff['Cracking Split'][3] * C_pbtx +
           coeff['Cracking Split'][4] * C_ph2 + coeff['Cracking Split'][5] * C_pch4 + coeff['Cracking Split'][6] * C_pfueloil + coeff['Cracking Split'][7] * C_pgasoil + coeff['Cracking Split'][8] * C_pcoke)
    
    Q_fuel = mass_ethylene * coeff['Fuel Demand (kj/kg)']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    air_in = m_fuel * coeff['Air Ratio']
    Q_air = air_in * C_pair * (coeff['Exhaust Temp'] - ambient_t)
    Q_steam = (coeff['Steam Demand (kJ/kg)'] * mass_ethylene)
    Q_loss = (Q_steam + Q_fuel) * coeff['loses']
    Q_out = Q_steam + Q_fuel + Q_in - Q_air - Q_loss
    m_steam = (Q_steam / ((C_pw * (coeff['Steam Temp'] - ambient_t)) + Hvap))
    coke_out = feed_in * coeff['Cracking Split'][8]
    feed_out = feed_in - coke_out
    composition_minus_coke = coeff['Cracking Split'][:-1]
    constant = (feed_out / (feed_out + m_steam))
    new_composition = [x * constant for x in composition_minus_coke]
    new_composition.append(1-sum(new_composition))
    print('Unit 2')
    return[{'name' : 'Super Heated Steam (Steam Cracking)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'pressure': coeff['Steam Pressure'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'Heat loss': Q_loss},
           {'name' : 'Cracked Gas Mixture', 'components' : ['C2H4', 'C3H6', 'Butenes', 'BTX', 'H2', 'CH4', 'Fuel Oil', 'Gas Oil', 'Water'], 'composition' : new_composition, 'mass_flow_rate' : feed_out+m_steam,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
           {'name' : 'Fuel (Steam Cracking)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Air (Steam Cracking)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
           {'name' : 'Exhaust (Steam Cracking)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in+m_fuel,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Exhaust Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_air}, 
           {'name' : 'Coke', 'components' : ['Coke'], 'composition' : [1], 'mass_flow_rate' : coke_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Preheated Feed': Steam_cracking_unit}

# Does the steam stay entrained in the gas mixture

# Unit 3: Quench - Reminder, check on the pressure units... added a removed water stream here
Unit3 = Unit('Quench')
Unit3.expected_flows_in = ['Cracked Gas Mixture', 'Fuel Oil']
Unit3.expected_flows_out = ['Fuel Oil Out', 'Cooled Cracked Gas', 'Condensate (Quench)', 'Heavy Carbon']
Unit3.coefficients = {'Unit Temp': 350., 'C_pquenchoil': 2.0, 'loses': 0.10, 'DelT Quench Oil': 200}

def Quench_tank_func(gas_flow, coeff):
    Q_in = gas_flow.attributes['heat_flow_rate']
    feed_in = gas_flow.attributes['mass_flow_rate']
    c_pout = ((gas_flow.attributes['composition'][gas_flow.attributes['components'].index('C2H4')] * C_pc2h4) + (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('C3H6')] * C_pc3h6) +
              (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Butenes')] * C_pbutenes) + (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('BTX')] * C_pbtx) +
              (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('H2')] * C_ph2) + (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('CH4')] * C_pch4) +
              (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Fuel Oil')] * C_pfueloil) +
              (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Gas Oil')] * C_pgasoil))
    water_out = feed_in * (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Water')])
    heavy_carbon_out = feed_in * (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Gas Oil')] + gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Fuel Oil')])
    feed_out = feed_in - water_out - heavy_carbon_out
    constant = (feed_in / (feed_out))
    composition_minus_heavies = gas_flow.attributes['composition']
    new_composition = [x * constant for x in composition_minus_heavies]
    updated_composition = new_composition[:-3]
    Q_out = c_pout * feed_in * (coeff['Unit Temp'] - ambient_t)
    Q_fuel_oil_out = (Q_in - Q_out)
    m_fuel_oil = Q_fuel_oil_out / (coeff['C_pquenchoil'] * coeff['DelT Quench Oil'])
    Q_loss = Q_fuel_oil_out * coeff['loses']
    Q_oil_out = Q_fuel_oil_out - Q_loss
    print('Unit 3')
    return[{'name' : 'Fuel Oil', 'components' : 'Fuel Oil', 'mass_flow_rate' : m_fuel_oil,
             'flow_type': 'Process Stream', 'temperature': ambient_t, 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Fuel Oil Out', 'components' : 'Fuel Oil', 'mass_flow_rate' : m_fuel_oil,
             'flow_type': 'Process Stream', 'temperature': ambient_t+coeff['DelT Quench Oil'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_oil_out},
           {'name' : 'Cooled Cracked Gas', 'components' : ['C2H4', 'C3H6', 'Butenes', 'BTX', 'H2', 'CH4', 'Fuel Oil', 'Gas Oil', 'Coke'], 'composition' : updated_composition, 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'pressure': 1, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Condensate (Quench)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_out,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'pressure': 1, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Heavy Carbon', 'components' : ['Fuel Oil'], 'mass_flow_rate' : heavy_carbon_out,
             'flow_type': 'Process Stream', 'temperature': ambient_t+coeff['DelT Quench Oil'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit3.calculations = {'Cracked Gas Mixture': Quench_tank_func}

# Unit 10: Heavy Seperations 
Unit10 = Unit('Heavy Seperator')
Unit10.expected_flows_in = ['Heavy Carbon', 'Steam (Heavy Seperator)']
Unit10.expected_flows_out = ['Product Fuel Oil', 'Condensate (Heavy Seperator)']
Unit10.coefficients = {'Steam Demand (kJ/kg)': 1570, 'Steam Temp': 149}

def Heavy_seperator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = coeff['Steam Demand (kJ/kg)'] * mass_ethylene
    m_steam = Q_steam / Hvap
    Q_out = Q_in + Q_steam
    print('Unit 10')
    return[{'name' : 'Product Fuel Oil', 'components' : ['Fuel Oil'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'temperature': ambient_t, 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'name' : 'Steam (Heavy Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Heavy Seperator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit10.calculations = {'Heavy Carbon': Heavy_seperator_func}
    
# Unit 4: Multi-Stage Gas Compression - Assume Acetyelene Removal Occurs here
Unit4 = Unit('Multi-Stage Gas Compression')
Unit4.expected_flows_in = ['Cooled Cracked Gas', 'Electricity (Compression)', 'Steam (Acetylene Removal)']
Unit4.expected_flows_out = ['Compressed Cracked Gas', 'Waste Heat (Compression)', 'Condensate (Acetylene Removal)']
Unit4.coefficients = {'Electricity (kw/kg)': 0.1, 'T_out': 45, 'C_pout': 2.5, 'P_out': 25, 'Steam Demand (kJ/kg)': 588, 'Steam Temp': 121, 'loses': 0.10}

def Multi_stage_gas_compressor_func(gas_flow, coeff):
    feed_in = gas_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = gas_flow.attributes['heat_flow_rate']
    Q_steam = mass_ethylene * coeff['Steam Demand (kJ/kg)']
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss
    print('Unit 4')
    return[{'name' : 'Electricity (Compression)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
           {'name' : 'Compressed Cracked Gas', 'components' : gas_flow.attributes['components'], 'composition' : gas_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Waste Heat (Compression)', 'components' : None, 'composition' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Waste Heat', 'elec_flow_rate' : 0, 'temperature': ((gas_flow.attributes['temperature'] + coeff['T_out'])/2), 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss},
           {'name' : 'Steam (Acetylene Removal)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (HAcetylene Removal)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit4.calculations = {'Cooled Cracked Gas': Multi_stage_gas_compressor_func}

# Unit 5: Cryogenic Separation - what is going into this and what temp and everything, can we refine these coefficients 
Unit5 = Unit('Cryogenic Separation')
Unit5.expected_flows_in = ['Compressed Cracked Gas']
Unit5.expected_flows_out = ['Product Stream 1', 'Methane', 'Hydrogen']
Unit5.coefficients = {'T_out': 20, 'P_out': 20}

def Cryogenic_seperator_func(gas_flow, coeff):
    Q_loss = gas_flow.attributes['heat_flow_rate']
    feed_in = gas_flow.attributes['mass_flow_rate']
    methane_out = (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('CH4')]) * feed_in
    h2_out = (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('H2')]) * feed_in
    feed_out = feed_in - methane_out - h2_out
    print('Unit 5')
    return[{'name' : 'Product Stream 1', 'components' : ['C2H4', 'C3H6', 'Butenes', 'BTX'], 'composition' : [.412,.235,.118,.235], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Methane', 'components' : ['CH4'], 'composition' : [1], 'mass_flow_rate' : methane_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Hydrogen', 'components' : ['H2'], 'composition' : [1], 'mass_flow_rate' : h2_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit5.calculations = {'Compressed Cracked Gas': Cryogenic_seperator_func}

# Unit 11: Flare 
Unit11 = Unit('Flare')
Unit11.required_calc_flows = 2 
Unit11.expected_flows_in = ['Methane', 'Hydrogen']
Unit11.expected_flows_out = ['Flare Gas']
Unit11.coefficients = {}

def Flare_func(ablist, coeff): 
    h2_flow = ablist[0]
    ch4_flow = ablist[1]
    mass_in = h2_flow.attributes['mass_flow_rate'] + ch4_flow.attributes['mass_flow_rate']
    print('Unit 11')
    return[{'name' : 'Flare Gas', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : mass_in,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0,  'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit11.calculations = (['Methane', 'Hydrogen'], Flare_func)

# Unit 7: Deethanizer - all of the gas compositions are static 
Unit7 = Unit('Deethanizer')
Unit7.expected_flows_in = ['Product Stream 1']
Unit7.expected_flows_out = ['Product Stream 2', 'Ethylene']
Unit7.coefficients = {'T_out': 0.0, 'P_out': 0.0}

def Deethanizer_func(gas_flow, coeff):
    feed_in = gas_flow.attributes['mass_flow_rate']
    ethane_out = (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('C2H4')]) * feed_in
    feed_out = feed_in - ethane_out
    print('Unit 7')
    return[{'name' : 'Ethylene', 'components' : ['C2H4'], 'composition' : [1], 'mass_flow_rate' : ethane_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Product Stream 2', 'components' : ['C3H6', 'Butenes', 'BTX'], 'composition' : [.4,.2,.4], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit7.calculations = {'Product Stream 1': Deethanizer_func}

# Unit 8: Depropanizer
Unit8 = Unit('Depropanizer')
Unit8.expected_flows_in = ['Product Stream 2']
Unit8.expected_flows_out = ['Product Stream 3', 'Propylene']
Unit8.coefficients = {'T_out': 0, 'P_out': 0}

def Depropanizer_func(gas_flow, coeff):
    feed_in = gas_flow.attributes['mass_flow_rate']
    propane_out = (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('C3H6')]) * feed_in
    feed_out = feed_in - propane_out
    print('Unit 8')
    return[{'name' : 'Propylene', 'components' : ['C3H6'], 'composition' : [1], 'mass_flow_rate' : propane_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Product Stream 3', 'components' : ['Butenes', 'BTX'], 'composition' : [.33,.67], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit8.calculations = {'Product Stream 2': Depropanizer_func}

# Unit 9: Pygas Recovery
Unit9 = Unit('Pygas Recovery')
Unit9.expected_flows_in = ['Product Stream 3']
Unit9.expected_flows_out = ['Butenes', 'BTX']
Unit9.coefficients = {'T_out': 0, 'P_out': 0}

def Pygas_recovery_func(gas_flow, coeff):
    feed_in = gas_flow.attributes['mass_flow_rate']
    butenes_out = (gas_flow.attributes['composition'][gas_flow.attributes['components'].index('Butenes')]) * feed_in
    feed_out = feed_in - butenes_out
    print('Unit 9')
    return[{'name' : 'Butenes', 'components' : ['Butenes'], 'composition' : [1], 'mass_flow_rate' : butenes_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'BTX', 'components' : ['BTX'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': coeff['T_out'], 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Product Stream 3': Pygas_recovery_func}

#####################################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit7, Unit8, Unit9, 
                Unit10, Unit11]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

#utilities_recap('heat_intensity_petrochemicals_6', allflows, processunits)






