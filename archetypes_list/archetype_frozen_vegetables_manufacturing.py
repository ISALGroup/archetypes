'''
Name: Aidan J ONeil 
Date: September 5th, 2025 


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
mass_out = mass_in * .8555

############################################################################## UNITS ########################################################
# Unit 1: Inspection and Grading 
Unit1 = Unit('Inspection')
Unit1.temperature = ambient_t
Unit1.unit_type = 'Seperator'
Unit1.expected_flows_in = ['Feed Material', 'Electricity (Inspection)']
Unit1.expected_flows_out = ['Waste (Inspection)', 'Graded Feed']
Unit1.coefficients = {'Electricity (kw/kg)': 11.6, 'Waste Ratio': 0.00}

def Inspection_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = coeff['Waste Ratio'] * feed_in
    feed_out = feed_in - waste_out 
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    print('Unit 1')
    return[{'name' : 'Electricity (Inspection)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Graded Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Waste (Inspection)', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit1.calculations = {'Feed Material': Inspection_func}
FlowA = Flow(name = 'Feed Material', components = ['Vegetables'], composition = [1] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Washing 
Unit2 = Unit('Washing')
Unit2.temperature = 40
Unit2.unit_type = 'Mixer'
Unit2.expected_flows_in = ['Electricity (Washer)', 'Hot Water (Washer)', 'Graded Feed']
Unit2.expected_flows_out = ['Wastewater (Washer)', 'Washed Feed']
Unit2.coefficients = {'Electricity (kw/kg)': 14.5, 'Hot Water Demand (kj/kg)': 400.7, 'Steam Temp': Unit2.temperature, 'loses': 0.10}

def Washing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_hotwater = mass_out * coeff['Hot Water Demand (kj/kg)'] / (1-coeff['loses'])
    Q_loss = Q_hotwater * coeff['loses']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_hotwater + Q_in - Q_loss
    water_in = Q_hotwater / (C_pw * (coeff['Steam Temp'] - ambient_t))
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    print('Unit 2')
    return[{'name' : 'Electricity (Washer)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Washed Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Hot Water (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature': Unit2.temperature, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_hotwater}, 
            {'name' : 'Wastewater (Washer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}]
Unit2.calculations = {'Graded Feed': Washing_func}

# Unit 3: Cutting 
Unit3 = Unit('Cutting')
Unit3.temperature = ambient_t 
Unit3.unit_type = 'Mechanical Process'
Unit3.expected_flows_in = ['Washed Feed', 'Electricity (Cutting)']
Unit3.expected_flows_out = ['Cut Feed']
Unit3.coefficients = {'Electricity (kw/kg)': 25.2}

def Cutting_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    print('Unit 3')
    return[{'name' : 'Electricity (Cutting)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Cut Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}]
Unit3.calculations = {'Washed Feed': Cutting_func}

# Unit 4: Scalding and Blanching 
Unit4 = Unit('Scalding and Blanching')
Unit4.temperature = 92.5
Unit4.unit_type = 'Other'
Unit4.expected_flows_in = ['Cut Feed', 'Hot Water (Scalding)']
Unit4.expected_flows_out = ['Blanched Feed', 'Wastewater (Scalding)']
Unit4.coefficients = {'Hot water demand (kJ/kg)': 370.1, 'Unit Temp': Unit4.temperature, 'loses': .10}

def Scalding_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_hotwater = mass_out * coeff['Hot water demand (kJ/kg)'] / (1-coeff['loses'])
    Q_loss = Q_hotwater * coeff['loses']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_hotwater + Q_in - Q_loss 
    m_water = Q_hotwater / (C_pw * (coeff['Unit Temp'] - ambient_t))
    print('Unit 4')
    return[{'name' : 'Blanched Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': Unit4.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Hot Water (Scalding)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : m_water,
             'flow_type': 'Steam', 'elec_flow_rate' : 0, 'temperature': Unit4.temperature, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_hotwater}, 
            {'name' : 'Wastewater (Scalding)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : m_water,
             'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}]
Unit4.calculations = {'Cut Feed': Scalding_func}

# Unit 5: Peeling 
Unit5 = Unit('Peeler')
Unit5.temperature = ambient_t 
Unit5.unit_type = "Mechanical Process"
Unit5.expected_flows_in = ['Blanched Feed', 'Electricity (Peeler)']
Unit5.expected_flows_out = ['Peels', 'Peeled Feed']
Unit5.coefficients = {'Peel wt %': 0.10, 'Electricity (kw/kg)': 14.4}

def Peeling_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    peels_out = feed_in * coeff['Peel wt %']
    feed_out = feed_in - peels_out 
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    print('Unit 5')
    return[{'name' : 'Electricity (Peeler)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Peeled Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Peels', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : peels_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss}]
Unit5.calculations = {'Blanched Feed': Peeling_func}

# Unit 6: Pulper 
Unit6 = Unit('Pulper')
Unit6.temperature = ambient_t 
Unit6.unit_type = 'Mechanical Process'
Unit6.expected_flows_in = ['Peeled Feed', 'Electricity (Pulper)']
Unit6.expected_flows_out = ['Pulp', 'Pulped Feed']
Unit6.coefficients = {'Waste Ratio': 0.02, 'Electricity (kw/kg)': 14.4}

def Pulping_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_loss = feed_flow.attributes['heat_flow_rate']
    pulp_out = feed_in * coeff['Waste Ratio']
    feed_out = feed_in - pulp_out 
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    print('Unit 6')
    return[{'name' : 'Electricity (Pulper)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Pulped Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Pulp', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : pulp_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_loss}]
Unit6.calculations = {'Peeled Feed': Pulping_func}

# Unit 7: Cooker - temp?
Unit7 = Unit('Cooker')
Unit7.temperature = 95
Unit7.unit_type = 'Other'
Unit7.expected_flows_in = ['Pulped Feed', 'Steam (Cooker)']
Unit7.expected_flows_out = ['Cooked Feed', 'Condensate (Cooker)']
Unit7.coefficients = {'Steam Demand (kJ/kg)': 370.1, 'loses': 0.10, 'Unit Temp': Unit7.temperature, 'Steam Temp': (Unit7.temperature + 10)}

def Cooker_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_steam = (mass_out * coeff['Steam Demand (kJ/kg)']) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_in + Q_steam - Q_loss 
    print('Unit 7')
    return[{'name' : 'Steam (Cooker)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
            {'name' : 'Condensate (Cooker)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss}, 
            {'name' : 'Cooked Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit7.calculations = {'Pulped Feed': Cooker_func}

# Unit 8: Fryer 
Unit8 = Unit('Fryer')
Unit8.temperature = 170
Unit8.unit_type = 'Other'
Unit8.expected_flows_in = ['Fuel (Fryer)', 'Cooked Feed']
Unit8.expected_flows_out = ['Exhaust (Fryer)', 'Fried Feed']
Unit8.coefficients = {'Fuel Demand (kJ/kg)': 755.9, 'loses': .10, 'Unit Temp': Unit8.temperature, 'Fuel HHV': 5200, 'Mass loss': 0.03}

def Fryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = feed_in * coeff['Mass loss']
    feed_out = feed_in - waste_out 
    Q_fuel = (mass_out * coeff['Fuel Demand (kJ/kg)']) / (1- coeff['loses'])
    m_fuel = Q_fuel / coeff['Fuel HHV']
    Q_loss = Q_fuel * coeff['loses']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_in + Q_fuel - Q_loss 
    exhaust_out = waste_out + m_fuel 
    print('Unit 8')
    return[{'name' : 'Fuel (Fryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Exhaust (Fryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : exhaust_out,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0, 'combustion_energy_content': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Fried Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}] 
Unit8.calculations = {'Cooked Feed': Fryer_func}

# Unit 9: Cooler and Washer 
Unit9 = Unit('Cooler and Washer')
Unit9.temperature = ambient_t 
Unit9.unit_type = 'Other'
Unit9.expected_flows_in = ['Fried Feed', 'Water (Cooler)', 'Electricity (Cooler)']
Unit9.expected_flows_out = ['Cooled Fried Feed', 'Wastewater (Cooler)']
Unit9.coefficients = {'Water Ratio': 5, 'Electricity (kw/kg)': 14.4, 'Unit Temp': Unit9.temperature}

def Cooler_washer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    water_in = feed_in * coeff['Water Ratio']
    Q_in = feed_flow.attributes['heat_flow_rate']
    del_t = Q_in / (water_in * C_pw)
    print(del_t)
    print('Unit 9')
    return[{'name' : 'Cooled Fried Feed', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}, 
            {'name' : 'Water (Cooler)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Wastewater (Cooler)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'temperature': (coeff['Unit Temp'] + del_t), 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_in}, 
            {'name' : 'Electricity (Cooler)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}]
Unit9.calculations = {'Fried Feed': Cooler_washer_func}

# Unit 10: Freezing 
Unit10 = Unit('Freezer')
Unit10.temperature = -18 
Unit10.unit_type = 'Other'
Unit10.expected_flows_in = ['Cooled Fried Feed', 'Electricity (Freezer)', 'Refridgeration']
Unit10.expected_flows_out = ['Product Vegetables']
Unit10.coefficients = {'Electricity (kw/kg)': 32.3, 'Refridgeration Demand (kJ/kg)': 2591.3}

def Freezer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = mass_out * coeff['Electricity (kw/kg)']
    refrig_in = mass_out * coeff['Refridgeration Demand (kJ/kg)']
    print('Unit 10')
    return[{'name' : 'Product Vegetables', 'components' : ['Vegetables'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Electricity (Freezer)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Refridgeration', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : refrig_in}]
Unit10.calculations = {'Cooled Fried Feed': Freezer_func}

###################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, Unit10]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_froozen_vegetables', allflows, processunits)
