# -*- coding: utf-8 -*-
"""
Created on Tuesday July 8th 14:04:34 2025

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
gamma_ch4 = 1.35
C_pch4 = 35.70
gamma_air = 1.31
gamma_n2 = 1.470
mass_in = 10000
C_psteam = 1.880
C_ph2 = 14.28
C_pn2 = 1.04
C_pco = 1.04
C_pco2 = .8457
C_pnh3 = 2.096
C_po2 = .9184
Hcondense_nh3 = 332.17
C_phno3 = .942
C_ph2so4 = 1416 

######################################### UNITS #####################################
#
# Unit 1: Adiabatic Compressor - Should work here be negative or positive (see line of code with -1) 
Unit1 = Unit('Compressor One')
Unit1.expected_flows_in = ['Methane', 'Electricity (Methane Compressor)']
Unit1.expected_flows_out = ['Compressed Methane']
Unit1.coefficients = {'Elec efficiency' : .85, 't_in': ambient_t, 't_out': 100, 'P_out': 32.5, 'P_in': 15} # (kJ/kg:70)

def Adiabatic_compressor_func(methane_flow, coeff):
    methane_in = methane_flow.attributes['mass_flow_rate']
    v_1 = (methane_in * 0.08314 * (coeff['t_in'] + 273)) / (16.04 * coeff['P_in'])
    v_2 = (methane_in * 0.08314 * (coeff['t_out'] + 273)) / (16.04 * coeff['P_out'])
    w = ((coeff['P_out'] * v_2) - (coeff['P_in'] * v_1)) / (1 - gamma_ch4) # is it gamma -1 of 1-gamma
    electricity_in = -1 * w / coeff['Elec efficiency']
    print('Unit1')
    return[{'name' : 'Electricity (Methane Compressor)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Compressed Methane', 'components' : ['Methane'], 'composition' : [1], 'mass_flow_rate' : methane_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit1.calculations = {'Methane': Adiabatic_compressor_func}
FlowA = Flow(name = 'Methane', components = ['Methane'], composition = [1], flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)


# Unit 2: Methane Preheater - what is the outlet temperature for the methane? 215 or 375? because there can only be one temp for all the components leaving the
## unit: Changed to combustion energy content so that heat demand is in Q fuel column
Unit2 = Unit('Methane Preheater')
Unit2.expected_flows_in = ['Compressed Methane', 'Air (Methane Preheater)', 'Fuel (Methane Preheater)']
Unit2.expected_flows_out = ['Exhaust (Methane Preheater)', 'Hot Methane']
Unit2.coefficients = {'loses': 0.15, 'Air Ratio': 3, 'Fuel HHV': 5200, 't_out': 375}

def Methane_preheater_func(methane_flow, coeff):
    methane_in = methane_flow.attributes['mass_flow_rate']
    Q_in = methane_flow.attributes['heat_flow_rate']
    Q_methane = methane_in * C_pch4 * (coeff['t_out'] - ambient_t)
    air_in = coeff['Air Ratio'] * methane_in
    Q_air = air_in * C_pair * (coeff['t_out'] - ambient_t)
    Q_fuel = (Q_air + Q_methane - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_fuel * coeff['loses']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    print('Unit 2')
    return[{'name' : 'Air (Methane Preheater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Exhaust (Methane Preheater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in + m_fuel,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_air},
           {'name' : 'Hot Methane','components' : ['Methane'], 'composition' : [1], 'mass_flow_rate' : methane_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_methane},
           {'name' : 'Fuel (Methane Preheater)','components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel,'combustion_energy_content': Q_fuel},
           {'Heat loss': Q_loss}]

Unit2.calculations = {'Compressed Methane': Methane_preheater_func}

# Unit 4: Air Compressor
Unit4 = Unit('Air Compressor')
Unit4.expected_flows_in = ['Air (Compressor)', 'Electricity (Air Compressor)']
Unit4.expected_flows_out = ['Compressed Air']
Unit4.coefficients = {'Elec efficiency' : .85, 't_in': ambient_t, 't_out': 80, 'P_out': 35, 'P_in': 1}

def Air_compressor_func(air_flow, coeff):
    air_in = air_flow.attributes['mass_flow_rate']
    v_1 = (air_in * 0.08314 * (coeff['t_in'] + 273)) / (16.04 * coeff['P_in'])
    v_2 = (air_in * 0.08314 * (coeff['t_out'] + 273)) / (16.04 * coeff['P_out'])
    w = ((coeff['P_out'] * v_2) - (coeff['P_in'] * v_1)) / (1 - gamma_ch4) # is it gamma -1 of 1-gamma
    electricity_in = -1 * w / coeff['Elec efficiency']
    print('Unit 4')
    return[{'name' : 'Electricity (Air Compressor)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Compressed Air', 'components' : ['Nitrogen', 'O2'], 'composition' : [.79, .21], 'mass_flow_rate' : air_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit4.calculations = {'Air (Compressor)': Air_compressor_func}
FlowB = Flow(name = 'Air (Compressor)', components = ['Nitrogen', 'O2'], composition = [.79, .21], flow_type = 'input', mass_flow_rate = 1.6 * mass_in)
FlowB.set_calc_flow()
allflows.append(FlowB)

# Unit 3: Primary Reformer - needs to add a fuel demand on top of the steam demand (where is that heat going)
Unit3 = Unit('Primary Reformer')
Unit3.required_calc_flows = 2 
Unit3.expected_flows_in = ['Compressed Air', 'Air In (Primary Reformer)','Hot Methane', 'Fuel (Primary Reformer)', 'Steam (Primary Reformer)']
Unit3.expected_flows_out = ['Reaction Mix 1', 'Exhaust (Primary Reformer)', 'Air (Primary Reformer)']
Unit3.coefficients = {'loses': 0.15, 'Steam Carbon Ratio': 3.0, 't_out': 815. , 'Heat of Rxn': 206.0, 'Steam temp': 250,
                      'Fuel HHV': 2500, 'Air Ratio': 3.0}

def Primary_reformer_func(ablist, coeff):
    air_flow = ablist[0]
    methane_flow = ablist[1]
    methane_in = methane_flow.attributes['mass_flow_rate']
    Q_methane_in = methane_flow.attributes['heat_flow_rate']
    steam_in = (methane_in / 16.1) * coeff['Steam Carbon Ratio'] * 18.00
    air_in = air_flow.attributes['mass_flow_rate']
    air_out = air_in
    mix_1 = steam_in + methane_in
    Q_steam_in = (steam_in * Hvap) + (steam_in * C_psteam * (coeff['Steam temp'] - 100))
    Q_steam_out = (steam_in * Hvap) + (steam_in * C_psteam * (coeff['t_out'] - 100))
    Q_air_in = air_flow.attributes['heat_flow_rate']
    Q_air_out = C_pair * air_in * (coeff['t_out'] - 80)
    Q_methane_out = methane_in * C_pch4 * (coeff['t_out'] - ambient_t)
    Q_rxn = methane_in * coeff['Heat of Rxn'] / 16.1
    Q_fuel = (Q_rxn + Q_steam_out + Q_air_out + Q_methane_out - Q_steam_in - Q_air_in - Q_methane_in) / (1- coeff['loses'])
    m_fuel = Q_fuel / coeff['Fuel HHV']
    fuel_air_in = m_fuel * coeff['Air Ratio']
    Q_exhaust = Q_fuel * coeff['loses']
    print('Unit3')
    return[{'name' : 'Reaction Mix 1','components' : ['CH4','H20','CO','H2'], 'composition' : [.092, .614, .239, .055], 'mass_flow_rate' : mix_1,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_methane_out+Q_steam_out+Q_rxn},
           {'name' : 'Air (Primary Reformer)', 'components' : ['Nitrogen', 'O2'], 'composition' : [.79, .21], 'mass_flow_rate' : air_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'pressure': 35, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_air_out},
           {'name' : 'Exhaust (Primary Reformer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : fuel_air_in+m_fuel,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_exhaust},
           {'name' : 'Air In (Primary Reformer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : fuel_air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Fuel (Primary Reformer)','components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'combustion_energy_content': Q_fuel, 'heat_flow_rate': Q_fuel},
           {'name' :  'Steam (Primary Reformer)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature':coeff['Steam temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam_in}]

Unit3.calculations = (['Compressed Air', 'Hot Methane'], Primary_reformer_func)

# Unit 5: Secondary Reformer pt 1 - Is there a bunch of heat lose in this unit? Currently, I have it that way
# these are static to the selectivity... so maybe I shouldn't include selectivity as a coeff?
Unit5 = Unit('Secondary Reformer: Combustion')
Unit5.required_calc_flows = 2
Unit5.expected_flows_in = ['Reaction Mix 1', 'Air (Primary Reformer)']
Unit5.expected_flows_out = ['Reaction Mix 2', 'Heat (Secondary Reformer)']
Unit5.coefficients = {'Unit Temp': 1200., 'Selectivity to CO':.5, 'Conversion of O2': 1}

def Secondary_reformer_pt1_func(ablist, coeff):
    air_flow = ablist[1]
    reaction_mix_flow = ablist[0]
    air_in = air_flow.attributes['mass_flow_rate']
    react_mix_in = reaction_mix_flow.attributes['mass_flow_rate']
    react_mix_out = react_mix_in + air_in
    c_pout = (.041 * C_pch4) + (.457 * C_psteam) + (.171 * C_pco) + (.027 * C_ph2) + (.304 * C_pn2)
    Q_out = react_mix_out * c_pout * (coeff['Unit Temp'] - ambient_t)
    Q_air_in = air_flow.attributes['heat_flow_rate']
    Q_mix_in = reaction_mix_flow.attributes['heat_flow_rate']
    Q_rxn_per_mol_o2 = (coeff['Selectivity to CO'] * 520.) + ((1-coeff['Selectivity to CO']) * 242.)
    Q_rxn = (air_in * .21 / 32.00) * Q_rxn_per_mol_o2 * coeff['Conversion of O2']
    Q_heat = Q_mix_in + Q_air_in + Q_rxn - Q_out 
    print('Unit 5')
    return[{'name' : 'Reaction Mix 2','components' : ['CH4','H20','CO','H2', 'N2'], 'composition' : [.041, .457, .171, .027, .304], 'mass_flow_rate' : react_mix_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' :  'Heat (Secondary Reformer)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_heat}]

Unit5.calculations = (['Reaction Mix 1', 'Air (Primary Reformer)'], Secondary_reformer_pt1_func)

# Unit 6: Secondary Reformer pt 2 - is there a ton of loss here
Unit6 = Unit('Secondary Reformer: Catalysis')
Unit6.required_calc_flows = 2
Unit6.expected_flows_in = ['Reaction Mix 2', 'Heat (Secondary Reformer)']
Unit6.expected_flows_out = ['Reaction Mix 3']
Unit6.coefficients = {'Heat of Rxn': 206.0, 'Unit Temp': 990}

def Secondary_reformer_pt2_func(ablist, coeff):
    mix_flow = ablist[0]
    heat_in = ablist[1]
    Q_in = heat_in.attributes['heat_flow_rate']
    mix_in = mix_flow.attributes['mass_flow_rate']
    Q_mix_in = mix_flow.attributes['heat_flow_rate']
    Q_rxn_needed = mix_in * 0.041  * coeff['Heat of Rxn']
    c_pout = (.358 * C_psteam ) + (.159 * C_pco) + (.125 * C_pco2) + (.055 * C_ph2) + (.302 * C_pn2)
    Q_out = c_pout * mix_in * (coeff['Unit Temp'] - ambient_t)
    Q_loss = Q_in + Q_mix_in - Q_rxn_needed - Q_out
    print('Unit6')
    
    return[{'name' : 'Reaction Mix 3','components' : ['H20','CO','CO2','H2', 'N2'], 'composition' : [.359, .159, .125, .055, .302], 'mass_flow_rate' : mix_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out+Q_rxn_needed},
           {'Heat loss': Q_loss}]
Unit6.calculations = (['Reaction Mix 2', 'Heat (Secondary Reformer)'], Secondary_reformer_pt2_func)

# Unit 7: Heat Recovery - We should have a heat flow catagory where it is just heat 
Unit7 = Unit('Heat Recoverer 1')
Unit7.expected_flows_in = ['Reaction Mix 3']
Unit7.expected_flows_out = ['Reaction Mix 4', 'Waste heat (Heat Recovery)']
Unit7.coefficients = {'Outlet Temp': 355, 'loses': .15}

def Heat_recovery_func(reaction_flow, coeff):
    reaction_in = reaction_flow.attributes['mass_flow_rate']
    Q_in = reaction_flow.attributes['heat_flow_rate']
    c_p = (.358 * C_psteam ) + (.159 * C_pco) + (.125 * C_pco2) + (.055 * C_ph2) + (.302 * C_pn2)
    Q_out = reaction_in * c_p * (coeff['Outlet Temp'] - ambient_t)
    Q_recoverable = Q_in - Q_out
    Q_loss = Q_recoverable * coeff['loses']
    Q_recovered = Q_recoverable - Q_loss
    print('Unit7')
    return[{'name' : 'Reaction Mix 4','components' : ['H20','CO','CO2','H2', 'N2'], 'composition' : [.359, .159, .125, .055, .302], 'mass_flow_rate' : reaction_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Outlet Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' :  'Waste heat (Heat Recovery)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_recovered},
           {'Heat loss': Q_loss}]

Unit7.calculations = {'Reaction Mix 3': Heat_recovery_func}
    
# Unit 8: Shift Converter - Don't understand what is meant by heat requirement for this unit? 
Unit8 = Unit('Shift Converter')
Unit8.expected_flows_in = ['Reaction Mix 4']
Unit8.expected_flows_out = ['Reaction Mix 5', 'Steam Out (Shift Converter)', 'Waste heat (Shift Converter)']
Unit8.coefficients = {'Conversion of CO': 1, 'Unit Temp': 32.5, 'Heat of Rxn': 41.0}

def Shift_converter_func(reaction_mix_flow, coeff):
    mix_in = reaction_mix_flow.attributes['mass_flow_rate']
    h2o_in = (reaction_mix_flow.attributes['composition'][reaction_mix_flow.attributes['components'].index('H20')]) * mix_in
    h2o_reacted = ((reaction_mix_flow.attributes['composition'][reaction_mix_flow.attributes['components'].index('CO')]) * mix_in) * (18.00 / 28.01)
    h2o_out = h2o_in - h2o_reacted
    mix_out = mix_in - h2o_out
    Q_in = reaction_mix_flow.attributes['heat_flow_rate']
    Q_steam_out = h2o_out * Hvap
    c_p = (.506 * C_pco2) + (.045 * C_ph2) + (.449 * C_pn2)
    Q_out = c_p * mix_out * (coeff['Unit Temp'] - ambient_t)
    Q_rxn = h2o_reacted * 41 / 18.0
    Q_recovered = Q_in + Q_rxn - Q_steam_out - Q_out
    
    print('Unit8')
    return[{'name' : 'Reaction Mix 5','components' : ['CO2','H2', 'N2'], 'composition' : [.506, .045, .449], 'mass_flow_rate' : mix_out,
            'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' :  'Steam Out (Shift Converter)', 'components' : ['Steam'], 'composition': [1], 'mass_flow_rate' : h2o_out,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature':315, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_steam_out},
           {'name' :  'Waste heat (Shift Converter)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_recovered},
           {'Heat of reaction': Q_rxn}]

Unit8.calculations = {'Reaction Mix 4': Shift_converter_func}
        

# Unit 9: CO2 Absorption
Unit9 = Unit('CO2 Absorption')
Unit9.expected_flows_in = ['Reaction Mix 5', 'Electricity (CO2 Absorption)']
Unit9.expected_flows_out = ['Carbon Dioxide', 'Reaction Mix 6']
Unit9.coefficients = {'Electricity (kw/kg)': 200}

def CO2_absorption_func(reaction_flow, coeff):
    mix_in = reaction_flow.attributes['mass_flow_rate']
    co2_in = (reaction_flow.attributes['composition'][reaction_flow.attributes['components'].index('CO2')]) * mix_in
    mix_out = mix_in - co2_in
    electricity_in = co2_in * coeff['Electricity (kw/kg)']
    Q_in = reaction_flow.attributes['heat_flow_rate']
    Q_loss = Q_in 
    print('Unit 9')
    return[{'name' : 'Electricity (CO2 Absorption)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Reaction Mix 6','components' : ['H2', 'N2'], 'composition' : [.176, .824], 'mass_flow_rate' : mix_out,
            'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out',
            'Set calc' : True, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Carbon Dioxide','components' : ['CO2'], 'composition' : [1], 'mass_flow_rate' : co2_in,
            'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit9.calculations = {'Reaction Mix 5': CO2_absorption_func}


# Unit 10 : Compressor - Should I add the cooling water here, is it below ambient temp?
Unit10 = Unit('Reaction Compressor')
Unit10.expected_flows_in = ['Reaction Mix 6', 'Electricity (Reaction Compressor)', 'Cooling Demand (Reaction Compressor)']
Unit10.expected_flows_out = ['Reaction Mix 7']
Unit10.coefficients = {'Elec efficiency' : .85, 't_in': ambient_t, 't_out': 270, 'P_out': 200, 'P_in': 25}

def Reaction_compression_func(reaction_flow, coeff):
    air_in = reaction_flow.attributes['mass_flow_rate']
    v_1 = (air_in * 0.08314 * (coeff['t_in'] + 273)) / (16.04 * coeff['P_in'])
    v_2 = (air_in * 0.08314 * (coeff['t_out'] + 273)) / (16.04 * coeff['P_out'])
    w = ((coeff['P_out'] * v_2) - (coeff['P_in'] * v_1)) / (1 - gamma_n2) # is it gamma -1 of 1-gamma
    electricity_in = -1 * w / coeff['Elec efficiency']
    c_p = (.176 * C_ph2) + (.824 * C_pn2)
    Q_out = c_p * air_in * (coeff['t_out'] - ambient_t)
    Q_cooling = Q_out 
    print('Unit 10')
    return[{'name' : 'Electricity (Reaction Compressor)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Reaction Mix 7', 'components' : ['H2', 'N2'], 'composition' : [.176, .824], 'mass_flow_rate' : air_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'pressure': coeff['P_out'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Cooling Demand (Reaction Compressor)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cooling}]

Unit10.calculations = {'Reaction Mix 6': Reaction_compression_func}

# Unit 11: Heater = fuel updated to combustion energy content 
Unit11 = Unit('Reaction Heater')
Unit11.expected_flows_in = ['Reaction Mix 7', 'Fuel (Reaction Heater)', 'Air (Reaction Heater)']
Unit11.expected_flows_out = ['Reaction Feed', 'Exhaust (Reaction Heater)']
Unit11.coefficients = {'loses': 0.15, 'Air Ratio': 3.0, 't_out': 450, 'Fuel HHV': 2500}

def Reaction_heat_func(reaction_feed, coeff):
    feed_in = reaction_feed.attributes['mass_flow_rate']
    Q_in = reaction_feed.attributes['heat_flow_rate']
    c_p = (.176 * C_ph2) + (.824 * C_pn2)
    Q_out = c_p * feed_in * (coeff['t_out'] - ambient_t)
    Q_fuel = (Q_out - Q_in) / (1 - coeff['loses'])
    m_fuel = Q_fuel / coeff['Fuel HHV'] 
    air_in = m_fuel * coeff['Air Ratio']
    Q_air = Q_fuel * coeff['loses']
    print('Unit 11')

    return[{'name' : 'Air (Reaction Heater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Exhaust (Reaction Heater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in+m_fuel,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_air},
           {'name' : 'Reaction Feed', 'components' : ['H2', 'N2'], 'composition' : [.176, .824], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name': 'Fuel (Reaction Heater)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'combustion_energy_content': Q_fuel, 'heat_flow_rate': Q_fuel}]

Unit11.calculations = {'Reaction Mix 7': Reaction_heat_func}

# Unit 12: Sythesis Converter - Add small steam demand to here to keep reaction isothermal 
Unit12 = Unit('Synthesis Converter')
Unit12.expected_flows_in = ['Reaction Feed', 'Chilling Demand (Synthesis Converter)', 'Recycle']
Unit12.expected_flows_out = ['Product Stream']
Unit12.coefficients = {'Conversion': .30, 'Heat of Rxn': -46.0, 'Recycle ratio': 2.33, 'Unit Temp':210}

def Synthesis_conversion_func(pure_feed, coeff):
    c_p = (.822 * C_pn2) + ((1-.822) * C_ph2)
    feed_in = pure_feed.attributes['mass_flow_rate']
    recycle_in = coeff['Recycle ratio'] * feed_in
    Q_recycle = c_p * (450 - ambient_t) * recycle_in
    recycle_n2_wt = .823
    recycle_h2_wt = 1 - recycle_n2_wt
    hydrogen_in = (recycle_h2_wt * recycle_in) + (feed_in * pure_feed.attributes['composition'][pure_feed.attributes['components'].index('H2')])
    nitrogen_in = (recycle_in + feed_in) - hydrogen_in
    ammonia_out = (hydrogen_in * coeff['Conversion'] * 17 / 3)
    hydrogen_out = hydrogen_in * (1 - coeff['Conversion'])
    nitrogen_out = (feed_in + recycle_in) - ammonia_out - hydrogen_out
    nitrogen_wt = nitrogen_out / (ammonia_out + hydrogen_out + nitrogen_out)
    ammonia_wt = ammonia_out / (ammonia_out + hydrogen_out + nitrogen_out)
    hydrogen_wt = 1 - ammonia_wt - nitrogen_wt 
    Q_in = pure_feed.attributes['heat_flow_rate']
    c_pout = (C_pn2 * nitrogen_wt) + (C_pnh3 * ammonia_wt) + (hydrogen_wt*C_ph2)
    Q_out = c_pout * (recycle_in + feed_in) * (coeff['Unit Temp'] - ambient_t)
    Q_rxn = coeff['Conversion'] * coeff['Heat of Rxn'] * (ammonia_out / (2 * 17))
    Q_chilling = -1 * (Q_in + Q_recycle  + Q_rxn - Q_out)
    

    print('Unit12')
    return[{'name' : 'Chilling Demand (Synthesis Converter)', 'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling},
           {'name': 'Recycle', 'components' : ['H2', 'N2'], 'composition': [recycle_h2_wt, recycle_n2_wt], 'mass_flow_rate': recycle_in,
            'flow_type': 'Process Stream', 'In or out': 'In', 'Set calc': False, 'Set shear': True, 'heat_flow_rate': Q_recycle},
           {'name' : 'Product Stream', 'components' : ['NH3', 'H2', 'N2'], 'composition' : [ammonia_wt, hydrogen_wt, nitrogen_wt], 'mass_flow_rate' : (feed_in + recycle_in),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]

Unit12.calculations = {'Reaction Feed' : Synthesis_conversion_func}

# Unit 13: Heat Recovery - Combination of two units the cooler and the steam generator 
Unit13 = Unit('Heat Recovery 2')
Unit13.expected_flows_in = ['Product Stream', 'Chilling Demand (Cooler)']
Unit13.expected_flows_out = ['Ammonia', 'Waste Heat (Heat Recovery 2)', 'Cooled Recycle']
Unit13.coefficients = {'loses': 0.10, 'Unit Temp': 25, 'Chilling Heat Split': .5}

def heat_recovery_2_func(ammonia_flow, coeff):
    feed_in = ammonia_flow.attributes['mass_flow_rate']
    Q_in = ammonia_flow.attributes['heat_flow_rate']
    ammonia_wt = ammonia_flow.attributes['composition'][ammonia_flow.attributes['components'].index('NH3')]
    hydrogen_wt = ammonia_flow.attributes['composition'][ammonia_flow.attributes['components'].index('H2')]
    nitrogen_wt = ammonia_flow.attributes['composition'][ammonia_flow.attributes['components'].index('N2')]
    c_p = (ammonia_wt * C_pnh3) + (hydrogen_wt * C_ph2) + (nitrogen_wt * C_pn2)
    Q_condense = (ammonia_wt * feed_in * Hcondense_nh3)
    Q_out = c_p * feed_in * (coeff['Unit Temp'] - ambient_t)
    Q_loss = coeff['loses'] * (Q_in + Q_condense)
    Q_avail = Q_in - Q_out - Q_loss
    Q_chilling = Q_avail * coeff['Chilling Heat Split']
    Q_waste_heat = Q_avail * (1 - coeff['Chilling Heat Split'])
    ammonia_out = feed_in * ammonia_wt
    recycle_out = feed_in - ammonia_out
    print('Unit13')
    return[{'name': 'Chilling Demand (Cooler)', 'flow_type': 'Waste heat', 'elec_flow_rate': 0, 'In or out': 'In', 'Set calc': False, 'heat_flow_rate': -Q_chilling},
           {'name': 'Waste Heat (Heat Recovery 2)',
            'flow_type': 'Waste heat', 'elec_flow_rate': 0, 'In or out': 'Out', 'Set calc': False, 'heat_flow_rate': Q_waste_heat},
           {'name': 'Ammonia', 'components': ['NH3'], 'composition': [1], 'mass_flow_rate': ammonia_out,
            'flow_type': 'Process Stream', 'elec_flow_rate': 0, 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': 0},
           {'name': 'Cooled Recycle', 'components': ['H2', 'N2'], 'composition': [0.822, 0.178], 'mass_flow_rate': recycle_out,
            'flow_type': 'Process Stream', 'elec_flow_rate': 0, 'In or out': 'Out', 'Set calc': True, 'heat_flow_rate': Q_out},
           {'Heat loss': Q_loss}]
Unit13.calculations = {'Product Stream': heat_recovery_2_func} 

# Unit 14: Recycle Heater - think about this and why it might not be showing 
# Update to be a fuel demand instead of waste heat
Unit14 = Unit('Recycle Heater')
Unit14.expected_flows_in = ['Cooled Recycle', 'Fuel (Recycle Heater)', 'Air (Recycle Heater)']
Unit14.expected_flows_out = ['Recycle', 'Exhaust (Recycle Heater)']
Unit14.coefficients = {'Outlet Temp': 450, 'Air Ratio': 3, 'Fuel HHV': 5200, 'loses': 0.10}

def Recycle_heater_func(recycle_flow, coeff):
    recycle_in = recycle_flow.attributes['mass_flow_rate']
    c_p = (.822 * C_pn2) + ((1-.822) * C_ph2)
    Q_in = recycle_flow.attributes['heat_flow_rate']
    Q_out = c_p * recycle_in * (coeff['Outlet Temp'] - ambient_t)
    Q_fuel = (Q_out - Q_in) / (1-coeff['loses'])
    m_fuel = Q_fuel / coeff['Fuel HHV']
    air_in = m_fuel * coeff['Air Ratio']
    Q_loss = Q_fuel * coeff['loses']
    print('Unit 14')
    return[{'name' : 'Air (Recycle Heater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Exhaust (Recycle Heater)','components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in+m_fuel,
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss},
           {'name': 'Fuel (Recycle Heater)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'combustion_energy_content': Q_fuel, 'heat_flow_rate': Q_fuel},
           {'name' : 'Recycle', 'components' : ['H2', 'N2'], 'composition' : [.822, 1-.822], 'mass_flow_rate' : recycle_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out, 'Set shear' : True}]
Unit14.calculations = {'Cooled Recycle': Recycle_heater_func}

# Unit 15: Ammonia Splitter
Unit15 = Unit('Ammonia Splitter')
Unit15.expected_flows_in = ['Ammonia']
Unit15.expected_flows_out = ['Ammonia Product', 'Ammonia for Urea', 'Ammonia for AS', 'Ammonia for AN']
Unit15.coefficients = {'Pure wt': .32, 'AS wt': .166, 'Urea wt': .163}

def Ammonia_splitter_func(ammonia_flow, coeff):
    ammonia_in = ammonia_flow.attributes['mass_flow_rate']
    Q_in = ammonia_flow.attributes['heat_flow_rate']
    as_ammonia = ammonia_in * coeff['AS wt']
    urea_ammonia = ammonia_in * coeff['Urea wt']
    product_ammonia = ammonia_in * coeff['Pure wt']
    an_ammonia = ammonia_in - as_ammonia - urea_ammonia - product_ammonia
    print('Unit 15')
    return[{'name' : 'Ammonia Product', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : product_ammonia,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Ammonia for Urea', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : urea_ammonia,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Ammonia for AS', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : as_ammonia,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Ammonia for AN', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : an_ammonia,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'Heat loss': Q_in}]

Unit15.calculations = {'Ammonia': Ammonia_splitter_func}       

# Unit 16: Ostwald Preheater - ammonia is being vaporized no?
Unit16 = Unit('Ostwald Preheater')
Unit16.expected_flows_in = ['Ammonia for AN', 'Fuel (Ostwald Preheater)', 'Air (Ostwald Preheater)', 'Electricity (Ostwald Preheater)']
Unit16.expected_flows_out = ['Reaction Mix 9', 'Exhaust (Ostwald Preheater)']
Unit16.coefficients = {'Air to Ammonia': 17.01, 'Electricity (kw/kg)': 150, 'Unit Temp': 850.,
                       'Loses': .10, 'Fuel HHV': 5200}

def Ostwald_preheater_func(ammonia_flow, coeff):
    ammonia_in = ammonia_flow.attributes['mass_flow_rate']
    air_in = ammonia_in * coeff['Air to Ammonia']
    electricity_in = air_in * coeff['Electricity (kw/kg)']
    Q_ammonia_out = (ammonia_in *C_pnh3 * (coeff['Unit Temp'] - ambient_t)) + (ammonia_in * Hcondense_nh3)
    Q_exhaust = ((.21 * C_po2) + (.79 * C_pn2)) * air_in * (coeff['Unit Temp'] - ambient_t)
    Q_fuel = (Q_exhaust + Q_ammonia_out) / (1 - coeff['Loses']) 
    Q_loss = Q_fuel * coeff['Loses']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    print('Unit16')
    return[{'name' : 'Reaction Mix 9', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : (ammonia_in + air_in),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_ammonia_out + Q_exhaust},
           {'name' : 'Fuel (Ostwald Preheater)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'combustion_energy_content': Q_fuel, 'heat_flow_rate': Q_fuel},
           {'name' : 'Air (Ostwald Preheater)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Electricity (Ostwald Preheater)',
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False},
           {'name' : 'Exhaust (Ostwald Preheater)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss}]

Unit16.calculations = {'Ammonia for AN': Ostwald_preheater_func}

# Unit 17: Ostwald Process
Unit17 = Unit('Ostwald Process')
Unit17.expected_flows_in = ['Reaction Mix 9']
Unit17.expected_flows_out = ['Nitrate Product Mix', 'HNO3', 'NH3']
Unit17.coefficients = {'HNO3 Weight Percent': .10, 'NH3 Weight Percent': .1, 'Unit Temp': 850.}

def Ostwald_process_func(reaction_mix, coeff):
    mix_in = reaction_mix.attributes['mass_flow_rate']
    Q_in = reaction_mix.attributes['heat_flow_rate']
    hno3_out = mix_in * coeff['HNO3 Weight Percent']
    nh3_out = mix_in * coeff['NH3 Weight Percent'] 
    mix_out = mix_in - hno3_out - nh3_out
    Q_nh3_out = nh3_out * C_pnh3 * (coeff['Unit Temp'] - ambient_t)
    Q_hno3_out = hno3_out * C_phno3 * (coeff['Unit Temp'] - ambient_t)
    Q_out = Q_in - Q_nh3_out - Q_hno3_out
    
    print('Unit17')
    return[{'name' : 'Nitrate Product Mix', 'components' : ['Ammonia Nitrate'], 'composition' : [1], 'mass_flow_rate' : (mix_out),
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'name' : 'HNO3', 'components' : ['HNO3'], 'composition' : [1], 'mass_flow_rate' : (hno3_out),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_hno3_out},
           {'name' : 'NH3', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate' : (nh3_out),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_nh3_out}]
Unit17.calculations = {'Reaction Mix 9': Ostwald_process_func}

# Unit 18: Ammonia Nitrate Cooler
Unit18 = Unit('Ammonia Nitrate Cooler')
Unit18.required_calc_flows = 2
Unit18.expected_flows_in = ['HNO3', 'NH3']
Unit18.expected_flows_out = ['Reacton Mix 10', 'Heat (AN Cooler)']
Unit18.coefficients = {'Unit Temp': 180}

def Ammonia_nitrate_cooler_func(ablist, coeff):
    ammonia_flow = ablist[0]
    hno3_flow = ablist[1]
    ammonia_in = ammonia_flow.attributes['mass_flow_rate']
    hno3_in = hno3_flow.attributes['mass_flow_rate']
    mix_out = hno3_in+ammonia_in
    Q_ammonia_in = ammonia_flow.attributes['heat_flow_rate']
    Q_hno3_in = hno3_flow.attributes['heat_flow_rate']
    Q_in = Q_ammonia_in + Q_hno3_in
    Q_out = ((ammonia_in * C_pnh3) + (hno3_in * C_phno3)) * (coeff['Unit Temp'] - ambient_t)
    Q_wasteheat = Q_in - Q_out
    print('Unit 18')
    return[{'name' : 'Reaction Mix 10', 'components' : ['mix'], 'composition' : [1], 'mass_flow_rate' : (mix_out),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' :  'Heat (AN Cooler)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_wasteheat}]
Unit18.calculations = (['HNO3', 'NH3'], Ammonia_nitrate_cooler_func)
           
# Unit 19: Ammonia Nitrate Process - What is happening here 
Unit19 = Unit('Ammonia Nitrate Process')
Unit19.expected_flows_in = ['Reaction Mix 10']
Unit19.expected_flows_out = ['Ammonia Nitrate Product']
Unit19.coefficients = {'Heat of Rxn': 365.}

def Ammonia_nitrate_process_func(mix_flow, coeff):
    Q_in = mix_flow.attributes['heat_flow_rate']
    mass_in = mix_flow.attributes['mass_flow_rate']
    ammonia_wt = (5.1 / (5.1+31.5))
    ammonia_in = ammonia_wt * mass_in
    Q_rxn = (ammonia_in / 17.00) * coeff['Heat of Rxn']
    Q_out = Q_in + Q_rxn 
    print('Unit19')
    return[{'name' : 'Ammonia Nitrate Product', 'components' : ['AN'], 'composition' : [1], 'mass_flow_rate' : (mass_in),
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'Heat of reaction': Q_rxn}]
Unit19.calculations = {'Reaction Mix 10': Ammonia_nitrate_process_func}

# Unit 20: Ammonia Sulfate Preaheater - 10 times too much
Unit20 = Unit('AS Preheater')
Unit20.expected_flows_in = ['Steam (AS Preheater)', 'Ammonia for AS', 'H2SO4']
Unit20.expected_flows_out = ['Condensate (AS Preheater)', 'Reaction Mix 11']
Unit20.coefficients = {'Unit Temp': 60, 'H2SO4 Molar Ratio': 0.5, 'loss': 0.10, 'Steam temp':120}

def Ammonia_sulfate_preheater_func(as_flow, coeff):
    ammonia_in = as_flow.attributes['mass_flow_rate']
    h2so4_in = (ammonia_in / 17) * coeff['H2SO4 Molar Ratio']
    ammonia_wt = ammonia_in / (ammonia_in + h2so4_in)
    h2so4_wt = 1 - ammonia_wt
    mix_out = ammonia_in + h2so4_in
    Q_in = as_flow.attributes['heat_flow_rate']
    Q_ammonia_out = ammonia_in * C_pnh3 * (coeff['Unit Temp'] - ambient_t)
    Q_h2so4 = h2so4_in * C_ph2so4 * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_ammonia_out + Q_h2so4 - Q_in) / (1 - coeff['loss'])
    Q_loss = Q_steam * coeff['loss']
    m_steam = Q_steam / Hvap
    print('Unit20')
    return[{'name':'Steam (AS Preheater)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature':coeff['Steam temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Reaction Mix 11', 'components' : ['NH3','H2SO4'], 'composition' : [ammonia_wt, h2so4_wt], 'mass_flow_rate' : (mix_out),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': (Q_ammonia_out + Q_h2so4)},
           {'name':'Condensate (AS Preheater)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'H2SO4', 'components' : ['H2SO4'], 'composition' : [1], 'mass_flow_rate' : h2so4_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit20.calculations = {'Ammonia for AS': Ammonia_sulfate_preheater_func}

# Unit 21: Ammonia Sulfate Process
Unit21 = Unit("AS Process")
Unit21.expected_flows_in = ['Reaction Mix 11']
Unit21.expected_flows_out = ['Ammonia Sulfate Product']
Unit21.coefficients = {'Heat of Rxn': 116.}

def Ammonia_sulfate_process_func(mix_flow, coeff):
    Q_in = mix_flow.attributes['heat_flow_rate']
    mass_in = mix_flow.attributes['mass_flow_rate']
    ammonia_wt = mix_flow.attributes['composition'][mix_flow.attributes['components'].index('NH3')]
    ammonia_in = ammonia_wt * mass_in
    Q_rxn = (ammonia_in / 17.00) * coeff['Heat of Rxn']
    Q_out = Q_in + Q_rxn 
    print('Unit21')
    return[{'name' : 'Ammonia Sulfate Product', 'components' : ['AS'], 'composition' : [1], 'mass_flow_rate' : (mass_in),
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'Heat of reaction': Q_rxn}]
Unit21.calculations = {'Reaction Mix 11': Ammonia_sulfate_process_func}

# Unit 22: Urea Preheater
Unit22 = Unit('Urea Preheater')
Unit22.required_calc_flows = 2
Unit22.expected_flows_in = ['Ammonia for Urea', 'Carbon Dioxide', 'Electricity (Urea Preaheater)', 'Steam (Urea Preheater)']
Unit22.expected_flows_out = ['Reaction Mix 8', 'Condensate (Urea Preaheater)']
Unit22.coefficients = {'Electricity (kw/kg)': 250.,'Unit Temp': 160., 'loss':0.10, 'Steam temp': 120}

def Urea_preheater_func(ablist, coeff):
    ammonia_flow = ablist[0]
    co2_flow = ablist[1]
    co2_in = co2_flow.attributes['mass_flow_rate']
    ammonia_in = ammonia_flow.attributes['mass_flow_rate']
    ammonia_wt = ammonia_in / (ammonia_in + co2_in)
    co2_wt = 1 -  ammonia_wt
    mix_out = co2_in + ammonia_in
    electricity_in = coeff['Electricity (kw/kg)'] * co2_in
    Q_in = co2_flow.attributes['heat_flow_rate'] + ammonia_flow.attributes['heat_flow_rate']
    Q_co2_out = C_pco2 * co2_in * (coeff['Unit Temp'] - ambient_t)
    Q_nh3_out = C_pnh3 * ammonia_in * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_co2_out + Q_nh3_out - Q_in) / (1-coeff['loss'])
    Q_loss = Q_steam * coeff['loss']
    m_steam = Q_steam / Hvap
    print('Unit22')
    print(mix_out)

    return[{'name':'Steam (Urea Preheater)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature':coeff['Steam temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Reaction Mix 8', 'components' : ['NH3','CO2'], 'composition' : [ammonia_wt, co2_wt], 'mass_flow_rate' : (mix_out),
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': (Q_nh3_out + Q_co2_out)},
           {'name':'Condensate (Urea Preaheater)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Electricity (Urea Preaheater)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit22.calculations = (['Ammonia for Urea', 'Carbon Dioxide'], Urea_preheater_func)

# Unit 23: Urea Process
Unit23 = Unit('Urea Process')
Unit23.expected_flows_in = ['Reaction Mix 8']
Unit23.expected_flows_out = ['Urea']
Unit23.coefficients = {'Heat of Rxn': 116.}

def Urea_process_func(mix_flow, coeff):
    Q_in = mix_flow.attributes['heat_flow_rate']
    mass_in = mix_flow.attributes['mass_flow_rate']
    ammonia_wt = mix_flow.attributes['composition'][mix_flow.attributes['components'].index('NH3')]
    ammonia_in = ammonia_wt * mass_in
    Q_rxn = (ammonia_in / 17.00) * coeff['Heat of Rxn']
    Q_out = Q_in + Q_rxn 
    print('Unit23')
    return[{'name' : 'Urea', 'components' : ['Urea'], 'composition' : [1], 'mass_flow_rate' : (mass_in),
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'Heat of reaction': Q_rxn}]
Unit23.calculations = {'Reaction Mix 8': Urea_process_func}

###########################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7,
                Unit8, Unit9, Unit10, Unit11, Unit12, Unit13, Unit14,
                Unit15, Unit16, Unit17, Unit18, Unit19, Unit20, Unit21, Unit22,
                Unit23]


main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)


utilities_recap('heat_intensity_ammonia_4', allflows, processunits)




