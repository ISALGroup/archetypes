# -*- coding: utf-8 -*-
"""
Created on Wednesday September 3rd 12:00:00 pm

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
mass_in = 1000
feed_air_in = mass_in * (7414.925/627)
C_pair = 1.000
heat_exchange_temp = 540
C_poil = 1.70
C_pcb = .70
rxn_yield = .6




############################################################### UNITS #############################################################################
# Unit 1: Feed Preheater
Unit1 = Unit('Feed Preheater')
Unit1.temperature = 300 
Unit1.unit_type = 'Mixer'
Unit1.expected_flows_in = ['Feed Oil', 'Hot Air', 'Steam (Feed Preheater)', 'Additives']
Unit1.expected_flows_out = ['Reactor Feed', 'Condensate (Feed Preheater)']
Unit1.coefficients = {'Steam Temp': 100, 'Unit Temp': Unit1.temperature, 'loses': 0.10, 'Additives ratio': 0.012}

def Feed_preheater_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    additives_in = feed_in * coeff['Additives ratio']
    Q_in = feed_flow.attributes['heat_flow_rate']
    air_in = feed_air_in 
    Q_air_in = air_in * C_pair * (heat_exchange_temp - ambient_t)
    feed_out = feed_in + air_in + additives_in
    Q_out = feed_in * C_poil * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) // (1 - coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    air_wt = air_in / feed_out 
    oil_wt = 1 - air_wt
    print('Unit 1') 
    return[{'name' : 'Reactor Feed', 'components' : ['Oil', 'Air'], 'composition' : [oil_wt, air_wt], 'mass_flow_rate' : feed_out,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out + Q_air_in}, 
           {'name' : 'Hot Air', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': heat_exchange_temp, 'In or out' : 'In', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': Q_air_in}, 
           {'name' : 'Steam (Feed Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Feed Preheater)', 'components' : 'Water', 'mass_flow_rate' : m_steam ,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
           {'Heat loss': Q_loss},
           {'name' : 'Additives', 'components' : ['Additives'], 'composition' : [1], 'mass_flow_rate' : additives_in,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit1.calculations = {'Feed Oil': Feed_preheater_func}
FlowA = Flow(name = 'Feed Oil', components = ['Oil'], composition = [1] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Reactor 
Unit2 = Unit('Reactor')
Unit2.temperature = 1400
Unit2.unit_type = 'Reactor'
Unit2.expected_flows_in = ['Reactor Feed', 'Fuel (Reactor)']
Unit2.expected_flows_out = ['Process Flow 1', 'Spent Fuel (Reactor)']
Unit2.coefficients = {'Yield': rxn_yield, 'Heat of rxn (kj/kg)': 24200, 'Unit Temp': Unit2.temperature, 'loses': 0.10, 'Fuel HHV': 5200, 'Fuel Demand (kJ/kg)': 5167.63}

def Reactor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    carbon_black_out = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Oil')]) * coeff['Yield']
    air_in = (feed_in * feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Air')])
    oil_in = feed_in - carbon_black_out - air_in
    Q_rxn = coeff['Heat of rxn (kj/kg)'] * carbon_black_out
    Q_fuel = coeff['Fuel Demand (kJ/kg)'] * mass_in
    Q_loss = Q_fuel * coeff['loses']
    Q_out = Q_in + Q_fuel - Q_loss 
    m_fuel = Q_fuel / coeff['Fuel HHV']
    carbon_black_wt = carbon_black_out / feed_in
    air_wt = air_in / feed_in
    oil_wt = 1 - air_wt - carbon_black_wt
    print('Unit 2')
    return[{'name' : 'Process Flow 1', 'components' : ['Carbon Black', 'Oil', 'Air'], 'composition' : [carbon_black_wt, oil_wt, air_wt], 'mass_flow_rate' : feed_in,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
           {'name' : 'Fuel (Reactor)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Spent Fuel (Reactor)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0, 'combustion_energy_content': 0},
           {'Heat loss': Q_loss}]
Unit2.calculations = {'Reactor Feed': Reactor_func}

# Unit 3: Heat Exchanger 
Unit3 = Unit('Heat Exchanger')
Unit3.temperature = heat_exchange_temp 
Unit3.unit_type = 'Other'
Unit3.expected_flows_in = ['Feed Air', 'Process Flow 1']
Unit3.expected_flows_out = ['Process Flow 2', 'Hot Air']
Unit3.coefficients = {}

def Heat_exchanger_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    black_carbon_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Carbon Black')])
    Q_in = feed_flow.attributes['heat_flow_rate']
    air_out = feed_air_in
    Q_air_out = air_out * C_pair * (heat_exchange_temp - ambient_t)
    feed_out = feed_in - air_out 
    carbon_black_wt = black_carbon_in / feed_out 
    other_wt = 1 - carbon_black_wt
    Q_out = Q_in - Q_air_out 
    print('Unit 3')
    return[{'name' : 'Hot Air', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_out,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': heat_exchange_temp, 'In or out' : 'Out', 'Set calc' : False, 'Set shear': True, 'heat_flow_rate': Q_air_out}, 
           {'name' : 'Feed Air', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : 0,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'Set shear': 0, 'heat_flow_rate': 0}, 
           {'name' : 'Process Flow 2', 'components' : ['Carbon Black', 'Oil'], 'composition' : [carbon_black_wt, other_wt], 'mass_flow_rate' : feed_out,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': heat_exchange_temp, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit3.calculations = {'Process Flow 1': Heat_exchanger_func}

# Unit 8: Bag Filter 
Unit8 = Unit('Bag Filter')
Unit8.temperature = heat_exchange_temp
Unit8.unit_type = 'Seperator'
Unit8.expected_flows_in = ['Process Flow 2', 'Electricity (Bag Filter)']
Unit8.expected_flows_out = ['Unpure Carbon Black', 'Waste to Fire Box']
Unit8.coefficients = {'Electricity (kw/kg)': 0.22}

def Bag_filter_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    black_carbon_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Carbon Black')])
    electricity_in = black_carbon_in * coeff['Electricity (kw/kg)']
    waste_out = feed_in - black_carbon_in
    Q_carbonblack = (black_carbon_in / feed_in) * Q_in
    Q_waste = Q_in - Q_carbonblack
    print('Unit 8')
    return[{'name' : 'Unpure Carbon Black', 'components' : ['Carbon Black'], 'composition' : [1], 'mass_flow_rate' : black_carbon_in,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': heat_exchange_temp, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_carbonblack}, 
           {'name' : 'Waste to Fire Box', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : waste_out,
           'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': heat_exchange_temp, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_waste}, 
           {'name' : 'Electricity (Bag Filter)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}]
Unit8.calculations = {'Process Flow 2': Bag_filter_func}

# Unit 9: Fire Box
Unit9 = Unit('Fire Box')
Unit9.temperature = 980
Unit9.unit_type = 'Other'
Unit9.expected_flows_in = ['Fuel (Fire Box)', 'Waste to Fire Box', 'Electricity (Fire Box)', 'Water (Fire Box)']
Unit9.expected_flows_out = ['Stack']
Unit9.coefficients = {'Fuel Demand (kJ/kg)': (3 * 1.055 * 1000), 'Water Demand (kg/kg)': 0.54, 'Electricity Demand': 0.002, 'Unit Temp': Unit9.temperature}

def Fire_box_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_fuel = mass_in * rxn_yield * coeff['Fuel Demand (kJ/kg)']
    electricity_in = mass_in * rxn_yield * coeff['Electricity Demand']
    water_in = mass_in * rxn_yield * coeff['Water Demand (kg/kg)']
    feed_out = feed_in + water_in 
    Q_out = Q_in + Q_fuel 
    print('Unit 9')
    return[{'name' : 'Electricity (Fire Box)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
             {'name' : 'Stack', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : feed_out,
              'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out}, 
              {'name' : 'Fuel (Fire Box)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel}, 
             {'name' : 'Water (Fire Box)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
              'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Waste to Fire Box' : Fire_box_func}
# Unit 4: Quench 
Unit4 = Unit('Quench')
Unit4.temperature = 230 
Unit4.unit_type = 'Other'
Unit4.expected_flows_in = ['Unpure Carbon Black', 'Water (Quench)']
Unit4.expected_flows_out = ['Quenched Carbon Black', 'Hot Water (Quench)']
Unit4.coefficients = {'Unit Temp': Unit4.temperature, 'Water Demand (kg/kg)': 6}

def Quench_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pcb * (coeff['Unit Temp'] - ambient_t)
    water_in = feed_in * coeff['Water Demand (kg/kg)']
    Q_water = Q_in - Q_out 
    print((Q_water / (water_in * C_pw)) + ambient_t)
    print('Unit 4')
    return[{'name' : 'Water (Quench)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
              'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Hot Water (Quench)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
              'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_water}, 
            {'name' : 'Quenched Carbon Black', 'components' : ['Carbon Black'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Unpure Carbon Black': Quench_func}

# Unit 5: Pelletizing 
Unit5 = Unit('Pelletizer')
Unit5.temperature = ambient_t
Unit5.unit_type = 'Mixer'
Unit5.expected_flows_in = ['Quenched Carbon Black', 'Pellet Additives', 'Water (Pelletizer)']
Unit5.expected_flows_out = ['Carbon Pellets']
Unit5.coefficients = {'Water Demand (kg/kg)': 2, 'Additives Demand (kg/kg)': 0.0025}

def Pelletizing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    water_in = feed_in * coeff['Water Demand (kg/kg)']
    additives_in = feed_in * coeff['Additives Demand (kg/kg)']
    feed_out = water_in + feed_in + additives_in
    water_wt = water_in / feed_out 
    carbon_wt = 1 - water_wt 
    print('Unit 5')
    return[{'name' : 'Water (Pelletizer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
              'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Carbon Pellets', 'components' : ['Carbon Black', 'Water'], 'composition' : [carbon_wt, water_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Pellet Additives', 'components' : ['Additives'], 'composition' : [1], 'mass_flow_rate' : additives_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}]
Unit5.calculations = {'Quenched Carbon Black': Pelletizing_func}

# Unit 6: Dryer 
Unit6 = Unit('Dryer')
Unit6.temperature = ((190 + 230)/2)
Unit6.unit_type = 'Splitter'
Unit6.expected_flows_in = ['Carbon Pellets', 'Steam (Dryer)']
Unit6.expected_flows_out = ['Dry Pellets', 'Condensate (Dryer)', 'Exhaust (Dryer)']
Unit6.coefficients = {'Outlet water wt': .01, 'loses': 0.10, 'Unit Temp': Unit6.temperature, 'Steam Temp': (Unit6.temperature + 10), 'Steam Demand (kJ/kg)': 1477}

def Dryer_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    solids_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Carbon Black')])
    carbon_black_out = solids_in / (1 - coeff['Outlet water wt'])
    water_evap = feed_in - carbon_black_out 
    Q_steam = coeff['Steam Demand (kJ/kg)'] * carbon_black_out
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss
    m_steam = Q_steam / Hvap 
    print('Unit 6')
    return[{'name' : 'Dry Pellets', 'components' : ['Carbon Black', 'Water'], 'composition' : [1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : carbon_black_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Exhaust (Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Steam (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam ,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
           {'Heat loss': Q_loss}]
Unit6.calculations = {'Carbon Pellets': Dryer_func}

# Unit 7: Product Handling
Unit7 = Unit('Product Handling')
Unit7.temperature = ambient_t
Unit7.unit_type = 'Mechanical Process'
Unit7.expected_flows_in = ['Dry Pellets', 'Electricity (Product Handling)']
Unit7.expected_flows_out = ['Product Carbon']
Unit7.coefficients = {'Electricity (kw/kg)': 0.0165}

def Product_handling_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 7')
    return[{'name' : 'Product Carbon', 'components' : ['Carbon Black'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in}, 
            {'name' : 'Electricity (Product Handling)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}]
Unit7.calculations = {'Dry Pellets': Product_handling_func}

################################################################################################################################################

processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_carbon_black_3', allflows, processunits)
