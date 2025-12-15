# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 15:26:55 2024

@author: Antoine
"""
allflows = []
processunits = []

#Our framework is mainly composed of only two classes: Flows and Units.
# The Flows represent material or energy flows in the process, and have a series
# of caracteristics described later. They should always be linked to 1 (input, product
# or waste flows e.g.) or 2 units (process flows).
# Units represent steps in the process that induce changes in the flows. They
# can be a reactor changing two or more different components into on or more
# products for example. They are caracterized by the flows that come in and out
# of them and by a series of calculations that allow them to work out the values
# of different flows knowing the caracteristics of the units and at least one 
# other flow

class Flow:
    def __init__(self, name, components, flow_rate, flow_type,
                 temperature=25, composition = [1], origin = None, 
                 destination = None, is_calc_flow = False):
        self.name = name
        #Name of the flow
        self.components = components
        #Components of the flow. For now they are only a string, but when handling
        # chemical units in the future, they should be lists
        self.flow_rate = flow_rate
        #Flow rate. Can be power for electric flows. Units are set ad hoc for now
        #but could be tuple in the future of the value + unit
        self.temperature = temperature
        #Temperature of the flow. For now set by default at 25C, but units should
        #also be taken into account
        self.flow_type = flow_type
        #Type of the flow in the flow sheet. These include for example input flows,
        #products, process flows, fuels, heat, electricity...
        self.composition = composition
        #Composition of the flow. List of values, so for example a stream made 
        #of ammonia and water with [0.4,0.6] as composition is made of 40%ammonia
        #and 60% water
        self.origin = origin
        #Unit from which the flow comes out of
        self.destination = destination
        #Unit in which the flow arrive
        self.is_calc_flow = is_calc_flow
        #Flag which tells the archetype that all the calculations in the program
        #should be made according to that flow. For example, if a product stream
        #is flagged as such, all the input, energy... streams values will be
        #calculated according to that stream.
    
    def set_destination(self, Destination_unit):
        #Function to set the destination of the stream to a given unit.
        #It will also put the stream in the list of streams that go into that unit
        if Destination_unit == self.destination and self in Destination_unit.input_flows:
            pass
        
        elif Destination_unit != self.destination and self not in Destination_unit.input_flows:
            Destination_unit.input_flows.append(self)
            self.destination = Destination_unit 
        elif Destination_unit != self.destination:    
            self.destination = Destination_unit
        else:
            Destination_unit.input_flows.append(self)
        
    def set_origin(self, Origin_unit):
        #Function to set the origin of the stream from a given unit.
        #It will also put the stream in the list of streams that go out of that unit
        if Origin_unit == self.origin and self in Origin_unit.input_flows:
            pass
        
        elif Origin_unit != self.origin and self not in Origin_unit.input_flows:
            Origin_unit.input_flows.append(self)
            self.origin = Origin_unit 
        elif Origin_unit != self.origin:    
            self.origin = Origin_unit
        else:
            Origin_unit.input_flows.append(self)
    
    def set_calc_flow(self):
        self.is_calc_flow = True


class Unit:
    def __init__(self, name, input_flows = [], output_flows = [], 
                 calculations = {}, expected_flows_in = [], expected_flows_out = [], coefficients = []):
        self.name = name
        #Name of the unit
        self.input_flows = input_flows
        #Flows coming into the unit
        self.output_flows = output_flows
        #Flows coming out of the unit
        self.calculations = calculations
        #Functions used by the unit to calculate values of the streams using 
        #the values of other streams and the parameters of the unit (in "coefficients")
        #For now they take the form of a dictionnary. For example, if the calc_stream
        #is an input, a function will be called linked to that input. But if 
        #another stream was used, other functions would be called. I am still
        #looking for a more elegant way to handle that than having as many functions
        #as there are streams.
        self.expected_flows_in = expected_flows_in
        #Expected flows coming in the unit
        self.expected_flows_out = expected_flows_out
        #Expected flows coming out of the unit
        self.coefficients = coefficients
        #Coefficients used by the calculations of the unit
    def add_input(self, Input_flow):
        #Function to add an input stream to the unit
        if Input_flow in self.input_flows and self == Input_flow.destination:
            pass
        elif Input_flow not in self.input_flows and self != Input_flow.destination:
            Input_flow.destination = self
            self.input_flows.append(Input_flow)
        elif Input_flow not in self.input_flows:    
            self.input_flows.append(Input_flow)
        else:
            Input_flow = self
    
    def add_output(self, Output_flow):
        #Function to add an output stream to the unit
        if Output_flow in self.output_flows and self != Output_flow.origin:
            pass
        elif Output_flow not in self.Output_flows and self != Output_flow.origin:
            Output_flow.origin = self
            self.output_flows.append(Output_flow)
        elif Output_flow not in self.output_flows:    
            self.output_flows.append(Output_flow)
        else:
            Output_flow = self
    
    
    def set_flow(self, flow_caracteristics):
        #This function allows the unit to do two things: either attach a stray flow
        #(no origin or destination) with
        #the required component(s) to itself and set its caracteristics to 
        #the list in flow_caracteristics; or create a new flow that is added to
        #the whole list of flows with the caracteristics in flow_caracteristics
        for flow in allflows:
            if flow_caracteristics['Components'] == flow.components and not flow.origin and not flow.destination:
                if 'Name' in flow_caracteristics: flow.name = flow_caracteristics['Name'] 
                if 'Flow rate' in flow_caracteristics: flow.flow_rate = flow_caracteristics['Flow rate'] 
                if 'Flow type' in flow_caracteristics: flow.flow_type = flow_caracteristics['Flow type'] 
                if 'Temperature' in flow_caracteristics: flow.temperature = flow_caracteristics['Temperature'] 
                if 'Composition' in flow_caracteristics: flow.composition = flow_caracteristics['Composition'] 
                if flow_caracteristics['In or out'] == 'In': flow.set_destination(self)
                if flow_caracteristics['In or out'] == 'Out': flow.set_origin(self)
                return
        
        New_flow = Flow(flow_caracteristics['Name'], flow_caracteristics['Components'], flow_caracteristics['Flow rate'], flow_caracteristics['Flow type'] )
        if 'Temperature' in flow_caracteristics: New_flow.temperature = flow_caracteristics['Temperature'] 
        if 'Composition' in flow_caracteristics: New_flow.composition = flow_caracteristics['Composition']
        allflows.append(New_flow)
        if flow_caracteristics['In or out'] == 'In': New_flow.set_destination(self)
        if flow_caracteristics['In or out'] == 'Out': New_flow.set_origin(self)



    def calc(self):
        #This function is the main one that is called when doing the program calculations.
        #It checks if one of the flows is the calc_flow, and then applies the calculations
        #present in the self.calculations to work out the different stream values
        #and then generate those streams and add them to the overall list
        #using set_flow
        for OutFlow in self.output_flows:
            if OutFlow.is_calc_flow:
                calculated_flows = self.calculations[OutFlow.components](OutFlow.flow_rate, self.coefficients)
                for flow in calculated_flows:
                    self.set_flow(flow)
                    
        for InFlow in self.input_flows:
            if InFlow.is_calc_flow: 
                calculated_flows = self.calculations[InFlow.components](InFlow.flow_rate, self.coefficients)
                for flow in calculated_flows:
                    self.set_flow(flow)

#Below is an example of a single unit being calculated with 4 flows in total
#We assume blood processing (meat packing unit 2), with an input of a 36 kg/hr blood input.
# The process uses 15.62 KJ/kg of blood to dry it and removes 75% of blood in the form of water.
Blood_in = Flow('Blood_in', 'Blood_in', 36 , 'input_flow', is_calc_flow= True)
allflows.append(Blood_in)


Processor = Unit('Processor')
Processor.expected_flows_in = ['Blood_in', 'Electricity']
Processor.expected_flows_out = ['Blood_out', 'Water']
Processor.coefficients = [0.75, 0.01562]
def processor_function_water(water_amount, coeff):
    blood_in_amount = water_amount/coeff[0]
    blood_out_amount = blood_in_amount - water_amount
    elec_amount = water_amount * coeff[1] #MJ/h
    return [{'Name' : 'Blood_in', 'Components' : 'Blood_in' , 
             'Flow rate' : blood_in_amount, 'Flow type': 'Input stream', 'In or out' : 'In'},
            {'Name' : 'Blood_out', 'Components' : 'Blood_out' , 
                     'Flow rate' : blood_out_amount, 'Flow type': 'Product', 'In or out' : 'Out'},
            {'Name' : 'Electricity', 'Components' : 'Electricity' , 
                     'Flow rate' : elec_amount, 'Flow type': 'Electricity', 'In or out' : 'In'}]

def processor_function_blood_out(blood_out_amount, coeff):
    blood_in_amount = blood_out_amount/(1-coeff[0])
    water_amount = blood_in_amount - blood_out_amount
    elec_amount = water_amount * coeff[1] #MJ/h
    return [{'Name' : 'Blood_in', 'Components' : 'Blood_in' , 
             'Flow rate' : blood_in_amount, 'Flow type': 'Input stream', 'In or out' : 'In'},
            {'Name' : 'Water', 'Components' : 'Water' , 
                     'Flow rate' : water_amount, 'Flow type': 'Waste stream', 'In or out' : 'Out'},
            {'Name' : 'Electricity', 'Components' : 'Electricity' , 
                     'Flow rate' : elec_amount, 'Flow type': 'Electricity', 'In or out' : 'In'}]


def processor_function_elec(elec_amount, coeff):
    water_amount = elec_amount/coeff[1]
    blood_in_amount = water_amount/coeff[0]
    blood_out_amount = blood_in_amount - water_amount
    return [{'Name' : 'Blood_in', 'Components' : 'Blood_in' , 
             'Flow rate' : blood_in_amount, 'Flow type': 'Input stream', 'In or out' : 'In'},
            {'Name' : 'Water', 'Components' : 'Water' , 
                     'Flow rate' : water_amount, 'Flow type': 'Waste stream', 'In or out' : 'Out'},
            {'Name' : 'Blood_out', 'Components' : 'Blood_out' , 
                     'Flow rate' : blood_out_amount, 'Flow type': 'Product', 'In or out' : 'Out'}]

def processor_function_blood_in(blood_in_amount, coeff):
    water_amount = blood_in_amount*coeff[0]
    elec_amount = water_amount*coeff[1] #MJ/hr
    blood_out_amount = blood_in_amount - water_amount
    return [{'Name' : 'Electricity', 'Components' : 'Electricity' , 
             'Flow rate' : elec_amount, 'Flow type': 'Electricity', 'In or out' : 'In'},
            {'Name' : 'Water', 'Components' : 'Water' , 
                     'Flow rate' : water_amount, 'Flow type': 'Waste stream', 'In or out' : 'Out'},
            {'Name' : 'Blood_out', 'Components' : 'Blood_out' , 
                     'Flow rate' : blood_out_amount, 'Flow type': 'Product', 'In or out' : 'Out'}]

Processor.calculations = {"Water" : processor_function_water,
              "Blood_out" : processor_function_blood_out,
              "Electricity" : processor_function_elec,
              "Blood_in" : processor_function_blood_in}
Processor.add_input(Blood_in)
Processor.calc()

for flow in allflows:
    print(flow.name)
    print(flow.flow_rate)
    
print(len(allflows))
