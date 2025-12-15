'''
Name: Aidan J ONeil 
Date: 9/16/2025 

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
recycled_paper_in = 1000
C_pw = 4.186
Hvap = 2257
market_pulp_in = 1000
stock_split = 0.5
C_pair = 1


######################################################################### UNITS ######################################################################################################################
#Unit 11: Recycled pulper
Unit1= Unit('Pulper')
Unit1.temperature = 40
Unit1.unit_type = ''
Unit1.expected_flows_in = ['Recycled paper', 'Electricity (Pulper, recycled)', 'Water (Pulper, recycled)', 'Steam (Pulper, recycled)']
Unit1.expected_flows_out = ['Pulped recycled', 'Condensate (Pulper, recycled)']
Unit1.coefficients = {'Consistency' : 0.15, 'Pulping temperature' : Unit1.temperature, 'Electricity per t paper' : 25}

def Pulprec_paper(waste_paper, coeff):
    waste_paper_amount = waste_paper.attributes['mass_flow_rate']
    dry_paper = waste_paper_amount*waste_paper.attributes['composition'][waste_paper.attributes['components'].index('Paper')]
    water_in_paper_in = waste_paper_amount - dry_paper
    dry_paper_cp = 1.4
    water_cp = 4.2
    total_pulp = dry_paper / coeff['Consistency']
    total_water = total_pulp - dry_paper
    water_in = total_water - water_in_paper_in
    Q_water = water_cp * total_water * (coeff['Pulping temperature'] - amb_t)
    Q_paper = dry_paper_cp * dry_paper * (coeff['Pulping temperature'] - amb_t)
    Q_total = Q_water + Q_paper
    elec_in = dry_paper * coeff['Electricity per t paper']/1000.
    vap_heat = 2256.4
    m_steam = Q_total/vap_heat
    steam_t = 100.
    Q_sensible_steam = water_cp * (steam_t - amb_t)
    Q_steam_total = Q_total
    print('Unit 1')
    return [{'name' : 'Electricity (Pulper, recycled)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_in ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Water (Pulper, recycled)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : water_in,
            'flow_type': 'Water', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Pulper, recycled)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
            'flow_type': 'Steam', 'temperature' : steam_t, 'pressure':1 , 'heat_flow_rate' :Q_steam_total ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Condensate (Pulper, recycled)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
            'flow_type': 'Condensate', 'temperature' : steam_t, 'pressure': 1 , 'heat_flow_rate' :Q_sensible_steam ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Pulped recycled', 'components' : ['Dry pulp', 'Water'], 'composition': [coeff['Consistency'], 1 - coeff['Consistency']], 'mass_flow_rate' : total_pulp,
            'flow_type': 'Process', 'temperature' : coeff['Pulping temperature'], 'pressure':1 , 'heat_flow_rate' :Q_total,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False}]
Unit1.calculations = {'Recycled paper' : Pulprec_paper}

FlowA = Flow(name='Recycled paper', components = ['Paper'], composition = [1], flow_type = 'input', mass_flow_rate = recycled_paper_in, heat_flow_rate=0)
FlowA.set_calc_flow()
allflows.append(FlowA)

#Unit 2: Screening
Unit2 = Unit('Screening')
Unit2.temperature = ambient_t
Unit2.unit_type = 'Seperator'
Unit2.expected_flows_in = ['Pulped recycled', 'Electricity (Screening, recycled)']
Unit2.expected_flows_out = ['Screened recycled pulp', 'Rejects (recycling)']
Unit2.coefficients = {'Rejects amount' : 0.02, 'Electricity per ton' : 23}

def Screenrec_pulp(waste_pulp, coeff):
    waste_pulp_amount = waste_pulp.attributes['mass_flow_rate']
    dry_pulp = waste_pulp_amount*waste_pulp.attributes['composition'][waste_pulp.attributes['components'].index('Dry pulp')]
    t_in = waste_pulp.attributes['temperature']
    Q_in = waste_pulp.attributes['heat_flow_rate']
    rejects_amount = coeff['Rejects amount'] * waste_pulp_amount
    pulp_out = waste_pulp_amount - rejects_amount
    Q_rejects = Q_in * coeff['Rejects amount']
    Q_out = Q_in - Q_rejects
    elec_amount = dry_pulp * coeff['Electricity per ton']
    moisture = 1 - waste_pulp.attributes['composition'][waste_pulp.attributes['components'].index('Dry pulp')]
    print('Unit 2')
    return [{'name' : 'Electricity (Screening, recycled)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_amount ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Rejects (recycling)', 'components' : ['Water', 'Dry pulp'], 'composition' : [moisture, 1 - moisture] ,'mass_flow_rate' : rejects_amount,
            'flow_type': 'Waste', 'temperature' : t_in, 'heat_flow_rate' : Q_rejects ,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Screened recycled pulp', 'components' : ['Water', 'Dry pulp'], 'composition' : [moisture, 1 - moisture], 'mass_flow_rate' : pulp_out, 'heat_flow_rate' : Q_out ,
            'flow_type': 'Process', 'temperature' : t_in,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False}]
Unit2.calculations = {'Pulped recycled' : Screenrec_pulp}

#Unit 3: De inking
Unit3 = Unit('Deinking')
Unit3.temperature = 45
Unit3.unit_type = ''
Unit3.expected_flows_in = ['Screened recycled pulp', 'Electricity (deinking)', 'Steam (deinking)', 'Water (deinking)', 'Additives (deinking)']
Unit3.expected_flows_out = ['Deinked pulp', 'Condensate (deinking)']
Unit3.coefficients = {'Additives quantity' : 0.05, 'Electricity per t' : 10, 'Deinking temperature' : Unit3.temperature, 'Consistency' : 0.015}

def Deinking_pulp(screened_pulp, coeff):
    pulp_amount = screened_pulp.attributes['mass_flow_rate']
    moist_in = screened_pulp.attributes['composition'][screened_pulp.attributes['components'].index('Water')]
    dry_part = screened_pulp.attributes['composition'][screened_pulp.attributes['components'].index('Dry pulp')]
    Q_in = screened_pulp.attributes['heat_flow_rate']
    dry_pulp = dry_part * pulp_amount
    moisture = moist_in * pulp_amount
    additives_cp = 2.5
    dry_paper_cp = 1.4
    water_cp = 4.2
    dry_pulp = pulp_amount * dry_part
    Q_in = screened_pulp.attributes['heat_flow_rate']
    additives_amount = dry_pulp * coeff['Additives quantity']
    deinked_drypart = additives_amount + dry_pulp
    total_deinked_amount = deinked_drypart/coeff['Consistency']
    water_out = total_deinked_amount - deinked_drypart
    elec_in = total_deinked_amount * coeff['Electricity per t'] / 1000.
    Q_out_total = ((additives_amount*additives_cp) + (dry_pulp* dry_paper_cp) + (water_out* water_cp)) * (coeff['Deinking temperature'] - amb_t)
    Q_heat_added = Q_out_total - Q_in
    water_in = water_out - moisture
    m_steam = Q_heat_added/Hvap
    a_q = additives_amount/total_deinked_amount
    w_q = (1- coeff['Consistency'])
    p_q = dry_pulp / total_deinked_amount
    sensible_heat = m_steam * water_cp *(100 - amb_t)
    Q_steam = Q_heat_added + sensible_heat
    print('Unit 3')
    return [{'name' : 'Electricity (deinking)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_in ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Steam (deinking)', 'components' : ['Water'], 'composition' : [1] ,'mass_flow_rate' : m_steam,
                     'flow_type': 'Steam', 'temperature' : 100, 'heat_flow_rate' : Q_steam ,  'In or out' : 'In', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Water (deinking)', 'components' : ['Water'], 'composition' : [1], 'mass_flow_rate' : water_in, 'heat_flow_rate' : 0 ,
                     'flow_type': 'Water', 'temperature' : amb_t,  'In or out' : 'In', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Additives (deinking)', 'components' : ['Additives'], 'composition' : [1] ,'mass_flow_rate' : additives_amount,
                     'flow_type': 'Process', 'temperature' : amb_t, 'heat_flow_rate' : 0,  'In or out' : 'In', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Deinked pulp', 'components' : ['Water', 'Dry pulp', 'Additives'], 'composition' : [w_q, p_q, a_q], 'mass_flow_rate' : total_deinked_amount, 'heat_flow_rate' : Q_out_total ,
                     'flow_type': 'Process', 'temperature' : coeff['Deinking temperature'],  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False},
            {'name' : 'Condensate (deinking)', 'components' : ['Water'], 'composition' : [1] ,'mass_flow_rate' : m_steam,
                     'flow_type': 'Condensate', 'temperature' : 100, 'heat_flow_rate' : sensible_heat,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False}]
Unit3.calculations = {'Screened recycled pulp' : Deinking_pulp}


#Unit 4: Washing (recycled line)
Unit4= Unit('Washing')
Unit4.temperature = ambient_t
Unit4.unit_type = ''
Unit4.expected_flows_in = ['Deinked pulp', 'Electricity (washing, recycled)', 'Water (washing, recycled)']
Unit4.expected_flows_out = ['Recycled pulp', 'Wastewater (washing, recycled)']
Unit4.coefficients = {'Washwater ratio' : 1, 'Electricity per ton' : 10}

def Washrec_pulp(deinkd_pulp, coeff):
    deinked_amount = deinkd_pulp.attributes['mass_flow_rate']
    drypulp_amount = deinked_amount * deinkd_pulp.attributes['composition'][deinkd_pulp.attributes['components'].index('Dry pulp')]
    additives_amount = deinked_amount * deinkd_pulp.attributes['composition'][deinkd_pulp.attributes['components'].index('Additives')]
    water_in_amount = deinked_amount * deinkd_pulp.attributes['composition'][deinkd_pulp.attributes['components'].index('Water')]
    Q_in = deinkd_pulp.attributes['heat_flow_rate']
    additives_cp = 2.5
    dry_paper_cp = 1.4
    water_cp = 4.2
    added_water = water_in_amount * coeff['Washwater ratio']
    new_t = amb_t + (Q_in/((additives_amount * additives_cp ) + (drypulp_amount * dry_paper_cp) + ((water_in_amount + added_water) * water_cp)))
    electricity_amount = deinked_amount * coeff['Electricity per ton']/1000.
    recycled_pulp_out = drypulp_amount + water_in_amount
    Q_rec = drypulp_amount * dry_paper_cp * (new_t - amb_t) + water_in_amount * water_cp * (new_t - amb_t)
    moist_out = water_in_amount/recycled_pulp_out
    wastewater_out = additives_amount + added_water
    Q_waste_water = Q_in - Q_rec
    additives_ratio = additives_amount / wastewater_out
    print('Unit 4')
    return [{'name' : 'Electricity (washing, recycled)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_amount ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Water (washing, recycled)', 'components' : ['Water'], 'composition' : [1] ,'mass_flow_rate' : added_water,
                     'flow_type': 'Water', 'temperature' : amb_t, 'heat_flow_rate' : 0,  'In or out' : 'In', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Recycled pulp', 'components' : ['Dry pulp', 'Water'], 'composition' : [1 - moist_out, moist_out], 'mass_flow_rate' : recycled_pulp_out, 'heat_flow_rate' : Q_rec ,
                     'flow_type': 'Process stream', 'temperature' : new_t,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False},
            {'name' : 'Wastewater (washing, recycled)', 'components' : ['Additives', 'Water'], 'composition' : [additives_ratio, 1-additives_ratio] ,'mass_flow_rate' : wastewater_out,
                     'flow_type': 'Waste', 'temperature' : new_t, 'heat_flow_rate' : Q_waste_water,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False}]
Unit4.calculations ={'Deinked pulp' : Washrec_pulp}

# Unit 5: Pulp Mixer 
Unit5 = Unit('Pulp Mixer')
Unit5.temperature = ambient_t
Unit5.unit_type = 'Mixer'
Unit5.required_calc_flows = 2
Unit5.expected_flows_in = ['Market Pulp', 'Recycled pulp']
Unit5.expected_flows_out = ['Pulp']
Unit5.coefficients = {}

def Pulp_mixer_func(ablist,coeff): 
    market_pulp_flow = ablist[0]
    recycled_pulp_flow = ablist[1]
    pulp_out = market_pulp_flow.attributes['mass_flow_rate'] + recycled_pulp_flow.attributes['mass_flow_rate']
    Q_out = recycled_pulp_flow.attributes['heat_flow_rate']
    print('Unit 5')
    return[{'name' : 'Pulp', 'components' : recycled_pulp_flow.attributes['components'], 'composition' : recycled_pulp_flow.attributes['composition'], 'mass_flow_rate' : pulp_out, 'heat_flow_rate' : 0,
            'flow_type': 'Process stream', 'temperature' : ambient_t,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False}, 
            {'Heat loss': Q_out}]
Unit5.calculations = (['Market Pulp', 'Recycled pulp'], Pulp_mixer_func)
FlowB = Flow(name='Market Pulp', components = ['Paper'], composition = [1], flow_type = 'input', mass_flow_rate = market_pulp_in, heat_flow_rate=0)
FlowB.set_calc_flow()
allflows.append(FlowB)

# Unit 6: Stock Preparation 
Unit6 = Unit('Stock preparation')
Unit6.expected_flows_in = ['Make-up water (Stock preparation)', 'Additives','Pulp' , 'Steam (Stock preparation)', 'Electricity (Stock preparation)' ]
Unit6.expected_flows_out = ['Thick stock', 'Condensate (Stock preparation)']
Unit6.coefficients = {'Electricity per ton of paper' : 274, 'Stock consistency' : 0.04, 'Energy consumption per ton of paper' : 0.7, 'Losses' : 0.1, 'Effluent per ton paper' : 10, 'Amount of additives per ton' : 50} 

def stock_prep(pulp_flow, coeff):
    pulp_in = pulp_flow.attributes['mass_flow_rate']
    paper_amount = pulp_in * (pulp_flow.attributes['composition'][pulp_flow.attributes['components'].index('Dry pulp')])
    water_in = pulp_in - paper_amount
    elec_in = paper_amount*coeff['Electricity per ton of paper']/1000. #kWh
    heat_in = paper_amount*coeff['Energy consumption per ton of paper']*1000. #GJ
    Q_steam = heat_in/(1 - coeff['Losses']) #GJ
    additives_amount = paper_amount*coeff['Amount of additives per ton']/1000.
    treated_paper_amount = paper_amount + additives_amount
    total_water = ((1 - coeff['Stock consistency'])/coeff['Stock consistency'])*treated_paper_amount
    makeup_water_amount = treated_paper_amount*coeff['Effluent per ton paper']
    cp_stock = 4.2
    water_vap_h = 2200
    steam_amount = Q_steam / water_vap_h
    Q_dew_point = steam_amount * cp_stock * (100-amb_t)
    Q_loss = Q_steam - heat_in
    total_outlet_amount = treated_paper_amount + total_water
    outlet_t = amb_t + (heat_in / (total_outlet_amount * cp_stock))
    print('Unit 6')
    return[{'name' : 'Electricity (Stock preparation)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_in ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Make-up water (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : makeup_water_amount,
                     'flow_type': 'Water', 'temperature' : amb_t, 'pressure': 1 , 'heat_flow_rate' : 0, 'combustion_energy_content' : 0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Additives', 'components' : ['Additives'], 'composition': [1], 'mass_flow_rate' : additives_amount,
                     'flow_type': 'Process flow', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_amount,
                     'flow_type': 'Steam', 'temperature' : 100, 'pressure':1 , 'heat_flow_rate' :Q_dew_point + Q_steam,'In or out' : 'In', 'Set calc' :False, 'Set shear' : False},
            {'name' : 'Condensate (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_amount,
                     'flow_type': 'Condensate', 'temperature' : 100, 'pressure':1 , 'heat_flow_rate' :Q_dew_point ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Thick stock', 'components' : ['Dry pulp', 'Additives', 'Water'], 'composition': [paper_amount/total_outlet_amount, additives_amount/total_outlet_amount, total_water/total_outlet_amount], 'mass_flow_rate' : pulp_in+ additives_amount + makeup_water_amount,
                     'flow_type': 'Process flow', 'temperature' : outlet_t, 'pressure':1 , 'heat_flow_rate' : heat_in ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'Heat loss' : Q_loss}]
Unit6.calculations = {'Pulp': stock_prep}

# Unit 7: Stock Split
Unit7 = Unit('Stock Splitter')
Unit7.temperature = ambient_t
Unit7.unit_type = 'Splitter'
Unit7.expected_flows_in = ['Thick stock']
Unit7.expected_flows_out = ['Stock to Tissues', 'Stock to Other']
Unit7.coefficients = {'Stock Split': stock_split}

def Stock_splitter_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    stock_to_other = feed_in * coeff['Stock Split']
    stock_to_tissue = feed_in - stock_to_other
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_tissue = (stock_to_tissue / feed_in) * Q_in 
    Q_other = Q_in - Q_tissue
    return[{'name' : 'Stock to Tissues', 'components' : feed_flow.attributes['components'], 'composition':  feed_flow.attributes['composition'], 'mass_flow_rate' : stock_to_tissue,
            'flow_type': 'Process flow', 'heat_flow_rate' : Q_tissue,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Stock to Other', 'components' : feed_flow.attributes['components'], 'composition':  feed_flow.attributes['composition'], 'mass_flow_rate' : stock_to_other,
            'flow_type': 'Process flow', 'heat_flow_rate' : Q_other,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}]
Unit7.calculations = {'Thick stock': Stock_splitter_func}

# Unit 8: Forming and press - Paper towels, toilet paper and other line
Unit8 = Unit('Forming and press')
Unit8.temperature = 30 
Unit8.unit_type = 'Splitter'
Unit8.expected_flows_in = ['Stock to Other' , 'Electricity (Forming and press)']
Unit8.expected_flows_out = ['Formed Other Paper', 'Wastewater (Forming and press)']
Unit8.coefficients = {'Electricity per ton of paper' : 238, 'Press consistency' : 0.4}
def form_and_press(thk_stock_flow, coeff):
    cp_stock = 4.2
    Q_in = thk_stock_flow.attributes['heat_flow_rate']
    paper_amount = thk_stock_flow.attributes['mass_flow_rate']*(thk_stock_flow.attributes['composition'][thk_stock_flow.attributes['components'].index('Dry pulp')] + thk_stock_flow.attributes['composition'][thk_stock_flow.attributes['components'].index('Additives')])
    water_in = thk_stock_flow.attributes['mass_flow_rate'] - paper_amount
    moisture_in_presspaper = ((1 - coeff['Press consistency']) * paper_amount)/coeff['Press consistency']
    ww_amount = water_in - moisture_in_presspaper
    elec_amount = paper_amount * coeff['Electricity per ton of paper']/1000.
    t_process = thk_stock_flow.attributes['temperature']
    total_paper_amount = moisture_in_presspaper + paper_amount
    Q_formed_p = cp_stock * (t_process - amb_t) * total_paper_amount
    Q_wastewater = Q_in -  Q_formed_p
    print('Unit 8')
    return [{'name' : 'Electricity (Forming and press)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_amount ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Formed Other Paper', 'components' : ['Paper', 'Water'], 'composition': [paper_amount/total_paper_amount, (1 - paper_amount)/total_paper_amount], 'mass_flow_rate' : total_paper_amount,
                     'flow_type': 'Process flow', 'temperature' : t_process, 'pressure': 1 , 'heat_flow_rate' : Q_formed_p, 'combustion_energy_content' : 0 ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'name' : 'Wastewater (Forming and press)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : ww_amount,
                     'flow_type': 'Wastewater', 'temperature' : t_process, 'pressure':1 , 'heat_flow_rate' :Q_wastewater ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False}]
Unit8.calculations = {'Stock to Other': form_and_press}

#Unit 20: Drying
Unit9= Unit('Other Dryer')
Unit9.temperature = 45
Unit9.expected_flows_in = ['Formed Other Paper', 'Electricity (Dryer, paper)', 'Air (Dryer, paper)', 'Steam (Dryer, paper)']
Unit9.expected_flows_out = ['Dried paper', 'Exhaust gas (Dryer, paper)', 'Condensate (Dryer, paper)']
Unit9.coefficients = {'Dry paper moisture' : 0.05 , 'Air temperature' : 80, 'd_T' : 5, 'Exhaust gas temperature' : 60, 'Electricity (kWh) per ton of paper' : 21, 'Paper temperature' : 45, 'Loss' : 0.1}

def Dryerfunc_paper(paper_pulp_flow, coeff):
    steam_t = coeff['Air temperature'] + coeff['d_T']
    paper_pulp_amount = paper_pulp_flow.attributes['mass_flow_rate']
    dry_paper_amount = paper_pulp_amount * paper_pulp_flow.attributes['composition'][paper_pulp_flow.attributes['components'].index('Paper')]
    water_amount = paper_pulp_amount - dry_paper_amount
    mu_m_out = coeff['Dry paper moisture']
    mass_m_out = (mu_m_out/(1-mu_m_out)) * dry_paper_amount
    paper_out_amount = dry_paper_amount + mass_m_out
    water_out_amount =  water_amount - mass_m_out
    air_t = coeff['Air temperature']
    exhaust_t = coeff['Exhaust gas temperature']
    electricity_amount = coeff['Electricity (kWh) per ton of paper'] * dry_paper_amount / 1000.
    t_in = paper_pulp_flow.attributes['temperature']
    dried_paper_out_t = coeff['Paper temperature']
    cp_water = 4.2 #kJ/kg.K
    cp_steam = 1.89 #kJ/kg.K
    cp_dry_paper = 2.3
    cp_air = 1.01
    vap_heat = 2256.4 #kJ/kg
    Q_water_out = water_out_amount * ((cp_steam * (exhaust_t - 100)) + (cp_water *(100 - t_in ) ) + vap_heat)
    Q_dry_paper_out = dry_paper_amount * cp_dry_paper * (dried_paper_out_t - t_in)
    Q_moisture_out = mass_m_out * cp_water * (dried_paper_out_t - t_in)
    Q_dried_paper = Q_dry_paper_out + Q_moisture_out
    m_air = (Q_water_out + Q_dried_paper)/(cp_air * (air_t - exhaust_t))
    Q_air_out = m_air * cp_air * (exhaust_t - amb_t)
    Q_air_in = m_air * cp_air * (air_t - amb_t)
    Q_in = paper_pulp_flow.attributes['heat_flow_rate']
    Q_exhaust = Q_air_out + Q_water_out
    Q_steam = ((Q_exhaust + Q_dried_paper)/(1 - coeff['Loss'])) - Q_in
    Q_loss = Q_steam * coeff['Loss']
    vap_heat_130 = 2173.7
    m_steam = Q_steam/vap_heat_130
    cp_wat_130 = 4.26
    Q_condensate = m_steam * cp_wat_130 * (steam_t - amb_t)
    Q_steam_in = Q_steam + Q_condensate
    exhaust_amount = water_out_amount + m_air
    exhaust_gas_water_ratio = water_out_amount/exhaust_amount
    print('Unit 9')
    return [{'name' : 'Electricity (Dryer, paper)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_amount ,  'Set calc' : False, 'Set shear' : False},     
            {'name' : 'Air (Dryer, paper)', 'components' : ['Air'], 'composition': [1], 'mass_flow_rate' : m_air,
                     'flow_type': 'Air', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Condensate (Dryer, paper)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Condensate', 'temperature' : steam_t, 'pressure':2.7 , 'heat_flow_rate' :Q_condensate ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Dryer, paper)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Steam', 'temperature' : steam_t, 'pressure':2.7 , 'heat_flow_rate' :Q_steam_in ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Exhaust gas (Dryer, paper)', 'components' : ['Water', 'Air'], 'composition': [exhaust_gas_water_ratio, 1 - exhaust_gas_water_ratio], 'mass_flow_rate' : exhaust_amount,
                     'flow_type': 'Exhaust', 'temperature' : exhaust_t, 'pressure':1 , 'heat_flow_rate' :Q_exhaust ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Dried paper', 'components' : ['Dry pulp', 'Water'], 'composition': [1 - mu_m_out, mu_m_out], 'mass_flow_rate' : paper_out_amount,
                     'flow_type': 'Process Stream', 'temperature' : dried_paper_out_t, 'pressure':1 , 'heat_flow_rate' :Q_dried_paper ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'Heat loss'  : Q_loss}]
Unit9.calculations = {'Formed Other Paper' : Dryerfunc_paper}

# Unit 10 - Tissue paper line 
Unit10 = Unit('Fourdrinier Wire')
Unit10.temperature = 30 
Unit10.unit_type = 'Splitter' 
Unit10.expected_flows_in = ['Stock to Tissues', 'Electricity (Fourdrinier Wire)']
Unit10.expected_flows_out = ['Wet Web', 'Wastewater (Fourdrinier Wire)']
Unit10.coefficients = {'Outlet water wt': .80, 'Electricity (kw/kg)': 0.05}

def Fourdrinier_wire_func(feed_flow, coeff):
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    solids_in = feed_in - water_in 
    feed_out = solids_in / (1-coeff['Outlet water wt'])
    water_out = feed_in - feed_out 
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 10')
    return[{'name' : 'Electricity (Fourdrinier Wire)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Wet Web', 'components' : ['Pulp', 'Water'], 'composition':  [1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : 0,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'name' : 'Wastewater (Fourdrinier Wire)', 'components' : ['Water'], 'composition':  [1], 'mass_flow_rate' : water_out,
            'flow_type': 'Wastewater', 'heat_flow_rate' : Q_in,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}]
Unit10.calculations = {'Stock to Tissues': Fourdrinier_wire_func}

# Unit 11 - Through-Air Dryer 
Unit11 = Unit('Through Air Dryer')
Unit11.temperature = 170 
Unit11.unit_type = 'Splitter'
Unit11.expected_flows_in = ['Wet Web', 'Electricity (TAD)', 'Fuel (TAD)', 'Air (TAD)']
Unit11.expected_flows_out = ['Dry Web', 'Exhaust (TAD)']
Unit11.coefficients = {'Outlet water wt': .30, 'Electricity (kw/kg)': 3.25, 'Fuel HHV': 5200, 'loses': 0.10, 'Air Ratio': 3.0, 'Exhaust Temp': 200, 
                       'Unit Temp': Unit11.temperature}

def Through_air_dryer_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    water_in = feed_in * (feed_flow.attributes['composition'][feed_flow.attributes['components'].index('Water')])
    solids_in = feed_in - water_in 
    feed_out = solids_in / (1-coeff['Outlet water wt'])
    water_evap = feed_in - feed_out 
    t_in = ambient_t
    Q_water_evap = (water_evap * Hvap) + (water_evap * C_pw * (100-t_in))
    C_psolids = ((1-coeff['Outlet water wt']) * 2.3) + (coeff['Outlet water wt'] * C_pw)
    Q_solids = C_psolids * feed_out * (coeff['Unit Temp'] - ambient_t)
    Q_in = feed_flow.attributes['heat_flow_rate']
    m_air = coeff['Air Ratio'] * feed_in
    Q_air = m_air * C_pair * (coeff['Exhaust Temp'] - ambient_t)
    Q_fuel = (Q_water_evap + Q_solids + Q_air - Q_in) / (1-coeff['loses'])
    Q_loss = Q_fuel * coeff['loses']
    m_fuel = Q_fuel / coeff['Fuel HHV']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 11')
    return[{'name' : 'Fuel (TAD)', 'components' : ['Fuel'], 'composition' : [1], 'mass_flow_rate' : m_fuel,
             'flow_type': 'Fuel', 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_fuel, 'combustion_energy_content': Q_fuel},
           {'name' : 'Air (TAD)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_air,
             'flow_type': 'Air', 'elec_flow_rate' : 0, 'temperature': ambient_t, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
           {'name' : 'Exhaust (TAD)', 'components' : ['Air'], 'composition' : [1], 'mass_flow_rate' : m_air+m_fuel+water_evap,
             'flow_type': 'Exhaust', 'elec_flow_rate' : 0, 'temperature': coeff['Exhaust Temp'], 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': Q_air+Q_water_evap}, 
            {'name' : 'Dry Web', 'components' : ['Pulp', 'Water'], 'composition':  [1-coeff['Outlet water wt'], coeff['Outlet water wt']], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate' : Q_solids,'In or out' : 'Out', 'Set calc' : True, 'Set shear': False}, 
            {'Heat loss': Q_loss}, 
            {'name' : 'Electricity (TAD)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}]
Unit11.calculations = {'Wet Web': Through_air_dryer_func}

# Unit 12: Other Paper Processing 
Unit12 = Unit('Other Paper Finishing')
Unit12.temperature = ambient_t
Unit12.unit_type = 'Mechanical Process'
Unit12.expected_flows_in = ['Dried paper', 'Electricity (Other Finishing)']
Unit12.expected_flows_out = ['Finished Other Products']
Unit12.coefficients = {'Electricity (kw/kg)': 0.13}

def Other_paper_finishing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 12')
    return[{'name' : 'Electricity (Other Finishing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Finished Other Products', 'components' : ['Product'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Product', 'heat_flow_rate' : Q_in,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}]
Unit12.calculations = {'Dried paper': Other_paper_finishing_func}

# Unit 13: Tissue Paper Finishing
Unit13 = Unit('Tissue Paper Finishing')
Unit13.temperature = ambient_t
Unit13.unit_type = 'Mechanical Process'
Unit13.expected_flows_in = ['Dry Web', 'Electricity (Tissue Finishing)']
Unit13.expected_flows_out = ['Finished Tissue Products']
Unit13.coefficients = {'Electricity (kw/kg)': 0.13}

def Tissue_paper_finishing_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    print('Unit 13')
    return[{'name' : 'Electricity (Tissue Finishing)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Finished Tissue Products', 'components' : ['Tissue'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Product', 'heat_flow_rate' : Q_in,'In or out' : 'Out', 'Set calc' : False, 'Set shear': False}]
Unit13.calculations = {'Dry Web': Tissue_paper_finishing_func}

#############################################################################################################################################
processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6, Unit7, Unit8, Unit9, Unit10, 
                Unit11, Unit12, Unit13]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_sanitary_products_manufacturing', allflows, processunits)
