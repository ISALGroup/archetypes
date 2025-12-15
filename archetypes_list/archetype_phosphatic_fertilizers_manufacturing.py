'''
Name: Aidan J ONeil 
Date: September 4th, 2025


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
C_pmap = (1.21 + 1.35)/2


##################################################################### UNITS #######################################################################################
# Unit 1: Blending and Grinding 
Unit1 = Unit('Blending and Grinding')
Unit1.temperature = ambient_t 
Unit1.unit_type = 'Mixer'
Unit1.expected_flows_in = ['Phosphate Rock', 'Electricity (Grinding)']
Unit1.expected_flows_out = ['Phosphate Powder']
Unit1.coefficients = {'Electricity (kw/kg)': 0.03 }

def Grinding_and_blending_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 1')
    return[{'name' : 'Electricity (Grinding)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Phosphate Powder', 'components' : ['Phosphate'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': 0}]
Unit1.calculations = {'Phosphate Rock': Grinding_and_blending_func}
FlowA = Flow(name = 'Phosphate Rock', components = ['Phosphate'], composition = [1] , flow_type = 'input', mass_flow_rate = mass_in)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Reactor - 70 to 80 degrees - is this an exothermic reaction? What is heating it up 
Unit2 = Unit('Reactor')
Unit2.temperature = 75
Unit2.unit_type = 'Reactor'
Unit2.expected_flows_in = ['Water (Reactor)', 'Electricity (Reactor)', 'Phosphate Powder', 'Sulfuric Acid']
Unit2.expected_flows_out = ['Process Stream 1']
Unit2.coefficients = {'Electricity (kw/kg)': .023, 'Water to Feed': (34080/102240), 'H2SO4 to Feed': (109935/102240), 'H3PO4 ratio': (84770/102240), 
                      'Unit Temp': Unit2.temperature, 'Heat of rxn (kJ/kg)': 160}

def Reactor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    water_in = feed_in * coeff['Water to Feed']
    h2so4_in = feed_in * coeff['H2SO4 to Feed']
    feed_out = feed_in + water_in + h2so4_in
    h3po4_out = coeff['H3PO4 ratio'] * feed_in 
    h3po4_wt = h3po4_out / feed_out 
    other_wt = 1 - h3po4_wt
    Q_out = coeff['Heat of rxn (kJ/kg)'] * feed_in 
    print('Unit 2')
    return[{'name' : 'Electricity (Reactor)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Water (Reactor)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Sulfuric Acid', 'components' : ['H2SO4'], 'composition' : [1], 'mass_flow_rate' : h2so4_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Process Stream 1', 'components' : ['H3PO4', 'Other'], 'composition' : [h3po4_wt, other_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'Heat of reaction': Q_out}]
Unit2.calculations = {'Phosphate Powder': Reactor_func}

# Unit3 : Filtration - is the mass ratio after filtration 50/50 h3po4 to water
Unit3 = Unit('Filtration')
Unit3.temperature = Unit2.temperature
Unit3.unit_type = 'Seperator'
Unit3.expected_flows_in = ['Electricity (Filtration)', 'Water (Filtration)', 'Process Stream 1']
Unit3.expected_flows_out = ['Wastewater (Filtration)', 'Process Stream 2']
Unit3.coefficients = {'Water Ratio': (42995/113600), 'Electricity (kw/kg)': 0.013, 'Unit Temp': Unit3.temperature}

def Filtration_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    water_in = feed_in * coeff['Water Ratio']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 3')
    return[{'name' : 'Electricity (Filtration)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
           {'name' : 'Process Stream 2', 'components' : ['H3PO4', 'Water'], 'composition' : [.50, .50], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}, 
            {'name' : 'Water (Filtration)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
             {'name' : 'Wastewater (Filtration)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in,
             'flow_type': 'Water', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit3.calculations = {'Process Stream 1': Filtration_func}

# Unit 4: Evaporator 
Unit4 = Unit('Evaporator')
Unit4.temperature = 102.5            
Unit4.unit_type = 'Seperator'
Unit4.expected_flows_in = ['Process Stream 2', 'Electricity (Evaporator)', 'Steam (Evaporator)']
Unit4.expected_flows_out = ['Process Stream 3', 'Condensate (Evaporator)']
Unit4.coefficients = {'Steam Economy': 3.5, 'loses': 0.10, 'Outlet water wt': .25, 'Steam Temp': 115, 'Electricity (kw/kg)': 0.02, 'Unit Temp': Unit4.temperature}

def Evaporator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    solids_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('H3PO4')])
    feed_out = solids_in / (1-coeff['Outlet water wt'])
    water_out = feed_in - feed_out 
    m_steam = water_out / coeff['Steam Economy']
    Q_steam = m_steam * Hvap 
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss
    electricity_in = coeff['Electricity (kw/kg)']
    print('Unit 4')
    return[{'name' : 'Steam (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
            {'name' : 'Condensate (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam+water_out,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
            {'Heat loss': Q_loss}, 
            {'name' : 'Electricity (Evaporator)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Process Stream 3', 'components' : ['H3PO4', 'Water'], 'composition' : [1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}]
Unit4.calculations = {'Process Stream 2': Evaporator_func}

# Unit 5: MAP Reactor - What is the heat of reaction for this reaction and what are the outlet weight percentages of this unit 
Unit5 = Unit('MAP Reactor')
Unit5.temperature = 110     # 100 - 120
Unit5.unit_type = 'Reactor'
Unit5.expected_flows_in = ['Process Stream 3', 'Ammonia', 'Electricity (MAP Reactor)']
Unit5.expected_flows_out = ['Process Stream 4']
Unit5.coefficients = {'Heat of rxn (kJ/kg)': 1354.6, 'Ammonia to Feed': (22328/113600), 'Electricity (kw/kg)': 0.007, 'Unit Temp': Unit5.temperature}

def MAP_reactor_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_rxn = feed_in * .355 * coeff['Heat of rxn (kJ/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = Q_rxn + Q_in 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    ammonia_in = feed_in * coeff['Ammonia to Feed']
    feed_out = ammonia_in + feed_in 
    print('Unit 5') 
    return[{'name' : 'Electricity (MAP Reactor)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
            {'name' : 'Process Stream 4', 'components' : ['MAP', 'DAP', 'Water'], 'composition' : [.355, .433, .212], 'mass_flow_rate': feed_out,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'Heat of reaction': Q_rxn}, 
             {'name' : 'Ammonia', 'components' : ['NH3'], 'composition' : [1], 'mass_flow_rate': ammonia_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': Unit4.temperature, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit5.calculations = {'Process Stream 3': MAP_reactor_func}

# Unit 6: Granulation 
Unit6 = Unit('Granulation')
Unit6.temperature = Unit5.temperature
Unit6.unit_type = 'Mechanical Process'
Unit6.expected_flows_in = ['Process Stream 4', 'Electricity (Granulation)']
Unit6.expected_flows_out = ['Granules']
Unit6.coefficients = {'Electricity (kw/kg)': 0.008}

def Granualtion_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 6')
    return[{'name' : 'Electricity (Granulation)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in},
            {'name' : 'Granules', 'components' : ['MAP', 'DAP', 'Water'], 'composition' : [.355, .433, .212], 'mass_flow_rate': feed_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': Unit5.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit6.calculations = {'Process Stream 4': Granualtion_func}

# Unit 7: Dryer
Unit7 = Unit('Dryer')
Unit7.temperature = 120 
Unit7.unit_type = 'Seperator'
Unit7.expected_flows_in = ['Granules', 'Fuel (Dryer)', 'Electricity (Dryer)']
Unit7.expected_flows_out = ['Exhaust (Dryer)', 'Dried Granules']
Unit7.coefficients = {'Outlet water wt': 0.015, 'loses': 0.10, 'Fuel HHV': 5200, 'Unit Temp': Unit7.temperature, 'Electricity (kw/kg)': 0.006, 
                      'Fuel Demand (kJ/kg evap)': 5000}

def Dryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    solids_in = feed_in - water_in 
    feed_out = (solids_in) / (1-coeff['Outlet water wt'])
    water_evap = feed_in - feed_out 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_fuel = coeff['Fuel Demand (kJ/kg evap)'] * water_evap
    Q_loss = Q_fuel * coeff['loses']
    Q_in = feed_flow.attributes['heat_flow_rate']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    Q_out = Q_in + Q_fuel - Q_loss
    print('Unit 7')
    return[{'name' : 'Electricity (Dryer)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Dried Granules', 'components' : ['MAP', 'DAP', 'Water'], 'composition' : [.444, .541, coeff['Outlet water wt']], 'mass_flow_rate': feed_out,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': Unit6.temperature, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
             {'Heat loss': Q_loss}, 
            {'name' : 'Fuel (Dryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
             {'name' : 'Exhaust (Dryer)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel+ water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0, 'combustion_energy_content': 0}]
Unit7.calculations = {'Granules': Dryer_func}

# Unit 8: Cooler 
Unit8 = Unit('Cooler')
Unit8.temperature = ambient_t
Unit8.unit_type = 'Other'
Unit8.expected_flows_in = ['Dried Granules', 'Electricity (Cooler)', 'Cool Air (Cooler)']
Unit8.expected_flows_out = ['Cool Granules', 'Air (Cooler)']
Unit8.coefficients = {'Unit Temp': ambient_t, 'Air Ratio': 10, "Electricity (kw/kg)": 0.004}

def Cooler_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = 0
    Q_chilled_air = -Q_in
    m_air = coeff['Air Ratio'] * feed_in 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 8')
    return[{'name' : 'Electricity (Cooler)', 'components' : None, 'mass_flow_rate' : 0,
            'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Cool Granules', 'components' : ['MAP', 'DAP', 'Water'], 'composition' : [.444, .541, 0.015], 'mass_flow_rate': feed_in,
             'flow_type': 'Process stream', 'elec_flow_rate' : 0, 'temperature': coeff['Unit Temp'], 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Cool Air (Cooler)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate': m_air,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': 10, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilled_air}, 
             {'name' : 'Air (Cooler)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate': m_air,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit8.calculations = {'Dried Granules': Cooler_func}

# Unit 9: Finishing 
Unit9 = Unit('Blending and Grinding')
Unit9.temperature = ambient_t 
Unit9.unit_type = 'Mixer'
Unit9.expected_flows_in = ['Cool Granules', 'Electricity (Finishing)']
Unit9.expected_flows_out = ['Product Granules']
Unit9.coefficients = {'Electricity (kw/kg)': 0.003 }

def Finishing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 9')
    return[{'name' : 'Electricity (Finishing)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_in}, 
            {'name' : 'Product Granules', 'components' : ['Product'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit9.calculations = {'Cool Granules': Finishing_func}

##########################################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
        if flow.attributes['flow_type'] == 'Product': 
            print(flow)

utilities_recap('heat_intensity_phosphatic_fertilizer_2', allflows, processunits)






