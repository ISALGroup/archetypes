# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 12:04:45 2024
Last updated on Aug 3 2026

This is the python model for paper production from recycled paper (the
"finishing" archetype, NAICS 322120 - Paper mills, Recycling/finishing
variation). It can only be run with the archetypes base library available at
https://github.com/ISALGroup/archetypes/tree/main/base.
A user manual for using the base library and the different archetypes developed 
is also available on the ISAL team's GitHub page. Accompanying documents, 
namely: 1. the technical appendix, which contains the team's general approach
to modeling and 2. the individual documents for each archetype can also 
be found on the 2035 Initiative website, available at https://www.2035initiative.com/.

The archetypes are free to use, distribute, and modify. If you use any of the
archetypes results or the framework in your work, please cite either:
- the 2035 initiative report:
The 2035 Initiative. The Clean Heat Climate Opportunity: A Roadmap for Electrifying 
Low- and Medium-Temperature Industrial Heat. December 2025.
- the technical appendix:
The 2035 Initiative. The Clean Heat Climate Opportunity: A Roadmap for Electrifying 
Low- and Medium-Temperature Industrial Heat - Technical Appendix. July 2025.
- or the citation contained in the CFF file available on the GitHub repository.

UCSB, the Industrial Sustainability Analysis Laboratory, The 2035 Initiative
and the different authors that participated in the production of the models 
or the accompanying documents are not responsible or liable for
any claim, damages or other liabilities associated with the use of the software
or their results. 

For further information about the software, please contact the author
Antoine Merlo: a_merlo@ucsb.edu or merloantoine0@gmail.com.
For the present model, the author is Antoine Merlo. For any questions, please get
in touch: a_merlo@ucsb.edu or merloantoine0@gmail.com.
For other questions about the Industrial Sustainability Analysis Laboratory
or to collaborate with us, please contact the head of the laboratory 
Prof. Eric Masanet: emasanet@ucsb.edu


@author: Antoine


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



## Global variables
amb_t = 20
paper_moisture = 0.05 #moisture content of incoming recycled (waste) paper
recycled_paper_flow = 1000. #kg/hr of recycled paper fed to the mill


#Unit 1: Pulping

Unit1 = Unit('Pulping')
Unit1.expected_flows_in = ['Recycled paper', 'Electricity (Pulping)', 'Water (Pulping)', 'Steam (Pulping)']
Unit1.expected_flows_out = ['Pulped paper', 'Condensate (Pulping)']


Unit1.coefficients = {'Consistency' : 0.15, 'Pulping temperature' : 80, 'Electricity per t paper' : 28}

def pulping_func(waste_paper, coeff):
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

    return [{'name' : 'Electricity (Pulping)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_in ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Water (Pulping)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : water_in,
                     'flow_type': 'Water', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Pulping)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Steam', 'temperature' : steam_t, 'pressure':1 , 'heat_flow_rate' :Q_steam_total ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Condensate (Pulping)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : m_steam,
                     'flow_type': 'Condensate', 'temperature' : steam_t, 'pressure': 1 , 'heat_flow_rate' :Q_sensible_steam ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Pulped paper', 'components' : ['Dry pulp', 'Water'], 'composition': [coeff['Consistency'], 1 - coeff['Consistency']], 'mass_flow_rate' : total_pulp,
                     'flow_type': 'Process', 'temperature' : coeff['Pulping temperature'], 'pressure':1 , 'heat_flow_rate' :Q_total,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False}
            ]

Unit1.calculations = {'Recycled paper' : pulping_func}

#Unit 2: Screening

Unit2 = Unit('Screening')
Unit2.expected_flows_in = ['Pulped paper', 'Electricity (Screening)']
Unit2.expected_flows_out = ['Screened pulp', 'Rejects (Screening)']


Unit2.coefficients = {'Rejects amount' : 0.05, 'Electricity per ton' : 23}

def screening_func(waste_pulp, coeff):
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
    return [{'name' : 'Electricity (Screening)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_amount ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Rejects (Screening)', 'components' : ['Water', 'Dry pulp'], 'composition' : [moisture, 1 - moisture] ,'mass_flow_rate' : rejects_amount,
                     'flow_type': 'Waste', 'temperature' : t_in, 'heat_flow_rate' : Q_rejects ,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Screened pulp', 'components' : ['Water', 'Dry pulp'], 'composition' : [moisture, 1 - moisture], 'mass_flow_rate' : pulp_out, 'heat_flow_rate' : Q_out ,
                     'flow_type': 'Process', 'temperature' : t_in,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False}
            ]

Unit2.calculations = {'Pulped paper' : screening_func}

#Unit 3: De-inking

Unit3 = Unit('Deinking')
Unit3.expected_flows_in = ['Screened pulp', 'Electricity (deinking)', 'Steam (deinking)', 'Water (deinking)', 'Additives (deinking)']
Unit3.expected_flows_out = ['Deinked pulp', 'Condensate (deinking)']


Unit3.coefficients = {'Additives quantity' : 0.05, 'Electricity per t' : 10, 'Deinking temperature' : 42.5, 'Consistency' : 0.015}

def deinking_func(screened_pulp, coeff):
    pulp_amount = screened_pulp.attributes['mass_flow_rate']
    dry_part = screened_pulp.attributes['composition'][screened_pulp.attributes['components'].index('Dry pulp')]
    additives_cp = 2.5
    dry_paper_cp = 1.4
    water_cp = 4.2
    vap_heat = 2256.4
    dry_pulp = pulp_amount * dry_part
    Q_in = screened_pulp.attributes['heat_flow_rate']
    additives_amount = dry_pulp * coeff['Additives quantity']
    deinked_drypart = additives_amount + dry_pulp
    total_deinked_amount = deinked_drypart/coeff['Consistency']
    water_out = total_deinked_amount - deinked_drypart
    elec_in = total_deinked_amount * coeff['Electricity per t'] / 1000.
    Q_out_total = ((additives_amount*additives_cp) + (dry_pulp* dry_paper_cp) + (water_out* water_cp)) * (coeff['Deinking temperature'] - amb_t)
    Q_heat_added = Q_out_total - Q_in
    moist_in = screened_pulp.attributes['composition'][screened_pulp.attributes['components'].index('Water')]
    moisture = moist_in * pulp_amount
    water_in = water_out - moisture
    m_steam = Q_heat_added/2256.4
    a_q = additives_amount/total_deinked_amount
    w_q = (1- coeff['Consistency'])
    p_q = dry_pulp / total_deinked_amount
    sensible_heat = m_steam * water_cp *(100 - amb_t)
    Q_steam = Q_heat_added + sensible_heat

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
                     'flow_type': 'Condensate', 'temperature' : 100, 'heat_flow_rate' : sensible_heat,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False}
            ]

Unit3.calculations = {'Screened pulp' : deinking_func}

#Unit 4: Washing

Unit4 = Unit('Washing')
Unit4.expected_flows_in = ['Deinked pulp', 'Electricity (washing)', 'Water (washing)']
Unit4.expected_flows_out = ['Washed pulp', 'Wastewater (washing)']


Unit4.coefficients = {'Washwater ratio' : 1, 'Electricity per ton' : 3}

def washing_func(deinkd_pulp, coeff):
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
    washed_pulp_out = drypulp_amount + water_in_amount
    Q_wash = drypulp_amount * dry_paper_cp * (new_t - amb_t) + water_in_amount * water_cp * (new_t - amb_t)
    moist_out = water_in_amount/washed_pulp_out
    wastewater_out = additives_amount + added_water
    Q_waste_water = Q_in - Q_wash
    additives_ratio = additives_amount / wastewater_out
    return [{'name' : 'Electricity (washing)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : electricity_amount ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Water (washing)', 'components' : ['Water'], 'composition' : [1] ,'mass_flow_rate' : added_water,
                     'flow_type': 'Water', 'temperature' : amb_t, 'heat_flow_rate' : 0,  'In or out' : 'In', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Washed pulp', 'components' : ['Dry pulp', 'Water'], 'composition' : [1 - moist_out, moist_out], 'mass_flow_rate' : washed_pulp_out, 'heat_flow_rate' : Q_wash ,
                     'flow_type': 'Water', 'temperature' : new_t,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : True, 'Set shear' : False},
            {'name' : 'Wastewater (washing)', 'components' : ['Additives', 'Water'], 'composition' : [additives_ratio, 1-additives_ratio] ,'mass_flow_rate' : wastewater_out,
                     'flow_type': 'Waste', 'temperature' : new_t, 'heat_flow_rate' : Q_waste_water,  'In or out' : 'Out', 'elec_flow_rate' : 0 ,  'Set calc' : False, 'Set shear' : False}
            ]

Unit4.calculations = {'Deinked pulp' : washing_func}

#Unit 5: Stock preparation

Unit5 = Unit('Stock preparation')
Unit5.expected_flows_in = ['Washed pulp' , 'Make-up water (Stock preparation)', 'Recirculated water (Stock preparation)', 'Additives', 'Steam (Stock preparation)', 'Electricity (Stock preparation)' ]
Unit5.expected_flows_out = ['Thick stock', 'Condensate (Stock preparation)']


Unit5.coefficients = {'Electricity per ton of paper' : 274, 'Stock consistency' : 0.04, 'Energy consumption per ton of paper' : 0.7, 'Losses' : 0.1, 'Effluent per ton paper' : 10, 'Amount of additives per ton' : 50}

def stock_prep(washpulp_flow, coeff):
    washpulp_amount = washpulp_flow.attributes['mass_flow_rate']
    paper_amount = washpulp_amount*washpulp_flow.attributes['composition'][washpulp_flow.attributes['components'].index('Dry pulp')]
    water_in = washpulp_amount*washpulp_flow.attributes['composition'][washpulp_flow.attributes['components'].index('Water')]
    elec_in = paper_amount*coeff['Electricity per ton of paper']/1000. #kWh
    heat_in = paper_amount*coeff['Energy consumption per ton of paper']*1000. #GJ
    Q_steam = heat_in/(1 - coeff['Losses']) #GJ
    additives_amount = paper_amount*coeff['Amount of additives per ton']/1000.
    treated_paper_amount = paper_amount + additives_amount
    total_water = ((1 - coeff['Stock consistency'])/coeff['Stock consistency'])*treated_paper_amount
    makeup_water_amount = treated_paper_amount*coeff['Effluent per ton paper']
    recirculated_water_amount = total_water - makeup_water_amount - water_in
    cp_stock = 4.2
    water_vap_h = 2200
    steam_amount = Q_steam / water_vap_h
    Q_dew_point = steam_amount * cp_stock * (100-amb_t)
    Q_loss = Q_steam - heat_in
    total_outlet_amount = treated_paper_amount + total_water
    outlet_t = amb_t + ((washpulp_flow.attributes['heat_flow_rate'] + heat_in)/(total_outlet_amount*cp_stock))

    return[{'name' : 'Electricity (Stock preparation)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_in ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Make-up water (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : makeup_water_amount,
                     'flow_type': 'Water', 'temperature' : amb_t, 'pressure': 1 , 'heat_flow_rate' : 0, 'combustion_energy_content' : 0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Recirculated water (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : recirculated_water_amount,
                     'flow_type': 'Process flow', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Additives', 'components' : ['Additives'], 'composition': [1], 'mass_flow_rate' : additives_amount,
                     'flow_type': 'Process flow', 'temperature' : amb_t, 'pressure':1 , 'heat_flow_rate' :0 ,'In or out' : 'In', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Steam (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_amount,
                     'flow_type': 'Steam', 'temperature' : 100, 'pressure':1 , 'heat_flow_rate' :Q_dew_point + Q_steam,'In or out' : 'In', 'Set calc' :False, 'Set shear' : False},
            {'name' : 'Condensate (Stock preparation)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : steam_amount,
                     'flow_type': 'Condensate', 'temperature' : 100, 'pressure':1 , 'heat_flow_rate' :Q_dew_point ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'name' : 'Thick stock', 'components' : ['Dry pulp', 'Additives', 'Water'], 'composition': [paper_amount/total_outlet_amount, additives_amount/total_outlet_amount, total_water/total_outlet_amount], 'mass_flow_rate' : total_outlet_amount,
                     'flow_type': 'Process flow', 'temperature' : outlet_t, 'pressure':1 , 'heat_flow_rate' : washpulp_flow.attributes['heat_flow_rate'] + heat_in ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'Heat loss' : Q_loss}
        ]

Unit5.calculations = {'Washed pulp' :  stock_prep  }

#Unit 6: Forming and press

Unit6 = Unit('Forming and press')
Unit6.expected_flows_in = ['Thick stock' , 'Electricity (Forming and press)']
Unit6.expected_flows_out = ['Formed paper', 'Wastewater (Forming and press)']

Unit6.coefficients = {'Electricity per ton of paper' : 238, 'Press consistency' : 0.4}

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
    return [{'name' : 'Electricity (Forming and press)', 'components' : None, 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'temperature' : 0,  'In or out' : 'In', 'elec_flow_rate' : elec_amount ,  'Set calc' : False, 'Set shear' : False},
            {'name' : 'Formed paper', 'components' : ['Paper', 'Water'], 'composition': [paper_amount/total_paper_amount, (1 - paper_amount)/total_paper_amount], 'mass_flow_rate' : total_paper_amount,
                     'flow_type': 'Process flow', 'temperature' : t_process, 'pressure': 1 , 'heat_flow_rate' : Q_formed_p, 'combustion_energy_content' : 0 ,'In or out' : 'Out', 'Set calc' : True, 'Set shear' : False},
            {'name' : 'Wastewater (Forming and press)', 'components' : ['Water'], 'composition': [1], 'mass_flow_rate' : ww_amount,
                     'flow_type': 'Wastewater', 'temperature' : t_process, 'pressure':1 , 'heat_flow_rate' :Q_wastewater ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False}
        ]

Unit6.calculations = {'Thick stock': form_and_press}

#Unit 7: Drying

Unit7 = Unit('Dryer (paper)')
Unit7.expected_flows_in = ['Formed paper', 'Electricity (Dryer, paper)', 'Air (Dryer, paper)', 'Steam (Dryer, paper)']
Unit7.expected_flows_out = ['Dried paper', 'Exhaust gas (Dryer, paper)', 'Condensate (Dryer, paper)']


Unit7.coefficients = {'Dry paper moisture' : 0.05 , 'Air temperature' : 110, 'd_T' : 5, 'Exhaust gas temperature' : 100, 'Electricity (kWh) per ton of paper' : 21, 'Paper temperature' : 45, 'Loss' : 0.1}


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
    Q_dry_paper_out = dry_paper_amount * cp_dry_paper * (dried_paper_out_t - amb_t)
    Q_moisture_out = mass_m_out * cp_water * (dried_paper_out_t - amb_t)
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
                     'flow_type': 'Product', 'temperature' : dried_paper_out_t, 'pressure':1 , 'heat_flow_rate' :Q_dried_paper ,'In or out' : 'Out', 'Set calc' : False, 'Set shear' : False},
            {'Heat loss'  : Q_loss}

            ]

Unit7.calculations = {'Formed paper' : Dryerfunc_paper}


processunits = [Unit1,Unit2,Unit3,Unit4,Unit5,Unit6,Unit7]



FlowA = Flow('Recycled paper',['Water', 'Paper'],'input', amb_t, 1, [paper_moisture, 1 - paper_moisture], None , None, recycled_paper_flow, np.nan, 0)
FlowA.set_calc_flow()
allflows.append(FlowA)

main(allflows, processunits, f_print = True)
print(are_units_calced(processunits))

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

#unit_recap_to_file('paper_finishing', allflows, processunits)

#utilities_recap('paper_finishing', allflows, processunits)