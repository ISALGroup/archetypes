'''
Name: Aidan O'Neil 
Date: 9/8/2025
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
material_input = 1000
C_pw = 4.21
Hvap = 2260

############################################################### UNITS ##############################################################
# Unit 1: Recieving and Hanging 
Unit1 = Unit('Recieving')
Unit1.temperature = ambient_t
Unit1.unit_type = 'Other'
Unit1.expected_flows_in = ['Live Chicken', 'Electricity (Recieving)']
Unit1.expected_flows_out = ['Recieved Chickens']
Unit1.coefficients = {'Electricity (kw/kg)': 0.000}

def Recieving_func(feed_flow, coeff): 
    chicken_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = chicken_in * coeff['Electricity (kw/kg)']
    print('Unit 1')
    return[{'name' : 'Electricity (Recieving)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Recieved Chickens', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : chicken_in,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit1.calculations = {'Live Chicken': Recieving_func}
FlowA = Flow('Live Chicken',['Chicken'],'input', ambient_t, 1, [1], None , None, material_input, np.nan, 0)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Stunning 
Unit2 = Unit('Stunning')
Unit2.temperature = ambient_t
Unit2.unit_type = 'Other'
Unit2.expected_flows_in = ['Recieved Chickens', 'Electricity (Stunning)']
Unit2.expected_flows_out = ['Stunned Chickens']
Unit2.coefficients = {'Electricity (kw/kg)': 0.000}

def Stunning_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 2')
    return[{'name' : 'Electricity (Stunning)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Stunned Chickens', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit2.calculations = {'Recieved Chickens': Stunning_func}

# Unit 3: Slaughtering - Do we want to include blood drying...? 
Unit3 = Unit('Slaughtering')
Unit3.temperature = ambient_t
Unit3.unit_type = 'Seperator'
Unit3.expected_flows_in = ['Stunned Chickens']
Unit3.expected_flows_out = ['Blood', 'Carcuss Chicken']
Unit3.coefficients = {'Blood wt %': 0.08}

def Slaughtering_func(feed_flow, coeff): 
    chicken_in = feed_flow.attributes['mass_flow_rate']
    blood_out = chicken_in * coeff['Blood wt %']
    chicken_out = chicken_in - blood_out
    print('Unit 3')
    return[{'name' : 'Carcuss Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : chicken_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Blood', 'components' : ['Blood'], 'composition':  [1], 'mass_flow_rate' : blood_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit3.calculations = {'Stunned Chickens': Slaughtering_func}

# Unit 10: Blood Dryer 
Unit10 = Unit('Blood Processer')
Unit10.temperature = ambient_t
Unit10.unit_type = 'Mixer'
Unit10.expected_flows_in = ['Blood', 'Water (Blood Processer)', 'Electricity (Blood Processer)']
Unit10.expected_flows_out = ['Waste Water (Blood Processer)', 'Blood to Dryer']
Unit10.coefficients = {'Water to Blood Ratio': 0.75, 'Electricty (kw/kg)': 0.15}

def Blood_processer_func(blood_flow, coeff):
    blood_in = blood_flow.attributes['mass_flow_rate']
    electricity_in = blood_in * coeff['Electricty (kw/kg)']
    water_in = blood_in * coeff['Water to Blood Ratio']
    print('Blood Processor')
    return[{'name' : 'Electricity (Blood Processer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Blood to Dryer', 'components' : ['Blood'], 'composition' :[1], 'mass_flow_rate' : blood_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0},
           {'name' : 'Water (Blood Processer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Waster Water (Blood Processer)', 'components' : ['Water'], 'composition' :[1], 'mass_flow_rate' : water_in,
             'flow_type': 'Waste Water', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit10.calculations = {'Blood': Blood_processer_func}

# Unit 11: Blood Dryer 
Unit11 = Unit('Blood Dryer')
Unit11.temperature = 80
Unit11.unit_type = 'Mixer'
Unit11.expected_flows_in = ['Blood to Dryer', 'Steam (Blood Dryer)', 'Electricity (Blood Dryer)']
Unit11.expected_flows_out = ['Condensate (Blood Dryer)', 'Waste Water (Blood Dryer)', 'Feed Suppliment']

Unit11.coefficients = {'Inlet Water wt%': .70, 'Outlet Water wt%': .12, 'Unit Temp': 80, 'Steam Temp': 110,
                      'C_pfeed': 3.6, 'loses': .10, 'Electricity (kw/kg)': 0.25}

def Blood_dryer_func(blood_flow, coeff):
    blood_in = blood_flow.attributes['mass_flow_rate']
    water_in = blood_in * coeff['Inlet Water wt%']
    feed_out = (blood_in - water_in) / (1- coeff['Outlet Water wt%'])
    water_evap = blood_in - feed_out
    electricity_in = feed_out * coeff['Electricity (kw/kg)']
    Q_in = blood_flow.attributes['heat_flow_rate']
    Q_waterevap = (water_evap * C_pw * (100 - ambient_t)) + (water_evap * Hvap)
    Q_out = feed_out * coeff['C_pfeed'] * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_waterevap + Q_out - Q_in) / (1- coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    print('Blood Dryer')
    return[{'name' : 'Steam (Blood Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Blood Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Condensate', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Waste Water (Blood Dryer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': water_evap,
             'flow_type': 'Waste Water', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_waterevap},
           {'name' : 'Electricity (Blood Dryer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Feed Suppliment', 'components' : ['Feed'], 'composition' :[1], 'mass_flow_rate' : feed_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out}]
Unit11.calculations = {'Blood to Dryer': Blood_dryer_func}

# Unit 4: Scalding - what is the temperature of this unit
Unit4 = Unit('Scalding')
Unit4.temperature = 55
Unit4.unit_type = 'Other'
Unit4.expected_flows_in = ['Carcuss Chicken', 'Steam (Scalding)']
Unit4.expected_flows_out = ['Scalded Chicken', 'Condensate (Scalding)']
Unit4.coefficients = {'loses': 0.10, 'Steam Temp': 100, 'C_pchicken': 3.22, 'Unit Temp': Unit4.temperature}

def Scalding_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * coeff['C_pchicken'] * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses'] 
    m_steam = Q_steam / Hvap
    print('Unit 4')
    return[{'name' : 'Scalded Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_out ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Steam (Scalding)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
            {'name' : 'Condensate (Scalding)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
            'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}]
Unit4.calculations = {'Carcuss Chicken': Scalding_func}

# Unit 5: Defeathering 
Unit5 = Unit('Defeathering')
Unit5.temperature = ambient_t 
Unit5.unit_type = 'Mechanical Process'
Unit5.expected_flows_in = ['Scalded Chicken']
Unit5.expected_flows_out = ['Feathers', 'Defeathered Chicken']
Unit5.coefficients = {'Feather wt': 0.065}

def Defeathering_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    feathers_out = feed_in * coeff['Feather wt']
    feed_out = feed_in - feathers_out
    Q_loss = feed_flow.attributes['heat_flow_rate']
    print('Unit 5')
    return[{'name' : 'Defeathered Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Feathers', 'components' : ['Feathers'], 'composition':  [1], 'mass_flow_rate' : feathers_out,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_loss ,'In or out' : 'Out', 'Set calc' : False}]
Unit5.calculations = {'Scalded Chicken': Defeathering_func}

# Unit 6: Evisceration 
Unit6 = Unit('Evisceration')
Unit6.temperature = ambient_t
Unit6.unit_type = 'Seperator'
Unit6.expected_flows_in = ['Defeathered Chicken']
Unit6.expected_flows_out = ['Viscera', 'Eviscerated Chicken']
Unit6.coefficients = {'Viscera wt': 0.175}

def Evisceration_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    viscera_out = feed_in * coeff['Viscera wt']
    feed_out = feed_in - viscera_out
    print('Unit 6')
    return[{'name' : 'Eviscerated Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Viscera', 'components' : ['Viscera'], 'composition':  [1], 'mass_flow_rate' : viscera_out,
            'flow_type': 'Process Stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit6.calculations = {'Defeathered Chicken': Evisceration_func}

# Unit 12: Viscera Processing 
Unit12 = Unit('Visceria Proceser')
Unit12.temperature = 135
Unit12.unit_type = 'Seperator'
Unit12.expected_flows_in = ['Viscera', 'Steam (Processer)']
Unit12.expected_flows_out = ['Tripe', 'Waste Water (Processer)']
Unit12.coefficients = {'Waste': (20/100), 'Unit Temp': (Unit12.temperature), 'Steam Temp': (Unit12.temperature + 10), 'loses': 0.10, 'C_pviscera': 3.522}

def Viscera_processing_func(viscera_flow, coeff):
    viscera_in = viscera_flow.attributes['mass_flow_rate']
    waste_out = viscera_in * coeff['Waste']
    Q_in = viscera_flow.attributes['heat_flow_rate']
    Q_out = viscera_in * coeff['C_pviscera'] * (coeff['Unit Temp'] - ambient_t)
    Q_waste = viscera_in * C_pw * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out + Q_waste - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    viscera_out = viscera_in - waste_out
    wastewater_out = waste_out + m_steam
    print('Processer')
    return[{'name' : 'Steam (Processer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Waste Water (Processer)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate': wastewater_out,
             'flow_type': 'Wastewater', 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_waste},
           {'Heat loss': Q_loss},
           {'name' : 'Tripe', 'components' : ['Tripe'], 'composition' :[1], 'mass_flow_rate' : viscera_out,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out}]

Unit12.calculations = {'Viscera': Viscera_processing_func}

# Unit 7: Cleaning 
Unit7 = Unit('Cleaning')
Unit7.temperature = ambient_t
Unit7.unit_type = 'Seperator'
Unit7.expected_flows_in = ['Water (Cleaning)', 'Eviscerated Chicken']
Unit7.expected_flows_out = ['Wastewater (Cleaning)', 'Cleaned Chicken']
Unit7.coefficients = {'Water Ratio': 2}

def Cleaning_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    m_water = feed_in * coeff['Water Ratio']
    print('Unit 7')
    return[{'name' : 'Cleaned Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Water (Cleaning)', 'components' : 'Water', 'mass_flow_rate' : m_water,
             'flow_type': 'Water', 'Temperature': ambient_t, 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
            {'name' : 'Wastewater (Cleaning)', 'components' : 'Water', 'mass_flow_rate' : m_water,
            'flow_type': 'Wastewater', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit7.calculations = {'Eviscerated Chicken': Cleaning_func}

# Unit 8: Chilling 
Unit8 = Unit('Chilling')
Unit8.temperature = 0
Unit8.unit_type = 'Other'
Unit8.expected_flows_in = ['Cleaned Chicken', 'Chilling Demand (Cooling)']
Unit8.expected_flows_out = ['Cooled Chicken']
Unit8.coefficients = {'C_pchicken': 3.22, 'Unit Temp': Unit8.temperature}

def Chilling_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pw * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out  - Q_in
    print('Unit 8')
    return[{'name' : 'Cooled Chicken', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_out ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Chilling Demand (Cooling)', 'components' : 'Water', 'mass_flow_rate' : 0,
             'flow_type': 'Chilling Demand', 'Temperature': coeff['Unit Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit8.calculations = {'Cleaned Chicken': Chilling_func}

# Unit 9: Second Processing
Unit9 = Unit('Second Processing')
Unit9.temperature = Unit8.temperature
Unit9.unit_type = 'Mechanical Process'
Unit9.expected_flows_in = ['Cooled Chicken', 'Electricity (Second Processing)']
Unit9.expected_flows_out = ['Product Chicken']
Unit9.coefficients = {'Electricity (kw/kg)': 0.0}

def Second_processing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = coeff['Electricity (kw/kg)'] * feed_in 
    print('Unit 9')
    return[{'name' : 'Electricity (Second Processing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Product Chickens', 'components' : ['Chicken'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Product', 'heat_flow_rate': Q_in ,'In or out' : 'Out', 'Set calc' : True}]
Unit9.calculations = {'Cooled Chicken': Second_processing_func}

######################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, Unit10, 
                Unit11, Unit12]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_poultry_2', allflows, processunits)


