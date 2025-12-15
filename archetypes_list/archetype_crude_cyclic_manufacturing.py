'''
Name: Aidan ONeil 
Date: September 22nd, 2025 


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
material_in = 1000
C_pw = 4.186
Hvap = 2257
C_pair = 1.00 

####################################################################################### UNITS ##############################################################################################################
# Unit 1: Vaporizer 
Unit1 = Unit('Vaporizer')
Unit1.temperature = 237
Unit1.unit_type = 'Mixer'
Unit1.expected_flows_in = ['Propylene', 'Benzene', 'Steam (Vaporizer)']
Unit1.expected_flows_out = ['Process Flow 1', 'Condensate (Vaporizer)']
Unit1.coefficients = {'Unit Temp': Unit1.temperature, 'Steam Temp': (Unit1.temperature + 10), 'loses': .10, 'Steam Demand (kJ/kg)': 122, 
                      'Propylene Mass Ratio': (4650/16170)}

def Vaproizer_func(feed_flow, coeff): 
    benzene_in = feed_flow.attributes['mass_flow_rate']
    p_in = benzene_in * coeff["Propylene Mass Ratio"]
    propane_in = p_in * 0.05 
    feed_out = p_in + benzene_in 
    benzene_wt = benzene_in / feed_out 
    propane_wt = propane_in / feed_out 
    prop_wt = 1 - benzene_wt - propane_wt
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_steam = ((benzene_in + p_in) * coeff['Steam Demand (kJ/kg)']) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss 
    m_steam = Q_steam / Hvap 
    print('Unit 1')
    return[{'name' : 'Steam (Vaporizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Vaporizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
            {'name' : 'Process Flow 1', 'components' : ['Propylene', 'Propane', 'Benzene'], 'composition' : [prop_wt, propane_wt, benzene_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out},
            {'name' : 'Propylene', 'components' : ['Propylene', 'Propane'], 'composition' : [.95, .05], 'mass_flow_rate' : p_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit1.calculations = {'Benzene': Vaproizer_func}
FlowA = Flow(name='Benzene', components = ['Benzene'], composition = [1], flow_type = 'input', mass_flow_rate = material_in, heat_flow_rate=0)
FlowA.set_calc_flow()
allflows.append(FlowA)
    
# Unit 2: Heater - Non-electrifiable?
Unit2 = Unit('Heater')
Unit2.temperature = 360 
Unit2.unit_type = 'Thermal Unit'
Unit2.expected_flows_in = ['Process Flow 1', 'Fuel (Heater)']
Unit2.expected_flows_out = ['Process Flow 2', 'Exhaust (Heater)']
Unit2.coefficients = {'Fuel Demand (kJ/kg)': 79, 'loses': 0.10, 'Unit Temp': Unit2.temperature, 'Fuel HHV': 5200}

def Heater_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_fuel = feed_in * coeff['Fuel Demand (kJ/kg)'] / (1-coeff['loses'])
    Q_loss = Q_fuel * coeff['loses']
    Q_out = Q_in + Q_fuel - Q_loss 
    m_fuel = Q_fuel / coeff['Fuel HHV'] 
    print('Unit 2')
    return[{'name' : 'Fuel (Heater)', 'components' : 'Water', 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'Heat loss': Q_loss}, 
           {'name' : 'Process Flow 2', 'components' : ['Propylene', 'Propane', 'Benzene'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Exhaust', 'components' : ['Exhaust'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit2.calculations = {'Process Flow 1': Heater_func}

# Unit 3: Reactor - what percent of this gets taken away by waste heat
Unit3 = Unit('Reactor')
Unit3.temperature = 427
Unit3.unit_type = 'Reactor'
Unit3.expected_flows_in = ['Process Flow 2']
Unit3.expected_flows_out = ['Process Flow 3', 'Wasteheat (Reactor)']
Unit3.coefficients = {'Heat of rxn (kJ/mol)': 79, 'Heat Recovered': 0.25}

def Reactor_func(feed_flow, coeff): 
   feed_in = feed_flow.attributes['mass_flow_rate'] 
   Q_in = feed_flow.attributes['heat_flow_rate']
   benzene_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Benzene')])
   mol_benzene = benzene_in / 78.11
   Q_rxn = mol_benzene * coeff['Heat of rxn (kJ/mol)']
   Q_avail = Q_rxn * coeff['Heat Recovered']
   Q_out = Q_in + (Q_rxn - Q_avail)
   print('Unit 3')
   return[{'name' : 'Process Flow 3', 'components' : ['Products'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'Heat of reaction': Q_rxn},
            {'name' : 'Wasteheat (Reactor)', 'components' : ['None'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Wasteheat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_avail}]
Unit3.calculations = {'Process Flow 2': Reactor_func}

# Unit 4: Cooler - I need to know the C_p for this 
Unit4 = Unit('Cooler')
Unit4.temperature = 90 
Unit4.unit_type = 'Thermal Unit'
Unit4.expected_flows_in = ['Process Flow 3', 'Coolant (Cooler)']
Unit4.expected_flows_out = ['Process Flow 4']
Unit4.coefficients = {'Unit Temp': Unit4.temperature}

def Cooler_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    C_Pflow = 2.0 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_out = feed_in * C_Pflow * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 4')
    return[{'name' : 'Process Flow 4', 'components' : ['Products'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Coolant (Cooler)', 'components' : ['Chilling'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit4.calculations = {'Process Flow 3': Cooler_func}

# Unit 5: Flash Tank 
Unit5 = Unit('Flash Tank')
Unit5.temperature = Unit4.temperature
Unit5.unit_type = 'Seperator'
Unit5.expected_flows_in = ['Process Flow 4']
Unit5.expected_flows_out = ['Gas Flow', 'Liquid Flow']
Unit5.coefficients = {}

def Flash_tank_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate'] 
    Q_in = feed_flow.attributes['heat_flow_rate']
    PDIB_in = feed_in * 0.0002
    liquid_out = PDIB_in / 0.001 
    gas_out = feed_in - liquid_out
    Q_saved = (liquid_out / feed_in) * Q_in
    Q_lost = Q_in - Q_saved
    liquid_out_components = ['Propylene','Propane','Benzene', 'Cumene','PDIB']
    liquid_out_composition = [0.009, 0.001, 0.946, 0.043, 0.001]
    gas_out_components = ['Propylene','Propane','Benzene', 'Cumene']
    gas_out_composition = [0.267, 0.011, 0.718, 0.003]
    print('Unit 5')
    return[{'name' : 'Liquid Flow', 'components' : liquid_out_components, 'composition' : liquid_out_composition, 'mass_flow_rate' : liquid_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_saved}, 
            {'name' : 'Gas Flow', 'components' : gas_out_components, 'composition' : gas_out_composition, 'mass_flow_rate' : gas_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_lost}]
Unit5.calculations = {'Process Flow 4': Flash_tank_func}

# Unit 6: Benzene Distillation - using the material input
Unit6 = Unit('Benzene Distillation')
Unit6.temperature = 214 
Unit6.unit_type = 'Seperator'
Unit6.expected_flows_in = ['Liquid Flow', 'Steam (Benzene Distillation)']
Unit6.expected_flows_out = ['Bottoms', 'Cumene', 'Unreacted Benzene']
Unit6.coefficients = {'Steam Demand (kJ/kg)': ((2185915 + 140333)/ 16170), 'Steam Temp': (Unit6.temperature +10), 'loses': 0.10}

def Benzene_distillation_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    feed_in = feed_flow.attributes['mass_flow_rate']
    cumume_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Cumene')])
    benzene_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Benzene')])
    waste_out = feed_in - cumume_in - benzene_in
    Q_steam = (material_in * coeff['Steam Demand (kJ/kg)'])/ (1-coeff['loses'])
    m_steam = Q_steam / Hvap
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_in + Q_steam - Q_loss 
    print('Unit 6')
    return[{'name' : 'Bottoms', 'components' : ['Waste'], 'composition' : [1], 'mass_flow_rate' : waste_out,
             'flow_type': 'Waste', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Unreacted Benzene', 'components' : ['Benzene'], 'composition' : [1], 'mass_flow_rate' : benzene_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Cumene', 'components' : ['Cumene'], 'composition' : [1], 'mass_flow_rate' : cumume_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Steam (Benzene Distillation)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Benzene Distillation)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}]
Unit6.calculations = {'Liquid Flow': Benzene_distillation_func}

# Unit 7: Cooler 2 - Need the CP here too
Unit7 = Unit('Cooler 2')
Unit7.temperature = 120 
Unit7.unit_type = 'Thermal Unit'
Unit7.expected_flows_in = ['Cumene', 'Coolant (Cooler 2)']
Unit7.expected_flows_out = ['Process Flow 5']
Unit7.coefficients = {'Unit Temp': Unit7.temperature}

def Cooler_two_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    C_Pflow = 2.0 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_out = feed_in * C_Pflow * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 7')
    return[{'name' : 'Process Flow 5', 'components' : ['Cumene'], 'composition' : [1], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Coolant (Cooler 2)', 'components' : ['Chilling'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit7.calculations = {'Cumene': Cooler_two_func}

# Unit 8: Oxidizer 
Unit8 = Unit('Oxidizer')
Unit8.temperature = Unit7.temperature
Unit8.unit_type = 'Reactor'
Unit8.expected_flows_in = ['Air (Oxidizer)', 'Process Flow 5']
Unit8.expected_flows_out = ['Offgas (Oxdizer)', 'Process Flow 6']
Unit8.coefficients = {'Air Ratio': (2145/5.2), 'Conversion': 0.15}

def Oxiderizer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    chp_out = feed_in * coeff['Conversion']
    gram_o2_reacted = (chp_out / 152.19) * 32.00 
    feed_out = gram_o2_reacted + feed_in 
    chp_wt = chp_out / feed_out
    air_in = coeff['Air Ratio'] * feed_in 
    air_out = air_in - gram_o2_reacted
    print('Unit 8')
    return[{'name' : 'Air (Oxidizer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_in,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Offgas (Oxidizer)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : air_out,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Process Flow 6', 'components' : ['Cumene', 'CHP'], 'composition' : [1-chp_wt, chp_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}]
Unit8.calculations = {'Process Flow 5': Oxiderizer_func}

# Unit 9: Cooler 3 - Need CP 
Unit9 = Unit('Cooler 3')
Unit9.temperature = 70 
Unit9.unit_type = 'Thermal Unit'
Unit9.expected_flows_in = ['Process Flow 6', 'Coolant (Cooler 3)']
Unit9.expected_flows_out = ['Process Flow 7']
Unit9.coefficients = {'Unit Temp': Unit9.temperature}

def Cooler_three_func(feed_flow, coeff): 
    Q_in = feed_flow.attributes['heat_flow_rate']
    C_Pflow = 2.0 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_out = feed_in * C_Pflow * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 9')
    return[{'name' : 'Process Flow 7', 'components' : ['Cumene', 'CHP'], 'composition' : feed_flow.attributes['composition'], 'mass_flow_rate' : feed_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_out}, 
            {'name' : 'Coolant (Cooler 3)', 'components' : ['Chilling'], 'composition' : [1], 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_chilling}]
Unit9.calculations = {'Process Flow 6': Cooler_three_func}

# Unit 10: Cleavage
Unit10 = Unit('Cleavage') 
Unit10.temperature = 70 
Unit10.unit_type = 'Reactor'
Unit10.expected_flows_in = ['Sulfuric Acid', 'Process Flow 7']
Unit10.expected_flows_out = ['Process Flow 8']
Unit10.coefficients = {'Molar Ratio H2SO4': 1.00}

def Cleavage_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    chp_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('CHP')])
    h2so4_in = (chp_in / 152.9) * 98.08 * coeff['Molar Ratio H2SO4']
    feed_out = h2so4_in + feed_in 
    moles_phenol = (chp_in / 152.9)
    moles_acetone = moles_phenol
    phenol_out = 94.11 * moles_phenol
    acetone_out = 58.08 * moles_acetone
    acetone_wt = acetone_out / feed_out 
    phenol_wt = phenol_out / feed_out
    cumene_wt = 1 - acetone_wt - phenol_wt
    print('Unit 10')
    return[{'name' : 'Process Flow 8', 'components' : ['Cumene', 'Phenol', 'Acetone'], 'composition' : [cumene_wt, phenol_wt, acetone_wt], 'mass_flow_rate' : feed_out,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : True, 'heat_flow_rate': Q_in}, 
            {'name' : 'Sulfuric Acid', 'components' : ['H2SO4'], 'composition' : [1], 'mass_flow_rate' : h2so4_in,
             'flow_type': 'Process Stream', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit10.calculations = {'Process Flow 7': Cleavage_func}

# Unit 11: Acetone Distillation
Unit11 = Unit('Product Distillation')
Unit11.temperature = 65 
Unit11.unit_type = 'Seperator'
Unit11.expected_flows_in = ['Process Flow 8', 'Steam (Product Column)']
Unit11.expected_flows_out = ['Product Phenol', 'Product Cumene', 'Product Acetone', 'Condensate (Product Column)']
Unit11.coefficients = {'Acetone Steam Demand (kJ/kg)': (15.26), 'Phenol Steam Demand (kJ/kg)': (48.9), 'Steam Temp': 100, 'Unit Temp': Unit11.temperature, 'loses':0.10}

def Product_distillation_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    cumene_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Cumene')])
    phenol_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Phenol')])
    acetone_in = feed_in - cumene_in - phenol_in
    Q_steam_phenol = coeff['Phenol Steam Demand (kJ/kg)'] * phenol_in
    Q_steam_acetone = coeff['Acetone Steam Demand (kJ/kg)'] * acetone_in
    Q_steam = (Q_steam_acetone + Q_steam_phenol) / (1-coeff['loses'])
    m_steam = Q_steam / Hvap 
    Q_loss = Q_steam * coeff['loses']
    Q_out = Q_steam + Q_in - Q_loss
    print('Unit 11')
    return[{'name' : 'Steam (Product Column)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Product Column)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss}, 
           {'name' : 'Product Phenol', 'components' : ['Phenol'], 'composition' : [1], 'mass_flow_rate' : phenol_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_out}, 
            {'name' : 'Product Cumene', 'components' : ['Cumene'], 'composition' : [1], 'mass_flow_rate' : cumene_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Product Acetone', 'components' : ['Acetone'], 'composition' : [1], 'mass_flow_rate' : acetone_in,
             'flow_type': 'Product', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit11.calculations = {'Process Flow 8':Product_distillation_func }

##################################################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, Unit10, 
                Unit11]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_Crude_cyclic', allflows, processunits)