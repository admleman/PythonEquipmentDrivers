import pyvisa
from pyvisa import VisaIOError
from . import errors
from importlib import import_module
import json
from pathlib import Path
from typing import List, Tuple, Union


# Globals
rm = pyvisa.ResourceManager()


# Utility Functions
def get_devices_addresses() -> Tuple[str]:
    """
    returns a list of the addresses of peripherals connected to the computer
    """
    return rm.list_resources()


def identify_devices(verbose: bool = False) -> List[Tuple[str]]:
    """
    identify_connections(verbose=False)

    Queries devices connected to the machine for with and IDN query, return
    those with a valid response response. The IDN query is a IEEE 488.2 Common
    Command and should be supported by all SCPI compatible instruments.

    Args:
        verbose (bool, optional): if True device addresses and responses, or,
            lack thereof are printed to stdout as they are queried. Defaults to
            False.

    Returns:
        List[Tuple[str]]: A list of tuples containing address, IDN response
            pairs for each detected device that responded to the query with a
            valid response.
    """

    scpi_devices = []
    for address in rm.list_resources():
        try:
            device = Scpi_Instrument(address)
            scpi_devices.append((address, device.idn))
            if verbose:
                print("address: {}\nresponse: {}\n".format(*scpi_devices[-1]))

        except pyvisa.Error:
            if verbose:
                print(f"Invalid IDN query reponse from address {address}\n")
        finally:
            del(device)

    return scpi_devices


class Scpi_Instrument():

    def __init__(self, address, **kwargs) -> None:
        self.address = address
        self.instrument = rm.open_resource(self.address,
                                           open_timeout=1000)
        self.timeout = int(kwargs.get('timeout', 1000))  # ms

    @property
    def idn(self) -> str:
        """
        idn

        Identify Query

        Returns a string that uniquely identifies the instrument. The IDN query
        sent to the instrument is one of the IEEE 488.2 Common Commands and
        should be supported by all SCPI compatible instruments.

        Returns:
            str: uniquely identifies the instrument
        """

        return self.instrument.query('*IDN?')

    def cls(self, **kwargs) -> None:
        """
        cls(**kwargs)

        Clear Status Command

        Clears the instrument status byte by emptying the error queue and
        clearing all event registers. Also cancels any preceding *OPC command
        or query. The CLS command sent to the instrument is one of the
        IEEE 488.2 Common Commands and should be supported by all SCPI
        compatible instruments.

        Returns:
            None
        """

        self.instrument.write('*CLS', **kwargs)

    def rst(self, **kwargs) -> None:
        """
        rst()

        Reset Command

        Executes a device reset and cancels any pending *OPC command or query.
        The RST command sent to the instrument is one of the IEEE 488.2 Common
        Commands and should be supported by all SCPI compatible instruments.
        """

        self.instrument.write('*RST', **kwargs)

    @property
    def timeout(self) -> int:
        return self.instrument.timeout

    @timeout.setter
    def timeout(self, timeout: int) -> None:
        self.instrument.timeout = int(timeout)  # ms

    def __del__(self) -> None:
        try:
            # if connection has been estabilished terminate it
            if hasattr(self, 'instrument'):
                self.instrument.close()
        except VisaIOError:
            # if connection not connection has been estabilished (such as if an
            # error is throw in __init__) do nothing
            pass

    def __repr__(self) -> str:

        def_str = f"{self.__class__.__name__}"
        def_str += f"({self.address}, timeout={self.timeout})"

        return def_str

    def __str__(self) -> str:
        return f'Instrument ID: {self.idn}\nAddress: {self.address}'

    def __eq__(self, obj) -> bool:

        """
        __eq__(obj)

        Args:
            obj (object): object to compare

        Returns:
            bool: True if the objects are both instances of Scpi_Instrument
                (or any class that inherits from Scpi_Instrument) and have the
                same address and class name. Otherwise False.
        """

        if not isinstance(obj, Scpi_Instrument):
            return False

        if not (self.__class__.__name__ == obj.__class__.__name__):
            return False

        if not (self.address == obj.address):
            return False
        return True

    def __ne__(self, obj) -> bool:
        """
        __ne__(obj)

        Args:
            obj (object): object to compare

        Returns:
            bool: whether or not to object are not equal. Defined as the
                inverse of the result from __eq__
        """

        return not self.__eq__(obj)

    def send_raw_scpi(self, command_str: str, **kwargs) -> None:
        """
        send_raw_scpi(command_str, **kwargs)

        Pass-through function which forwards the contents of 'command_str' to
        the device. This function is intended to be used for API calls for
        functionally that is not currently supported. Can only be used for
        commands, will not return queries.

        Args:
            command_str: string, scpi command to be passed through to the
                device.
        """

        self.instrument.write(str(command_str), **kwargs)

    def query_raw_scpi(self, query_str: str, **kwargs) -> str:
        """
        query_raw_scpi(query, **kwargs)

        Pass-through function which forwards the contents of 'query_str' to
        the device, returning the response without any processing. This
        function is intended to be used for API calls for functionally that is
        not currently supported. Only to be used for queries.

        Args:
            query_str: string, scpi query to be passed through to the device.

        """

        return self.instrument.query(str(query_str), **kwargs)

    def read_raw_scpi(self, **kwargs) -> str:
        """
        read_raw_scpi(**kwargs)

        Pass-through function which reads the device, returning the response
        without any processing. This function is intended to be used for API
        calls for functionally that is not currently supported.
        Only to be used for read.
        """

        return self.instrument.read(**kwargs)


class EnvironmentSetup():
    """
    Class for handling the instantiation of generic sets of test equipment
    based on addressing data from file. Can blindly connect to all equipment in
    the provided file or dictionary (equipment_setup) and can optionally verify
    that a specific set of equipment is in file (based on object_mask)

    # Add expected/assumed format of json file
    Expected JSON file format

    "device_name_1": {
                      "object": "Class_Name_1",
                      "definition": "Object_Definition_1",
                      "address": "Device_Address_1"
                      },
    "device_name_2": {
                      "object": "Class_Name_2",
                      "definition": "Object_Definition_2",
                      "address": "Device_Address_2"
                      },
        .
        .
        .

    "device_name_n": {
                      "object": "Class_Name_n",
                      "definition": "Object_Definition_n",
                      "address": "Device_Address_n"
                      }

    The "device_name" of each dictionary represents the name of the instance
    of class "object" to be connected to at address "address". The location to
    the definition of the class "object" needs to be provided using the key
    "definition". An example of this is shown below:

    "source_v_in": {
                    "object": "Chroma_62012P",
                    "definition": "pythonequipmentdrivers.source",
                    "address": "USB0::0x1698::0x0837::002000000655::INSTR",
                    "kwargs": {}
                    },

    If this device is connected and availible this will create an instance of
    the Chroma_62012P at the provided address. The source is defined in the
    pythonequipmentdrivers.source sub-module. This instance can be accessed
    using EnvironmentSetup('path_to_json file'). i.e. self.source_v_in
    There is an optional argument for each device "kwargs", if present the
    arugements contained in kwargs will be passed as keyword arguements in the
    instantation of the device, if not needed this can be omitted.

    The "object_mask" arguement can be used to connect to a sub-set of devices
    described in the JSON file. If used, object_mask should be an iterable
    containing the names of the devices in the JSON file that are desired.
    If all names contained in object_mask are not present in the JSON file an
    exception will be raised. Otherwise, this object will connect exculsively
    to the devices specified in object_mask.

    If init_ is True than this object will search the JSON file for an
    array named "init" which defines a sequence of commands to initialize the
    device. For example:

    "source_v_in": {
                    "object": "Chroma_62012P",
                    "definition": "pythonequipmentdrivers.source",
                    "address": "USB0::0x1698::0x0837::002000000655::INSTR"
                    "init": [
                             ["set_voltage", {"voltage": 0}],
                             ["off", {}],
                             ]
                    },

    In this example, If init is True and the device was successfully
    connected, this object will successively iterate through the array of
    command, arguement pairs; calling the commands listed using arguements (if
    any) provided. The commands listed must be valid methods of the device
    object, all arguements used will be passed as keyword arguements and
    therefore need to be named.
    """

    def __init__(self, equipment_setup, init: bool = False, **kwargs) -> None:

        self.read_configuration(equipment_setup)

        self.object_mask = set(kwargs.get('object_mask', []))
        self.check_mask()

        self.connect_to_devices(init=init, verbose=kwargs.get('verbose', True))

    def check_mask(self) -> None:
        """
        check_mask()

        Checks that the devices required by self.object_mask are present within
        the configuration information.
        """

        if not self.object_mask:  # mo mask
            return None

        common = set.intersection(set(self.configuration.keys()),
                                  self.object_mask)

        if common != self.object_mask:
            raise ValueError("Required Equipment Missing",
                             self.object_mask.difference(common))

    def read_configuration(self, device_setup: Union[str, Path, dict]) -> None:
        """
        read_configuration(equipment_setup)

        Reads configuration information and stores it as the instance variable
        "configuration".

        Args:
            device_setup (str, Path, dict): Configuration information for the
                devices to connect to. Information can either be passed
                directly (dict) or can read from a file (str or Path-like).
        """

        if not isinstance(device_setup, (str, Path, dict)):
            raise ValueError('Unsupported type for arguement "equipment_setup"'
                             ' should a str/Path object to a JSON file or a'
                             ' dictionary')

        if isinstance(device_setup, dict):
            self.configuration = device_setup
            return None

        # read equipment info from file
        with open(device_setup, 'rb') as file:
            self.configuration = json.load(file)

    def connect_to_devices(self, **kwargs) -> None:
        """
        Establishs connections to the equipment specified in equipment_json
        """

        if self.object_mask:  # remove items not in mask
            for device in set(self.configuration).difference(self.object_mask):
                self.configuration.pop(device)

        for name, info in self.configuration.items():

            try:
                # get object to instantate from config file
                Module = import_module(info['definition'])
                Class = getattr(Module, info['object'])

                # get any kwargs for instantiation
                obj_kwargs = info.get('kwargs', {})

                # create an instance of the Class 'info["object"]' named 'name'
                vars(self)[name] = Class(info['address'], **obj_kwargs)

                if kwargs.get('verbose', True):
                    print(f'[CONNECTED] {name}')

                if kwargs.get('init', False) and ('init' in info):
                    # get the instance in question
                    inst = getattr(self, name)
                    self.initiaize_device(inst, info['init'])
                    if kwargs.get('verbose', True):
                        print('\tInitialzed')

            except (VisaIOError, ConnectionError) as error:

                if kwargs.get('verbose', True):
                    print(f'[FAILED CONNECTION] {name}')

                # if the failed connection is for a piece of required
                # equipment connecting devices
                if self.object_mask:
                    raise errors.ResourceConnectionError(error)

            except (ModuleNotFoundError, AttributeError) as error:

                if kwargs.get('verbose', True):
                    print(f'[UNSUPPORTED DEVICE] {name}\t{error}')

                if self.object_mask:
                    raise errors.UnsupportedResourceError(error)

    @staticmethod
    def _get_callable_methods(instance) -> Tuple:
        """
        _get_callable_methods(instance)

        Returns a tuple of all callable methods of an object or instance that
        are not "dunder"/"magic"/"private" methods

        Args:
            instance (object): object or instance of an object to get the
                callable methods of.

        Returns:
            tuple: collection of callable methods.
        """

        # get methods that are callable (will not include sub-classes)
        methods = instance.__dir__()
        cmds = filter(lambda method: (callable(getattr(instance, method))),
                      methods)

        # filter out ignore dunders
        cmds = filter(lambda func_name: ('__' not in func_name), cmds)
        return tuple(cmds)

    def initiaize_device(self, instance, sequence) -> None:
        """
        initiaize_device(inst, sequence)

        Here "inst" has the two methods "set_voltage", and "off". The first of
        which requires the arguement voltage and the second of which has no
        args.
        Args:
            instance (object): object instance to initialize

            sequence (list): list of lists containing valid
                methods of "inst" with a dict of arguements to pass as kwargs.

                                Will run in the order given
        ex: sequence = [
                        ["set_voltage", {"voltage": 0}],
                        ["off", {}],
                    ]
        """

        valid_cmds = self._get_callable_methods(instance)
        error_msg = '\tError with initialization command {}:\t{}'

        for method_name, method_kwargs in sequence:
            if method_name in valid_cmds:
                try:
                    func = getattr(instance, method_name)
                    func(**method_kwargs)

                except TypeError as error:  # invalid kwargs
                    print(error_msg.format(method_name, error))


if __name__ == "__main__":
    pass
