from pysolarmanv5 import PySolarmanV5
from deye_controller.utils import group_registers, map_response, RegistersGroup
from deye_controller.modbus.protocol import HoldingRegisters
from constants import ip, serial_number
from typing import List
from types import MappingProxyType


def get_registers(selection, excluded_selection):
    if len(selection) > 0:
        registers = MappingProxyType({attr: getattr(HoldingRegisters, attr) for attr in selection})
    else:
        registers = MappingProxyType(vars(HoldingRegisters))

    return [
        key for key, value in registers.items()
        if hasattr(value, 'address') and not isinstance(value, (list, dict, set)) and key not in excluded_selection
    ]


def read_groups(modbus: PySolarmanV5, groups: List[RegistersGroup]):
    result = {}
    for group in groups:
        if hasattr(group, 'start_address') and hasattr(group, 'len'):
            res = modbus.read_holding_registers(group.start_address, group.len)
            map_response(res, group)
            for reg in group:
                if hasattr(reg, 'description') and hasattr(reg, 'format'):
                    value = reg.format()
                    if isinstance(value, (int, float, str)):
                        result[reg.description.title()] = value
                        print(f"PASSED! {reg.description.title()}: {value} {getattr(reg, 'suffix', '')}")
                    else:
                        print(f"SKIPPED! {reg.description.title()}: {value} {getattr(reg, 'suffix', '')}")
        else:
            print(f"Invalid group: {group}")

    print(f"\n\nREAD_GROUPS_RESULT: {result}\n\n")
    return result


def read_data(selection, excluded_selection):
    selection = get_registers(selection, excluded_selection)
    
    if not selection:
        print("No valid registers found.")
        return {}

    regs = [getattr(HoldingRegisters, attr) for attr in selection]
    if not regs:
        print("No registers to read.")
        return {}

    groups = group_registers(regs)
    if not groups:
        print("No groups created from registers.")
        return {}
    
    if not ip or not serial_number:
        print("Ip or serial number were not provided.")
        return {}
    
    modbus = PySolarmanV5(ip, serial_number)
    return read_groups(modbus, groups)


metadata_selection = [
    'DeviceType', 'CommProtocol', 'CommAddress', 'BatteryControl', 
    'BattCapacity', 'BattEqualization', 'BattAbsorbtion', 'BattFloat', 
    'BattShutDownCapacity', 'BattRestartCapacity', 'BattLowCapacity', 
    'BattShutDownVoltage', 'BattRestartVoltage', 'GridFrequency', 
    'MaxAmpCharge'
]

def get_timestamp():
    return read_data([], metadata_selection)


def get_metadata():
    return read_data(metadata_selection, [])
