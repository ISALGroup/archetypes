# -*- coding: utf-8 -*-
"""
Created on Thursday May 8th 14:14:34 2025

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
C_pnh3 = 2.19
C_pco2 = 0.844
C_pco = 1.02
C_pch4 = 2.22
C_pn2 = 1.04
C_pno = 0.995
C_pn2o = 0.88

######################################################UNITS#####################################
# Unit 1: Methane Preheater
Unit1 = Unit('Methane Preheater')
Unit1.expected_flows_in = ['Feed Methane', 'Fuel (Methane Preheater)', 'Air (Methane Preheater)']
Unit1.expected_flows_out = ['1', 'Stack Exhaust (Methane Preheater)']

Unit1.coefficients = {'Unit Temp': 375.0, 'Fuel HHV': 55000., 'Air Ratio': 2,
                      'Loses': .10}

def Methanepreheater_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    air_in = feed_in * coeff['Air Ratio']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pch4 * (coeff['Unit Temp'] - ambient_t)
    Q_exhaust = air_in * C_pair * (coeff['Unit Temp'] - ambient_t)
    Q_fuel = (Q_out + Q_exhaust - Q_in) / (1 - coeff['Loses'])
    Q_loss = Q_fuel * coeff['loses']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    exhaust_out = m_fuel + air_in

    return[{'name' : '1', 'components' : ['Methane'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name': 'Stack Exhaust (Methane Preheater)', 'components': ['Exhaust'], 'composition': [1], 'mass_flow_rate': exhaust_out,
             'flow_type': 'Exhaust', 'elec_flow_rate': 0, 'In or our': 'Out', 'Set calc': False, 'heat_flow_rate': Q_exhaust},
           {'name': 'Fuel (Methane Preheater)', 'components': ['Fuel'], 'composition': [1], 'mass_flow_rate': m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate': 0, 'In or our': 'In', 'Set calc': False, 'heat_flow_rate': Q_fuel},
           {'name': 'Air (Methane Preheater)', 'components': ['Air'], 'composition': [1], 'mass_flow_rate': air_in,
             'flow_type': 'Air', 'elec_flow_rate': 0, 'In or our': 'In', 'Set calc': False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit1.calculations = {'Feed Methane': Methanepreheater_func}
FlowA = Flow(name = 'Feed Methane', components = ['Methane'], composition = [1], flow_type = 'input', mass_flow_rate = 10000)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Desulfurization
Unit2 = Unit('Sulfur Removal')
Unit2.expected_flows_in = ['1', 'ZnO', 'H2']
Unit2.expected_flows_out = ['2', 'ZnS']

Unit2.coefficients = {'Sulfur Content': (.5*10**-6)}

def Desulfurization_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    sulfur_in = feed_in * coeff['Sulfur Content']
    zn_o_in = sulfur_in * 81.38 / 32.06
    zn_s_out = zn_o_in * 97.474 / 81.38
    water_out = zn_s_out * 18.00 / 97.474
    h2_in = water_out + zn_s_out - zn_o_in
    feed_out = water_out + feed_in
    water_wt = water_out /feed_out
    Q_in = feed_flow.attributes['heat_flow_rate']
    
    return[{'name' : '2', 'components' : ['Methane', 'Water'], 'composition' : [1-water_wt, water_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'ZnO', 'components' : ['ZnO'], 'composition' : [1], 'mass_flow_rate' : zn_o_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'ZnS', 'components' : ['ZnS'], 'composition' : [1], 'mass_flow_rate' : zn_s_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'H2', 'components' : ['H2'], 'composition' : [1], 'mass_flow_rate' : h2_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit2.calculations = {'1': Desulfurization_func}

# Unit 3: Primary Reformer
Unit3 = Unit('Primary Reformer')
Unit3.expected_flows_in = ['2', 'Fuel (Primary Reformer)', 'Steam (Primary Reformer)']
Unit3.expected_flows_out = ['3', 'Exhaust (Primary Reformer)']

Unit3.calculations = {'Conversion Rate': .60, 'Heat of Rx': 206.0, 'Loses': .95,
                      'Unit Temp': 815, 'Unit Pressure': }

def Primaryreformer_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_mol_in = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')]) / 18.00
    methane_mol_in = (feed_in - water_in) / 16.00
    steam_in = (methane_mol_in - water_mol_in) * 18.00
    co_out = methane_mol_in * coeff['Conversion Rate'] * 1 * 28.01
    h2_out = methane_mol_in * coeff['Conversion Rate'] * 3 * 2.000 # stoich conversion
    


    
    
           
    
    
