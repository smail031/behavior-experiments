import core
import os
import h5py

class ConfigFile():
    '''
    A class to handle a behavior rig's configuration file.

    Attributes:
    -----------
    self.hdf_file: object
        An h5py.File object for the corresponding configuration file.
    '''
    def __init__(self, hdf_file):
        self.hdf_file = hdf_file
        self.pins = {}
        self.tones = {}
        self.pumps = {}

        self.read_hdf_file()

    def read_hdf_file(self):
        '''
        Read current configuration file and use it to populate the dictionaries 
        for each component.
        '''
        components = ['pins', 'tones', 'pumps']
        attributes = [self.pins, self.tones, self.pumps]
        rig_name = self.hdf_file.attrs['rig_name']

        for comp in range(len(components)):
            component_group = self.hdf_file.require_group(components[comp])
            item_list = list(component_group.attrs.keys())
            for item in item_list:
                attributes[comp][item] = component_group.attrs[item]

    def add_item(self, component, name, value):
        '''
        
        '''

class GPIOPin():
    '''
    A class to handle a RPi GPIO pin.
    '''
    def __init__(self, name, pin_number):
        self.name = name
        self.pin_number = pin_number


    
