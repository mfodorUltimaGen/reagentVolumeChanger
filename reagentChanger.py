import xml.etree.ElementTree as ET
import sys
from random import randint
from math import floor
import json
#import pdb; pdb.set_trace()


tool_type = 'U'
instrument_state_file = sys.argv[1] + '\\InstrumentState.xml'
#instrument_state_file = 'C:\\Projects\\Pegasus_3.0_QA\\State\\InstrumentState.xml'


drawers = {'Left': 0, 'Right': 1}
reagent_names = ['A', 'C', 'T', 'G', 'A-', 'C-', 'T-', 'G-', 'Wash', 'Cleave', 'MiniWash']

if tool_type == 'U':
    reagent_names += ['Scan', 'TTM']


# Load config.json data into a dictionary
def load_config_data(tool_type) -> dict:
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
            config = config[tool_type]
        return config
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


# Parse through InstrumentState, look for target reagent, update data
def parse_instrument_state(reagent_name, reagent_data, reagent_drawer):
    try:
        tree = ET.parse(instrument_state_file)
        root = tree.getroot()
        reagent_cfg_elem = root.find('Reagents')[reagent_drawer]  # Get the left or right ReagentCfg element
        for reagent in reagent_cfg_elem.findall('Reagent'):  # Iterate through all 'Reagent' elements
            if reagent.attrib['Volumes'].startswith(reagent_name):  # Once find 'Wash' reagent, update data
                reagent.attrib['Volumes'] = reagent_data
                break
        else:
            print(f"No reagent with Volumes found for {reagent_name}.")
        tree.write(instrument_state_file)
        return

    except ET.ParseError:
        print("Error parsing the XML file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Calculate new wash header volumes based on percent input
def calculate_new_volume(reagent_name, percent) -> dict:
    volume_list = {'initial': 0.0000, 'usable': 0.0000, 'used': 0.0000, 'past': 0.0000, 'current': 0.0000,
                  'available': 0.0000, 'reserved': 0.0000}

    reagent_initial = 'initial' + reagent_name
    reagent_usable = 'usable' + reagent_name
    reagent_decimal_value = strip_decimal(data[reagent_usable])

    volume_list['initial'], volume_list['usable'] = data[reagent_initial], data[reagent_usable]
    volume_list['available'] = floor(volume_list['usable'] * (percent/100))
    volume_list['used'] = (volume_list['usable'] - volume_list['available']) + reagent_decimal_value
    volume_list['past'] = volume_list['used']
    volume_list['usable'] = volume_list['usable'] + reagent_decimal_value
    return volume_list


# Return the first four decimal digits of the float value as a string prefixed by '0.'
def strip_decimal(value) -> float:
    decimal_part = str(value).split('.')[-1]  # Get the decimal part
    four_digits = decimal_part[:4]  # Get the first four digits
    return float(f"0.{four_digits}")  # Format it as '0.xxxx'


# Return number of whole digits
def count_whole_digits(s):
    integer_part = s.split('.')[0]
    return sum(c.isdigit() for c in integer_part)


# create new reagent data string based on new volume calculations
def generate_new_wash_header(reagent_name, volume_list) -> str:
    for volume_header in volume_list:  # Iterate through all headers in volume list
        volume_list[volume_header] = f"{volume_list[volume_header]:.4f}"  # Ensure header has 4 decimal digits
        volume_list[volume_header] = str(volume_list[volume_header])
        while len(volume_list[volume_header]) < 9 and volume_header != 'initial':  # Set spacing between each value correctly, except space between reagent name and initial
            volume_list[volume_header] = ' ' + volume_list[volume_header]
    digits = count_whole_digits(volume_list['initial'])-3  # Set spacing between reagent name and initial
    while len(reagent_name) + digits < 12:
        reagent_name += ' '

    return (f"{reagent_name}"
            f"{volume_list['initial']}   {volume_list['usable']}   {volume_list['used']}   "
            f"{volume_list['past']}   {volume_list['current']}   {volume_list['available']}   "
            f"{volume_list['reserved']}")


data = load_config_data(tool_type)
print('Assuming tool type U\n')

for drawer in drawers:
    percent = -1
    # If config.json has randomization enabled
    if data["randomPercent"]:
        percent = randint(0, 100)
    else:
        # Get user input
        percent = int(input(f'Enter required *{drawer} Reagent* volume percent remaining, as an integer (0-100)\n'))
        if percent < 0 or percent > 100:
            continue
    # For each reagent, update the values for this specific drawer
    for reagent_name in reagent_names:
        volume_list = calculate_new_volume(reagent_name, percent)
        reagentString = generate_new_wash_header(reagent_name, volume_list)
        parse_instrument_state(reagent_name, reagentString, drawers[drawer])

    print(f"{drawer} Reagent Drawer changes saved to {instrument_state_file}.\n\n")
