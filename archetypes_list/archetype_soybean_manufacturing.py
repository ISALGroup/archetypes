'''
Name: Aidan J ONeil
Date: 723/2025 12:00:00
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
amb_t = ambient_t
soybean_amount = 1000
C_psolids = 0.81
C_pw = 4.186
Hvap = 2257
C_phexane = 1.23
Hvap_hexane = 441.9
C_poil = 2.00
C_pair = 1.000

            
#Unit 1 :Cleaner definition                  
Unit1 = Unit('Cleaner')
Unit1.expected_flows_in = ['Soybeans', 'Water (Cleaner)']
Unit1.expected_flows_out = ['Wastewater (Cleaner)', 'Cleaned soybeans']
Unit1.coefficients = {'Cleaner water ratio' : 1.67}

def Cleaner_func(soybeans_flow, coeff):
    soybeans_in = soybeans_flow.attributes['mass_flow_rate']
    water_in = soybeans_in * coeff['Cleaner water ratio']
    print('Unit 1')
    
    return [{'name' : 'Water (Cleaner)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : water_in,
                     'flow_type': 'Water', 'temperature' : ambient_t, 'pressure' : 1 , 'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Wastewater (Cleaner)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : water_in,
                     'flow_type': 'Water', 'temperature' : ambient_t, 'pressure' : 1 , 'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Cleaned soybeans', 'components' : soybeans_flow.attributes['components'], 'composition' : soybeans_flow.attributes['composition'], 'mass_flow_rate' : soybeans_in,
                     'flow_type': 'Process flow', 'temperature' : ambient_t, 'pressure':1 , 'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False}
            ]

Unit1.calculations = {'Soybeans' : Cleaner_func}

FlowA = Flow('Soybeans',['Water', 'Dry bean'],'input', ambient_t, 1, [0.13, 0.87], None , None, soybean_amount, np.nan, 0)
FlowA.set_calc_flow()
allflows.append(FlowA)

#Unit 2 : Dryer definition  
Unit2= Unit('Dryer')
Unit2.expected_flows_in = ['Cleaned soybeans', 'Electricity (Dryer, soybeans)', 'Air (Dryer, soybeans)', 'Steam (Dryer, soybeans)']
Unit2.expected_flows_out = ['Dried soybeans', 'Exhaust gas (Dryer, soybeans)', 'Condensate (Dryer, soybeans)']

Unit2.coefficients = {'Water evap rate' : (.227/2.722) , 'Air temperature' : ambient_t, 'Unit Temp' : 37.8,
                      'Exhaust gas temperature' : 60, 'Air Ratio': 2, 'Electricity (kW/kg)' : 0.021, 'Loss' : 0.1,
                      'Steam Temp':100}

def Dryerfunc_soybean(soybean_flow, coeff):
    soybeans_in = soybean_flow.attributes['mass_flow_rate']
    water_evap = soybeans_in * coeff['Water evap rate']
    soybeans_out = soybeans_in - water_evap
    air_in = soybeans_in * coeff['Air Ratio'] 
    electricity_amount = soybeans_in * coeff['Electricity (kW/kg)']
    Q_in = soybean_flow.attributes['heat_flow_rate']
    Q_water_evap = water_evap * Hvap
    Q_out = soybeans_in * C_psolids  * (coeff['Unit Temp'] - ambient_t)
    Q_exhaust = (soybeans_in * coeff['Air Ratio']) * C_pair * (coeff['Exhaust gas temperature'] - ambient_t)
    Q_steam = (Q_out + Q_water_evap + Q_exhaust - Q_in)/ (1 - coeff['Loss'])
    Q_loss = Q_steam * coeff['Loss'] 
    m_steam = Q_steam / Hvap
    exhaust_amount = water_evap + air_in
    exhaust_gas_water_ratio = water_evap / (water_evap + air_in)
    steam_t = coeff['Steam Temp']
    print('Unit2')
    return [{'name' : 'Electricity (Dryer, soybeans)',
             'flow_type': 'Electricity',  'In or out' : 'In', 'elec_flow_rate' : electricity_amount ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Air (Dryer, soybeans)', 'components' : ['Air'], 'composition': [1], 'mass_flow_rate' : air_in,
                     'flow_type': 'Air', 'temperature' : ambient_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Condensate (Dryer, soybeans)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Condensate', 'temperature' : steam_t, 'pressure':2.7 , 'heat_flow_rate' :0 ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Dryer, soybeans)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Steam', 'temperature' : steam_t, 'pressure':2.7 , 'heat_flow_rate' :Q_steam ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Exhaust gas (Dryer, soybeans)', 'components' : ['Water', 'Air'], 'composition': [exhaust_gas_water_ratio, 1 - exhaust_gas_water_ratio], 'mass_flow_rate' : exhaust_amount,
                     'flow_type': 'Exhaust', 'temperature' : coeff['Exhaust gas temperature'], 'pressure':1 , 'heat_flow_rate' :Q_water_evap + Q_exhaust ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Dried soybeans', 'components' : ['Dry bean', 'Water'], 'composition': [.90,.10], 'mass_flow_rate' : soybeans_out,
                     'flow_type': 'Process', 'temperature' : coeff['Unit Temp'], 'pressure':1 , 'heat_flow_rate' :Q_out ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'Heat loss'  : Q_loss}]

Unit2.calculations = {'Cleaned soybeans' : Dryerfunc_soybean}

#Unit 3 : Don't need storage units

#Unit 4 : Cracking mill definition  
Unit4 = Unit('Cracking mill')
Unit4.expected_flows_in = ['Dried soybeans', 'Electricity (Cracking)']
Unit4.expected_flows_out = ['Cracked soybeans']
Unit4.coefficients = {'Electricity per ton of beans' : 4.7}

def Cracking_mill_func(soybean_flow, coeff):
    soybeans_in = soybean_flow.attributes['mass_flow_rate']
    electricity_in = soybeans_in * coeff['Electricity per ton of beans']
    print('Unit 4')
    return[{'name' : 'Cracked soybeans', 'components' : soybean_flow.attributes['components'], 'composition':  soybean_flow.attributes['composition'], 'mass_flow_rate' : soybeans_in,
                     'flow_type': 'Process', 'pressure':1 , 'heat_flow_rate' :soybean_flow.attributes['heat_flow_rate'] ,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Electricity (Cracking)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit4.calculations = {'Dried soybeans': Cracking_mill_func}

#Unit 5 : Dehuller definition  
Unit5 = Unit('Dehuller')
Unit5.expected_flows_in = ['Cracked soybeans', 'Electricity (Dehuller)']
Unit5.expected_flows_out = ['Hulls', 'Dehulled beans']
Unit5.coefficients = {'Hull Ratio': 0.018, 'Electricity (kw/kg)': 0.0000}

def Dehuller_func(beans_flow, coeff):
    beans_in = beans_flow.attributes['mass_flow_rate']
    hull_out = beans_in * coeff['Hull Ratio']
    beans_out = beans_in - hull_out
    electricity_in = beans_in * coeff['Electricity (kw/kg)']
    print('Unit 5')
    return[{'name' : 'Dehulled beans', 'components' : beans_flow.attributes['components'], 'composition':  beans_flow.attributes['composition'], 'mass_flow_rate' : beans_out,
            'flow_type': 'Process', 'heat_flow_rate' :beans_flow.attributes['heat_flow_rate'] ,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Hulls', 'components' : beans_flow.attributes['components'], 'composition':  beans_flow.attributes['composition'], 'mass_flow_rate' : hull_out,
            'flow_type': 'Waste', 'heat_flow_rate' :0 ,'In or out' : 'Out', 'Set calc' : False},
           {'name' : 'Electricity (Dehuller)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]

Unit5.calculations = {'Cracked soybeans': Dehuller_func}

#Unit 6 : Conditioner definition  
Unit6 = Unit('Conditioner')
Unit6.expected_flows_in = ['Dehulled beans', 'Electricity (Conditioner)', 'Steam (Conditioner)']
Unit6.expected_flows_out = ['Conditioned beans', 'Condensate (Conditioner)']

Unit6.coefficients = {'Unit Temp': 60., 'Steam Temp': 100, 'loses': 0.30, 'Electricity (kw/kg)': 0.000}

def Conditioner_func(bean_flow, coeff):
    beans_in = bean_flow.attributes['mass_flow_rate']
    Q_in = bean_flow.attributes['heat_flow_rate']
    water_in = (bean_flow.attributes['composition'][bean_flow.attributes['components'].index('Water')]) * beans_in
    solids_in = beans_in - water_in
    Q_out = (solids_in * C_psolids * (coeff['Unit Temp'] - ambient_t)) + (water_in *C_pw * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    m_steam = Q_steam / Hvap
    electricity_in = beans_in * coeff['Electricity (kw/kg)']
    Q_loss = Q_steam * coeff['loses']
    print('Unit6') 
    return[{'name' : 'Electricity (Conditioner)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Conditioner)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Conditioner)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Conditioned beans', 'components' : ['Water', 'Solids'], 'composition':  [.87, .13], 'mass_flow_rate' : beans_in,
            'flow_type': 'Process', 'heat_flow_rate' : Q_out ,'In or out' : 'Out', 'Set calc' : True}]

Unit6.calculations = {'Dehulled beans': Conditioner_func}

#Unit 7 : Flaking mill definition  
Unit7 = Unit('Flaking mill')
Unit7.expected_flows_in = ['Conditioned beans', 'Electricity (Flaking mill)']
Unit7.expected_flows_out = ['Flaked beans']
Unit7.coefficients = {'Electricity (kw/kg)': 0.000 }

def Flaking_mill_func(bean_flow, coeff):
    beans_in = bean_flow.attributes['mass_flow_rate']
    electricity_in = beans_in * coeff['Electricity (kw/kg)']
    print('Unit 7')
    return[{'name' : 'Electricity (Flaking mill)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Flaked beans', 'components' : ['Water', 'Solids'], 'composition':  [.87, .13], 'mass_flow_rate' : beans_in,
            'flow_type': 'Process', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : True},
           {'Heat loss': bean_flow.attributes['heat_flow_rate']}]
Unit7.calculations = {'Conditioned beans': Flaking_mill_func}

#Unit 8 : Oil extractor definition  
Unit8 = Unit('Oil extractor')
Unit8.expected_flows_in = ['Flaked beans', 'Hexane', 'Electricity (Oil extractor)']
Unit8.expected_flows_out = ['Soybean flakes', 'Oil']
Unit8.coefficients = {'Hexane Ratio': 1.04, 'Oil Out Ratio': .185, 'Electricity (kw/kg)': 0.000}

def Oil_extractor_func(bean_flow, coeff):
    beans_in = bean_flow.attributes['mass_flow_rate']
    hexane_in = beans_in * coeff['Hexane Ratio']
    oil_out = beans_in * coeff['Oil Out Ratio']
    flakes_out = beans_in + hexane_in - oil_out
    hexane_wt = hexane_in / flakes_out
    flakes_wt = 1 - hexane_wt
    electricity_in = coeff['Electricity (kw/kg)'] * beans_in
    print('Unit 8') 
    return[{'name' : 'Electricity (Oil extractor)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Oil', 'components' : ['Oil'], 'composition':  [1], 'mass_flow_rate' : oil_out,
            'flow_type': 'Process', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Hexane', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_in,
            'flow_type': 'Process', 'heat_flow_rate' : .1 ,'In or out' : 'In', 'Set calc' : False, 'Set shear': True},
           {'name' : 'Soybean flakes', 'components' : ['Flakes'], 'composition':  [1], 'mass_flow_rate' : flakes_out,
            'flow_type': 'Process', 'heat_flow_rate' : -.1 ,'In or out' : 'Out', 'Set calc' : True}]


Unit8.calculations = {'Flaked beans': Oil_extractor_func}

#Unit 9 : Desolventizer definition  
Unit9 = Unit('Desolventizer')
Unit9.expected_flows_in = ['Soybean flakes', 'Electricity (Desolventizer)', 'Steam (Desolventizer)']
Unit9.expected_flows_out = ['Desolventized flakes', 'Hexane vapor', 'Condensate (Desolventizer)']

Unit9.coefficients = {'Hexane inlet wt%':(.52/1.996), 'Outlet Flakes Temp':93.3, 'Outlet Temp Hexane': 68.9,
                      'Electricity (kw/kg)': 0.000, 'loses':0.30, 'Steam Temp': 100.}

def Desolventizer_func(flakes_flow, coeff):
    flakes_in = flakes_flow.attributes['mass_flow_rate']
    hexane_in = flakes_in * coeff['Hexane inlet wt%']
    flakes_out = flakes_in - hexane_in
    Q_in = flakes_flow.attributes['heat_flow_rate'] 
    solids_in = flakes_in - hexane_in
    Q_hexane = hexane_in * (((C_phexane * (coeff['Outlet Temp Hexane'] - ambient_t)) + Hvap_hexane))
    Q_flakes = solids_in * C_psolids * (coeff['Outlet Flakes Temp'] - ambient_t)
    Q_steam = (Q_flakes + Q_hexane - Q_in) / (1- coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    electricity_in = flakes_in * coeff['Electricity (kw/kg)']
    print('Unit 9')
    return[{'name' : 'Electricity (Desolventizer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Desolventizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Desolventizer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Hexane vapor', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_in,
            'flow_type': 'Process', 'heat_flow_rate' : Q_hexane ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False},
           {'name' : 'Desolventized flakes', 'components' : ['Flakes'], 'composition':  [1], 'mass_flow_rate' : flakes_out,
            'flow_type': 'Process', 'heat_flow_rate' : Q_flakes ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}]

Unit9.calculations = {'Soybean flakes': Desolventizer_func}

#Unit 10 : Meal dryer definition - check the efficiency of this unit because it might be MEE  
Unit10 = Unit('Meal dryer')
Unit10.expected_flows_in = ['Desolventized flakes', 'Electricity (Meal dryer)', 'Steam (Meal dryer)']
Unit10.expected_flows_out = ['Dried meal', 'Condensate (Meal dryer)']
Unit10.coefficients = {'Water wt%': (.310/2.310), 'loses': .855, 'Electricity (kw/kg)': 0.000, 'Steam Temp': 100.}

def Meal_dryer_func(flakes_flow, coeff):
    flakes_in = flakes_flow.attributes['mass_flow_rate']
    Q_in = flakes_flow.attributes['heat_flow_rate']
    water_evap = flakes_in * coeff['Water wt%']
    flakes_out = flakes_in - water_evap
    Q_steam = (water_evap * Hvap) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    electricity_in = coeff['Electricity (kw/kg)'] * flakes_in
    m_steam = Q_steam / Hvap
    print('Unit10') 
    return[{'name' : 'Electricity (Meal dryer)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Steam (Meal dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Meal dryer)', 'components' : 'Water', 'mass_flow_rate' : m_steam + water_evap,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Dried meal', 'components' : ['Meal'], 'composition':  [1], 'mass_flow_rate' : flakes_out,
            'flow_type': 'Process','Temperature':93.0, 'heat_flow_rate' : Q_in ,'In or out' : 'Out', 'Set calc' : True}]

Unit10.calculations = {'Desolventized flakes': Meal_dryer_func}

#Unit 11 : Meal cooler definition  
Unit11 = Unit('Meal cooler')
Unit11.expected_flows_in = ['Dried meal','Chilling (Meal cooler)', 'Electricity (Meal cooler)']
Unit11.expected_flows_out = ['Cooled meal']
Unit11.coefficients = {'Unit Temp': ambient_t, 'C_psolids': 1.47, 'Electricity (kw/kg)': 0.000}

def Meal_cooler_func(meal_flow, coeff):
    meal_in = meal_flow.attributes['mass_flow_rate']
    Q_in = meal_flow.attributes['heat_flow_rate']
    electricity_in = meal_in * coeff['Electricity (kw/kg)']
    Q_out = meal_in * coeff['C_psolids'] * (coeff['Unit Temp'] - ambient_t)
    Q_cw = (Q_out - Q_in)
    print('Unit 11')
    return[{'name' : 'Electricity (Meal cooler)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Cooled meal', 'components' : ['Meal'], 'composition':  [1], 'mass_flow_rate' : meal_in,
            'flow_type': 'Process','Temperature':coeff['Unit Temp'], 'heat_flow_rate' : Q_out ,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Chilling (Meal cooler)', 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cw}]

Unit11.calculations = {'Dried meal': Meal_cooler_func}

#Unit 12 : Preheater/condenser definition  
Unit12 = Unit('Preheater/condenser')
Unit12.required_calc_flows = 2
Unit12.expected_flows_in = ['Hexane vapor', 'Oil', 'Chilling (Condenser)']
Unit12.expected_flows_out = ['Hexane to storage', 'Oil to Flash']

Unit12.coefficients = {}

def Condenser_func(ablist, coeff):
    hexane_flow = ablist[0]
    oil_flow = ablist[1]
    hexane_to_storage = (hexane_flow.attributes['mass_flow_rate'])
    oil_to_flash = oil_flow.attributes['mass_flow_rate']
    Q_in = (oil_flow.attributes['heat_flow_rate']) + (hexane_flow.attributes['heat_flow_rate'])
    Q_out_hexane = 0
    Q_oil = 0
    Q_cw = Q_out_hexane + Q_oil - Q_in
    print('Unit 12')
    return[{'name' : 'Hexane to storage', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_to_storage,
            'flow_type': 'Process', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False},
           {'name' : 'Oil to Flash', 'components' : ['Oil'], 'composition':  [1], 'mass_flow_rate' : oil_to_flash,
            'flow_type': 'Process', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False},
           {'name' : 'Chilling (Condenser)', 'mass_flow_rate' : 0,
             'flow_type': 'Chilling', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_cw}]

Unit12.calculations = (['Hexane vapor', 'Oil'], Condenser_func)

#Unit 13 : Hexane storage definition  
Unit13 = Unit('Hexane storage')
Unit13.required_calc_flows = 2
Unit13.expected_flows_in = ['Condensed Hexane', 'Hexane to storage']
Unit13.expected_flows_out = ['Hexane', 'Waste Hexane']
Unit13.coefficients = {'Hexane to Beans Ratio': (2.540/2.722)}

def Hexane_storage_func(ablist, coeff):
    hexane_flow_one = ablist[0]
    hexane_flow_two = ablist[1]
    hexane_in = (hexane_flow_one.attributes['mass_flow_rate']) + (hexane_flow_two.attributes['mass_flow_rate'])
    hexane_to_reactor = soybean_amount * coeff['Hexane to Beans Ratio']
    waste_hexane = hexane_in - hexane_to_reactor
    Q_loss = .1
    print('Unit13')
    return[{'name' : 'Hexane', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_to_reactor,
            'flow_type': 'Process', 'heat_flow_rate' : Q_loss ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': True},
           {'name' : 'Waste Hexane', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : waste_hexane,
            'flow_type': 'Waste', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False},
           {'Heat loss': -Q_loss}]

Unit13.calculations = (['Condensed Hexane', 'Hexane to storage'], Hexane_storage_func)

#Unit 16 : Flash chamber definition  
Unit16 = Unit('Flash chamber')
Unit16.expected_flows_in = ['Oil to Flash']
Unit16.expected_flows_out = ['Oil to Evaporator']
Unit16.coefficients = {}

def Flash_chamber_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    Q_oil = oil_flow.attributes['heat_flow_rate']
    print('Unit 16')
    return[{'name' : 'Oil to Evaporator', 'components' : ['Oil'], 'composition':  [1], 'mass_flow_rate' : oil_in,
            'flow_type': 'Process', 'heat_flow_rate' : 0 ,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}]

Unit16.calculations = {'Oil to Flash': Flash_chamber_func}

#Unit 18 : Evaporator definition  
Unit18 = Unit('Evaporator')
Unit18.expected_flows_in = ['Oil to Evaporator', 'Steam (Evaporator)']
Unit18.expected_flows_out = ['Oil/Hexane Mix', 'Condensate (Evaporator)']
Unit18.coefficients = {'Vaporization Rate': (.15/.364), 'Unit Temp': 51.7, 'Steam Temp': 100, 'loses': .70, 'Hexane wt%': .00350}

def Evaporator_func(oil_flow, coeff):
    oil_in = oil_flow.attributes['mass_flow_rate']
    hexane_in = oil_in * coeff['Hexane wt%']
    pure_oil_in = oil_in - hexane_in
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_oil_out = pure_oil_in * C_poil * (coeff['Unit Temp'] - ambient_t)
    Q_hexane = (hexane_in * C_phexane * (coeff['Unit Temp'] - ambient_t)) + (hexane_in * coeff['Vaporization Rate'] * Hvap_hexane)
    Q_out = Q_hexane + Q_oil_out
    Q_steam = (Q_out - Q_in) / (1 - coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 18')
    return[{'name' : 'Steam (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Evaporator)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Oil/Hexane Mix', 'components' : ['Oil', 'Hexane'], 'composition':  [1-coeff['Hexane wt%'], coeff['Hexane wt%']], 'mass_flow_rate' : oil_in,
            'flow_type': 'Process','Temperature':coeff['Unit Temp'], 'heat_flow_rate' : Q_out ,'In or out' : 'Out', 'Set calc' : True}]

Unit18.calculations = {'Oil to Evaporator': Evaporator_func}

#Unit 19 : Vacuum stripper definition - there has to be some reason why this is split from unit 18
# for now I assume that the oil doesn't get any heat...
Unit19 = Unit('Vacuum stripper')
Unit19.expected_flows_in = ['Oil/Hexane Mix', 'Steam (Vacuum stripper)']
Unit19.expected_flows_out = ['Condensate (Vacuum stripper)', 'Stripped Hexane', 'Soybean Oil']
Unit19.coefficients = {'Unit Temp': 65.6, 'Steam Temp': 100, 'loses':.10}

def Vacuum_stripper_func(oil_flow, coeff):
    oil_in = (oil_flow.attributes['mass_flow_rate']) * (oil_flow.attributes['composition'][oil_flow.attributes['components'].index('Oil')])
    hexane_in = (oil_flow.attributes['mass_flow_rate']) * (oil_flow.attributes['composition'][oil_flow.attributes['components'].index('Hexane')]) 
    Q_in = oil_flow.attributes['heat_flow_rate']
    Q_hexane_out = (hexane_in * Hvap_hexane) + (hexane_in * C_phexane * (coeff['Unit Temp'] - ambient_t))
    Q_steam = (Q_hexane_out) / (1-coeff['loses'])
    Q_loss = Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap
    print('Unit 19')
    return[{'name' : 'Steam (Vacuum stripper)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Vacuum stripper)', 'components' : 'Water', 'mass_flow_rate' : m_steam ,
             'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0},
           {'Heat loss': Q_loss},
           {'name' : 'Stripped Hexane', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_in,
            'flow_type': 'Process','Temperature':coeff['Unit Temp'], 'heat_flow_rate' : Q_hexane_out ,'In or out' : 'Out', 'Set calc' : True},
           {'name' : 'Soybean Oil', 'components' : ['Oil'], 'composition':  [1], 'mass_flow_rate' : oil_in,
            'flow_type': 'Product','Temperature':coeff['Unit Temp'], 'heat_flow_rate' : Q_in ,'In or out' : 'Out', 'Set calc' : False}]

Unit19.calculations = {'Oil/Hexane Mix': Vacuum_stripper_func}

#Unit 20 : Hexane steam condenser definition  
Unit20 = Unit('Hexane steam condenser')
Unit20.expected_flows_in = ['Stripped Hexane']
Unit20.expected_flows_out = ['Condensed Hexane', 'Waste heat (hexane condensation)']
Unit20.coefficients = {}

def Hexane_condenser_func(hexane_flow, coeff):
    Q_in = hexane_flow.attributes['heat_flow_rate']
    Q_out = 0
    Q_avail = Q_in - Q_out
    hexane_in = hexane_flow.attributes['mass_flow_rate']
    print('Unit 20')
    return[{'name' : 'Condensed Hexane', 'components' : ['Hexane'], 'composition':  [1], 'mass_flow_rate' : hexane_in,
            'flow_type': 'Process','Temperature':ambient_t, 'heat_flow_rate' : Q_out ,'In or out' : 'Out', 'Set calc' : True},
           {'name' :'Waste heat (hexane condensation)', 
             'flow_type': 'Waste heat', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_avail}]

Unit20.calculations = {'Stripped Hexane': Hexane_condenser_func}

###################################################################################################################################################
processunits = [Unit1, Unit2, Unit4, Unit5, Unit6, Unit7, Unit8,
                Unit9, Unit10, Unit11, Unit12, Unit13, Unit16, Unit18,
                Unit19, Unit20]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

#for flow in allflows:
 #   if flow.attributes['flow_type'] == 'Product':
  #      print(flow)

for flow in allflows:
    print(flow)

#utilities_recap('heat_intensity_soybean_4', allflows, processunits)









