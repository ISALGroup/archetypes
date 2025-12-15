# -*- coding: utf-8 -*-
"""
Created on Monday July 21st 14:04:34 2025

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
C_poil = 1.86 # these need to be different 
C_pstearin = 1.86
C_polein = 1.86


##################################### Units  ######################
#Unit 1: Crude Oil Storage
Unit1 = Unit('Crude Oil Storage')
Unit1.expected_flows_in = ['Feed Oil', 'Electricity (Storage)']
Unit1.expected_flows_out = ['Crude Oil']
Unit1.coefficients = {'Electricity (kw/kg)': 0.000}

def Crude_oil_storage_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    print('Unit 1')
    return[{'name' : 'Electricity (Storage)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Crude Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]

Unit1.calculations = {'Feed Oil': Crude_oil_storage_func}
FlowA = Flow(name = 'Feed Oil', components = ['Oil'], composition = [1], flow_type = 'input', mass_flow_rate = 100000)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Degumming
Unit2 = Unit('Degumming')
Unit2.expected_flows_in = ['Crude Oil', 'Phosphoric Acid', 'Water (Degumming)', 'Steam (Degumming)']
Unit2.expected_flows_out = ['Oil', 'Condensate (Degumming)']
Unit2.coefficients = {'Phosphorous Ratio': 0.003, 'Water Ratio': 0.001, 'Unit Temp': 90.0,
                      'loses': 0.10, 'Steam Temp': 100.}

def Degumming_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    phosphoric_in = oil_in * coeff['Phosphorous Ratio']
    water_in = oil_in * coeff['Water Ratio']
    oil_out = oil_in + phosphoric_in + water_in
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_out = (oil_in * C_poil * (coeff['Unit Temp'] - ambient_t)) + ((water_in + phosphoric_in) * C_pw * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_out - Q_in) / (1- coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    print('Unit 2')
    return[{'name' : 'Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
           {'name' : 'Steam (Degumming)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Degumming)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Water (Degumming)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Phosphoric Acid', 'components' : ['H2SO4'], 'composition' : [1], 'mass_flow_rate' : phosphoric_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Crude Oil': Degumming_func}

# Unit 3: Gum Seperator - Bleached earth comes in the next unit 
Unit3 = Unit('Gum Seperator')
Unit3.expected_flows_in = ['Oil', 'Electricity (Gum Seperator)']
Unit3.expected_flows_out = ['Gum', 'Degummed Oil']
Unit3.coefficients = {'Sludge Out': 0.01, 'Electricity (kw/kg)': 0.00}

def Gum_seperator_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    sludge_out = oil_in * coeff['Sludge Out']
    oil_out = oil_in - sludge_out
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_out = (oil_out / oil_in) * Q_in
    Q_loss = Q_in - Q_out
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    print('Unit 3')
    return[{'name' : 'Electricity (Gum Seperator)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Gum', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : sludge_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss},
           {'name' : 'Degummed Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit3.calculations = {'Oil': Gum_seperator_func}

#Unit 4: Bleaching Vessel
Unit4 = Unit('Bleach Tank')
Unit4.expected_flows_in = ['Degummed Oil', 'Bleaching Earth', 'Electricity (Bleach Tank)', 'Steam (Bleach Tank)']
Unit4.expected_flows_out = ['Condensate (Bleach Tank)', 'Bleaching Oil']
Unit4.coefficients = {'Bleached Earth Ratio': 0.005, 'Unit Temp': 110., 'Steam Temp': 110.,
                      'loses': 0.10, 'Electricity (kw/kg)': 0.00}
def Bleaching_vessel_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    Q_in = oil_flow.attributes['heat_flow_rate']
    bleach_earth_in = coeff['Bleached Earth Ratio'] * oil_in
    oil_out = bleach_earth_in + oil_in
    Q_out = (bleach_earth_in * 0.86 * (coeff['Unit Temp'] - ambient_t)) + (oil_in * C_poil * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    print('Unit 4')
    return[{'name' : 'Steam (Bleach Tank)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Bleach Tank)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Electricity (Bleach Tank)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Bleaching Earth', 'components' : ['Bleach'], 'composition' : [1], 'mass_flow_rate' : bleach_earth_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Bleaching Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_out,
             'flow_type': 'Process Stream', 'Temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Degummed Oil': Bleaching_vessel_func}

#Unit 5: Bleaching Filter
Unit5 = Unit('Bleach Filter')
Unit5.expected_flows_in = ['Bleaching Oil', 'Electricity (Bleach Filter)']
Unit5.expected_flows_out = ['Bleach', 'Debleached Oil']
Unit5.coefficients = {'Waste out': 0.007, 'Electricity (kw/kg)': 0.00}

def Bleaching_filter_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    waste_out = oil_in * coeff['Waste out']
    oil_out = oil_in - waste_out
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_out = (oil_out / oil_in) * Q_in
    Q_waste = Q_in - Q_out
    electricity_in = coeff['Electricity (kw/kg)'] * oil_in
    print('Unit 5')
    return[{'name' : 'Electricity (Bleach Filter)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Bleach', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_waste},
           {'name' : 'Debleached Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit5.calculations = {'Bleaching Oil': Bleaching_filter_func}

# Unit 6: Deodorizer Column
Unit6 = Unit('Deodorizer')
Unit6.expected_flows_in = ['Debleached Oil', 'Steam (Deodorizer)', 'Electricity (Deodorizer)']
Unit6.expected_flows_out = ['Condensate (Deodorizer)', 'Vapors', 'Refined Oil']
Unit6.coefficients = {'PFAD Ratio': 0.042, 'Unit Temp': 240.0, 'Steam Temp': 260.0, 'loses': 0.01,
                      'Electricity (kw/kg)':0.00}

def Deodorizer_column_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    Q_in = oil_flow.attributes['heat_flow_rate']
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    Q_out = oil_in * C_poil * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    pfad_out = oil_in * coeff['PFAD Ratio']
    oil_out = oil_in - pfad_out
    Q_pfad  = (pfad_out / oil_in) * Q_out
    Q_refined = Q_out - Q_pfad
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    
    print('Unit 6')
    return[{'name' : 'Electricity (Deodorizer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Deodorizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Deodorizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Vapors', 'components' : ['PFAD'], 'composition' : [1], 'mass_flow_rate' : pfad_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_pfad},
           {'name' : 'Refined Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_refined}]
Unit6.calculations = {'Debleached Oil': Deodorizer_column_func}
    
# Unit 7: Fatty Acid Condenser
Unit7 = Unit('Fatty Acid Condenser')
Unit7.expected_flows_in = ['Vapors', 'Electricity (Fatty Acid Condenser)']
Unit7.expected_flows_out = ['Fatty Acids', 'Waste Heat (Fatty Acid Condenser)']
Unit7.coefficients = {'Condensate Temp': 50.0, 'C_ppfad': 1.86, 'H_fusion_pfad': 120.0,
                      'Electricity (kw/kg)': 0.00}

def PFAD_condenser_func(pfad_flow, coeff):
    pfad_in = pfad_flow.attributes['mass_flow_rate']
    Q_in = pfad_flow.attributes['heat_flow_rate']
    Q_out = pfad_in * coeff['C_ppfad'] * (coeff['Condensate Temp'] - ambient_t)
    Q_avail = Q_in - Q_out
    Q_rxn = pfad_in * coeff['H_fusion_pfad']
    electricity_in = pfad_in * coeff['Electricity (kw/kg)']
    print('Unit7')
    return[{'name' : 'Electricity (Fatty Acid Condenser)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Fatty Acids', 'components' : ['Fatty Acids'], 'composition' : [1], 'mass_flow_rate' : pfad_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out},
           {'name' : 'Waste Heat (Fatty Acid Condenser)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_avail}]
Unit7.calculations = {'Vapors': PFAD_condenser_func}
           
# Do we need unit 8

# Unit 9 : Condition Tank
Unit9 = Unit('Conditioning Tank')
Unit9.expected_flows_in = ['Refined Oil']
Unit9.expected_flows_out = ['Conditioned Oil', 'Waste Heat (Conditioning Tank)']
Unit9.coefficients = {'Unit Temp': 70.0}

def Conditioning_tank_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_out = oil_in * C_poil * (coeff['Unit Temp'] - ambient_t)
    Q_avail = Q_in - Q_out
    print('Unit9')
    return[{'name' : 'Waste Heat (Conditioning Tank)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_avail},
           {'name' : 'Conditioned Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0,'Temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit9.calculations = {'Refined Oil': Conditioning_tank_func} 

# Unit 10 : Crystallizer
Unit10 = Unit('Crystallizer')
Unit10.expected_flows_in = ['Conditioned Oil', 'Cooling Water (Crystallizer)', 'Electricity (Crystallizer)']
Unit10.expected_flows_out = ['Crystallized Oil', 'Water (Crystallizer)']
Unit10.coefficients = {'Electricity (kw/kg)': 0.00, 'Cooling Water Inlet Temp': 10., 'Cooling Water Outlet Temp': ambient_t,
                       'Crystalization Rate': 0.25, 'Unit Temp': 35}

def Crystallizer_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    Q_in = oil_flow.attributes['heat_flow_rate']
    crystallized = oil_in * coeff['Crystalization Rate']
    liquid = oil_in - crystallized
    #Q_crystallization = crystallized * 71.0
    Q_cooling = oil_in * C_poil * (coeff['Unit Temp'] - ambient_t)
    Q_cw = Q_cooling - Q_in
    m_cw = -Q_cw / (C_pw * (coeff['Cooling Water Outlet Temp'] - coeff['Cooling Water Inlet Temp']))
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    
    print('Unit 10')
    return[{'name' : 'Crystallized Oil', 'components' : ['Olein', 'Stearin'], 'composition' : [.75, .25], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0,'Temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_cooling},
           {'name' : 'Electricity (Crystallizer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Cooling Water (Crystallizer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : m_cw,
             'flow_type': 'Cooling water', 'elec_flow_rate' : 0,'Temperature': coeff['Cooling Water Inlet Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cw},
           {'name' : 'Water (Crystallizer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : m_cw,
             'flow_type': 'Water', 'elec_flow_rate' : 0,'Temperature': coeff['Cooling Water Outlet Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},]
Unit10.calculations = {'Conditioned Oil': Crystallizer_func}
           
# Unit 11: Filter Membrane - all filters should require 2 flows
Unit11 = Unit('Filter Membrane')
Unit11.expected_flows_in = ['Crystallized Oil']
Unit11.expected_flows_out = ['Stearin', 'Olein']
Unit11.coefficients = {}

def Filter_membrane_func(oil_flow,coeff):
    stearin_in = (oil_flow.attributes['composition'][oil_flow.attributes['components'].index('Stearin')]) * oil_flow.attributes['mass_flow_rate']
    olein_in = (oil_flow.attributes['composition'][oil_flow.attributes['components'].index('Olein')]) * oil_flow.attributes['mass_flow_rate']
    heat_loss = oil_flow.attributes['heat_flow_rate']
    print('Unit 11')
    return[{'name' : 'Stearin', 'components' : ['Stearin'], 'composition' : [1], 'mass_flow_rate' : stearin_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Olein', 'components' : ['Olein'], 'composition' : [1], 'mass_flow_rate' : olein_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'Heat loss': heat_loss}]
Unit11.calculations = {'Crystallized Oil': Filter_membrane_func} 

# Unit 12: Olein Polish FIlter
Unit12 = Unit('Olein Polish Filter')
Unit12.expected_flows_in = ['Olein', 'Electricity (Olein Filter)']
Unit12.expected_flows_out = ['Clean Olein']
Unit12.coefficients = {'Electricity (kw/kg)': 0.00}

def Olein_polish_cleaner(olein_flow,coeff):
    olein_in = olein_flow.attributes['mass_flow_rate']
    electricity_in = coeff['Electricity (kw/kg)'] * olein_in
    print('Unit12')
    return[{'name' : 'Electricity (Olein Filter)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Clean Olein', 'components' : ['Olein'], 'composition' : [1], 'mass_flow_rate' : olein_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit12.calculations = {'Olein': Olein_polish_cleaner}

# Unit 13 : Stearin Melting Tank
Unit13 = Unit('Stearin Melting')
Unit13.expected_flows_in = ['Stearin', 'Electricity (Stearin Melting)', 'Steam (Stearin Melting)']
Unit13.expected_flows_out = ['Liquid Stearin', 'Condensate (Stearin Melting)']
Unit13.coefficients = {'Unit Temp': 70.0, 'Heat of Fusion': 150.0, 'loses': 0.10, 'Electricity (kw/kg)': 0.00,
                       'Steam Temp': 100}

def Stearin_melting_func(stearin_flow, coeff):
    stearin_in = stearin_flow.attributes['mass_flow_rate']
    Q_in = stearin_flow.attributes['heat_flow_rate']
    Q_out = (stearin_in * coeff['Heat of Fusion']) + (stearin_in * C_pstearin * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    electricity_in = stearin_in * coeff['Electricity (kw/kg)'] 
    print('Unit 13')
    return[{'name' : 'Electricity (Stearin Melting)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Stearin Melting)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Stearin Melting)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Liquid Stearin', 'components' : ['Stearin'], 'composition' : [1], 'mass_flow_rate' : stearin_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit13.calculations = {'Stearin': Stearin_melting_func}
           
#Unit 14: Preheater
Unit14 = Unit('Preheater')
Unit14.expected_flows_in = ['Clean Olein', 'Steam (Olein Preaheat)']
Unit14.expected_flows_out = ['Hot Olein', 'Condensate (Olein Preaheat)']
Unit14.coefficients = {'loses': 0.10, 'Unit Temp': 70, 'Steam Temp': 100}

def Preaheater_func(olein_flow, coeff):
    olein_in = olein_flow.attributes['mass_flow_rate']
    Q_in = olein_flow.attributes['heat_flow_rate']
    Q_out = olein_in * C_polein * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 14')
    return[{'name' : 'Steam (Olein Preaheat)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Olein Preaheat)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Hot Olein', 'components' : ['Olein'], 'composition' : [1], 'mass_flow_rate' : olein_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit14.calculations = {'Clean Olein': Preaheater_func}

# Unit 15: Blender - A combination of 15 and 16 
Unit15 = Unit('Blender')
Unit15.required_calc_flows = 2
Unit15.expected_flows_in = ['Hot Olein', 'Liquid Stearin', 'Electricity (Blender)', 'Additives']
Unit15.expected_flows_out = ['Blended Oil']
Unit15.coefficients = {'Electricity (kw/kg)': 0.000, 'Addition ratio': 0.001}

def Blender_func(ablist, coeff):
    olein_flow = ablist[0]
    stearin_flow = ablist[1]
    oil_in = (olein_flow.attributes['mass_flow_rate']) + (stearin_flow.attributes['mass_flow_rate'])
    Q_in = (olein_flow.attributes['heat_flow_rate']) + (stearin_flow.attributes['heat_flow_rate'])
    additives_in = oil_in * coeff['Addition ratio']
    oil_out = oil_in + additives_in
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    print('Unit 15')
    return[{'name' : 'Blended Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in},
           {'name' : 'Electricity (Blender)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Additives', 'components' : ['Additives'], 'composition' : [1], 'mass_flow_rate' : additives_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit15.calculations = (['Hot Olein', 'Liquid Stearin'], Blender_func)
           
# Unit 17: Polishing
Unit17 = Unit('Polisher')
Unit17.expected_flows_in = ['Blended Oil', 'Electricity (Polishing)']
Unit17.expected_flows_out = ['Finished Oil']
Unit17.coefficients = {'Electricity (kw/kg)': 0.000}

def Polishing_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    electricity_in = oil_in * coeff['Electricity (kw/kg)']
    Q_loss = oil_flow.attributes['heat_flow_rate']
    print('Unit 17')
    return[{'name' : 'Electricity (Polishing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Finished Oil', 'components' : ['Oil'], 'composition' : [1], 'mass_flow_rate' : oil_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]

Unit17.calculations = {'Blended Oil': Polishing_func}

#################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7,
                Unit9, Unit10, Unit11, Unit12, Unit13, Unit14, Unit15, Unit17]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    print(flow)


#utilities_recap('heat_intensity_fats_oil_blending', allflows, processunits)


