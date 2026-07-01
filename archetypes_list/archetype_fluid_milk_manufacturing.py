'''
Name: Aidan ONeil
Date: September 4th, 2025

Last updated on Jul 1 2026

This is the python model for fluid milk production. It can only be run with the 
archetypes base library available at https://github.com/ISALGroup/archetypes/tree/main/base.
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
For the present model, the author is Aidan O'Neil. For any questions, please get
in touch: ajo76@ucsb.edu.
For other questions about the Industrial Sustainability Analysis Laboratory
or to collaborate with us, please contact the head of the laboratory 
Prof. Eric Masanet: emasanet@ucsb.edu


@author: Aidan

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

ambient_t = 4
material_input = 1000
C_pw = 4.21
Hvap = 2260
C_pmilk = 3.80



################################################UNITS##########################################
# Unit 1: Clarification 
Unit1 = Unit('Clarification')
Unit1.temperature = ambient_t
Unit1.unit_type = 'Seperator'
Unit1.expected_flows_in = ['Feed Milk', 'Electricity (Clarification)']
Unit1.expected_flows_out = ['Clarified Milk', 'Waste (Clarification)']
Unit1.coefficients = {'Waste Ratio': 0.01, 'Electricity (kw/kg)': 0.0023}

def Clarfication_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    waste_out = feed_in * coeff['Waste Ratio']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    feed_out = feed_in - waste_out 
    print('Unit 1')
    return[{'name' : 'Electricity (Clarification)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Waste (Clarification)', 'components' : ['Waste'], 'composition':  [1], 'mass_flow_rate' : waste_out,
            'flow_type': 'Waste', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : False}, 
            {'name' : 'Clarified Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit1.calculations = {'Feed Milk': Clarfication_func}
FlowA = Flow('Feed Milk',['Milk'],'input', ambient_t, 1, [1], None , None, material_input, np.nan, 0)
FlowA.set_calc_flow()
allflows.append(FlowA)

# Unit 2: Separation 
Unit2 = Unit('Seperator')
Unit2.temperature = ambient_t 
Unit2.unit_type = 'Seperator'
Unit2.expected_flows_in = ['Clarified Milk', 'Electricity (Seperator)']
Unit2.expected_flows_out = ['Cream', 'Unpastuerized Milk']
Unit2.coefficients = {'Electricity (kw/kg)': 0.0052, 'Cream wt': 0.02 }

def Seperator_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    cream_out = feed_in * coeff['Cream wt']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    feed_out = feed_in - cream_out 
    print('Unit 2')
    return[{'name' : 'Electricity (Seperator)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0},
           {'name' : 'Cream', 'components' : ['Cream'], 'composition':  [1], 'mass_flow_rate' : cream_out,
            'flow_type': 'Product', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : False}, 
            {'name' : 'Unpastuerized Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_out,
            'flow_type': 'Process stream', 'heat_flow_rate': 0 ,'In or out' : 'Out', 'Set calc' : True}]
Unit2.calculations = {'Clarified Milk': Seperator_func}

# Unit 3: Pasteruization 
Unit3 = Unit('Pasturization')
Unit3.temperature = 70
Unit3.unit_type = 'Other'
Unit3.expected_flows_in = ['Unpastuerized Milk', 'Steam (Pasteurization)']
Unit3.expected_flows_out = ['Pastuerized Milk', 'Condensate (Pastuerization)']
Unit3.coefficients = {'Unit Temp': Unit3.temperature, 'Steam Temp': 100, 'loses': 0.10}

def Pastuerization_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_steam = (Q_out - Q_in) / (1-coeff['loses'])
    Q_loss= Q_steam * coeff['loses']
    m_steam = Q_steam / Hvap 
    print('Unit 3')
    return[{'name' : 'Steam (Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
             'flow_type': 'Steam', 'Temperature': coeff['Steam Temp'], 'elec_flow_rate' : 0, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': Q_steam},
           {'name' : 'Condensate (Pasteurization)', 'components' : 'Water', 'mass_flow_rate' : m_steam,
            'flow_type': 'Condensate', 'elec_flow_rate' : 0, 'In or out' : 'Out', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'Heat loss': Q_loss}, 
            {'name' : 'Pastuerized Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_out ,'In or out' : 'Out', 'Set calc' : True}]
Unit3.calculations = {'Unpastuerized Milk': Pastuerization_func}

# Unit 4: Homogenization 
Unit4 = Unit('Homogenization')
Unit4.temperature = Unit3.temperature
Unit4.unit_type = 'Mechanical Process'
Unit4.expected_flows_in = ['Pastuerized Milk', 'Electricity (Homogenization)']
Unit4.expected_flows_out = ['Homogenized Milk']
Unit4.coefficients = {'Electricity (kw/kg)': 0.0029}

def Homogenization_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 4')
    return[{'name' : 'Electricity (Homogenization)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Homogenized Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_in ,'In or out' : 'Out', 'Set calc' : True}]
Unit4.calculations = {'Pastuerized Milk': Homogenization_func}

# Unit 5: Cooling 
Unit5 = Unit('Cooler')
Unit5.temperature = 7 
Unit5.unit_type = 'Other'
Unit5.expected_flows_in = ['Homogenized Milk', 'Chilling (Cooler)']
Unit5.expected_flows_out = ['Cooled Milk']
Unit5.coefficients = {'Unit Temp': Unit5.temperature}

def Cooler_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    Q_in = feed_flow.attributes['heat_flow_rate']
    Q_out = feed_in * C_pmilk * (coeff['Unit Temp'] - ambient_t)
    Q_chilling = Q_out - Q_in 
    print('Unit 5')
    return[{'name' : 'Cooled Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Process stream', 'heat_flow_rate': Q_out ,'In or out' : 'Out', 'Set calc' : True}, 
            {'name' : 'Chilling (Cooler)', 'components' : ['Cooling Water'], 'composition':  [1], 'mass_flow_rate' : 0,
            'flow_type': 'Chilling', 'heat_flow_rate': Q_chilling ,'In or out' : 'In', 'Set calc' : False}]
Unit5.calculations = {'Homogenized Milk': Cooler_func}

# Unit 6: Packaging 
Unit6 = Unit('Packaging')
Unit6.temperature = Unit5.temperature
Unit6.unit_type = 'Mechanical Process'
Unit6.expected_flows_in = ['Cooled Milk', 'Electricity (Packaging)']
Unit6.expected_flows_out = ['Product Milk']
Unit6.coefficients = {'Electricity (kw/kg)': 0.015}

def Packaging_func(feed_flow, coeff): 
    feed_in = feed_flow.attributes['mass_flow_rate']
    electricity_in = feed_in * coeff['Electricity (kw/kg)']
    Q_in = feed_flow.attributes['heat_flow_rate']
    print('Unit 6')
    return[{'name' : 'Electricity (Packaging)', 'mass_flow_rate' : 0,
             'flow_type': 'Electricity', 'elec_flow_rate' : electricity_in, 'In or out' : 'In', 'Set calc' : False, 'heat_flow_rate': 0}, 
            {'name' : 'Product Milk', 'components' : ['Milk'], 'composition':  [1], 'mass_flow_rate' : feed_in,
            'flow_type': 'Product', 'heat_flow_rate': Q_in ,'In or out' : 'Out', 'Set calc' : True}]
Unit6.calculations = {'Cooled Milk': Packaging_func}

##########################################################################################################################################################################################

processunits = [Unit1, Unit2, Unit3, Unit4, Unit5, Unit6]

main(allflows, processunits)

for unit in processunits:
    unit.check_heat_balance(allflows)
    unit.check_mass_balance(allflows)

for flow in allflows:
    if flow.attributes['flow_type'] == 'Product':
        print(flow)

utilities_recap('heat_intensity_fluid_milk_2', allflows, processunits)
