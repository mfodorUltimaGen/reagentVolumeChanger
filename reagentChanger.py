import xml.etree.ElementTree as ET
import sys
from math import floor
import json
#import pdb; pdb.set_trace()


tool_name = 'U-Tool'
instrument_state_file = sys.argv[1] + '\\InstrumentState.xml'
# instrument_state_file = 'C:\\Projects\\Pegasus_3.0_QA\\State\\InstrumentState.xml'


def run_program() -> None:
    for drawer_name, drawer_index in tool_config['ReagentDrawers'].items():

        new_percent = int(input(f'Enter required *{drawer_name} Reagent* volume percent remaining, as an integer (0-100)\n'))
        if new_percent < 0 or new_percent > 100:
            print(f"{drawer_name} Reagent drawer skipped.\n")
            continue

        updated_reagents = generate_updated_reagents_dict(new_percent)
        update_instrument_state(updated_reagents, drawer_index)

        print(f"{drawer_name} Reagent drawer changes saved to {instrument_state_file}.\n")


# Load config.json data into a dictionary
def load_config_data() -> dict:
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


# Create a dict of reagents names with their updated data row strings
def generate_updated_reagents_dict(new_percent: int) -> dict:
    updated_reagent = {}
    for reagent_name, reagent_data in tool_config[tool_name].items():
        new_volume = calculate_new_volume(reagent_data, new_percent)
        reagent_string = format_reagent_element_row(reagent_name, new_volume)
        updated_reagent[reagent_name] = reagent_string
    return updated_reagent


# Calculate volumes based on desired percent remaining
def calculate_new_volume(reagent_data: dict, percent: int) -> dict:
    volume_dict = {'initial': 0.0000, 'usable': 0.0000, 'used': 0.0000, 'past': 0.0000, 'current': 0.0000,
                   'available': 0.0000, 'reserved': 0.0000}

    reagent_decimal_value = strip_decimal(reagent_data['usable'])

    volume_dict['initial'], volume_dict['usable'] = reagent_data['initial'], reagent_data['usable']
    volume_dict['available'] = floor(volume_dict['usable'] * (percent/100))
    volume_dict['used'] = (volume_dict['usable'] - volume_dict['available']) + reagent_decimal_value
    volume_dict['past'] = volume_dict['used']
    volume_dict['usable'] = volume_dict['usable'] + reagent_decimal_value
    return volume_dict


# Format calculations into a single row string
def format_reagent_element_row(reagent_name: str, volume_dict: dict) -> str:
    # Iterate through all headers in volume list
    for volume_header in volume_dict:
        # Ensure header has 4 decimal digits
        volume_dict[volume_header] = f"{volume_dict[volume_header]:.4f}"

        # Set spacing between each value correctly, except space between reagent name and initial
        while len(volume_dict[volume_header]) < 9 and volume_header != 'initial':
            volume_dict[volume_header] = ' ' + volume_dict[volume_header]

    # Set spacing between reagent name and initial
    digits = count_whole_digits(volume_dict['initial'])-3
    while len(reagent_name) + digits < 12:
        reagent_name += ' '

    final_string = (f"{reagent_name}"
                    f"{volume_dict['initial']}   {volume_dict['usable']}   {volume_dict['used']}   "
                    f"{volume_dict['past']}   {volume_dict['current']}   {volume_dict['available']}   "
                    f"{volume_dict['reserved']}")
    return final_string


# Update instrument state with generated dict
def update_instrument_state(updated_reagents: dict, drawer_index: int) -> None:
    try:
        tree = ET.parse(instrument_state_file)
        root = tree.getroot()
        reagents_section = root.find('Reagents')[drawer_index]  # Get the left or right Reagents parent section
        for reagent_name, reagent_data in updated_reagents.items():
            for reagent_elem in reagents_section.findall('Reagent'):  # Iterate through all 'Reagent' elements
                if reagent_elem.attrib['Volumes'].startswith(reagent_name):  # Once find the reagent, update data
                    reagent_elem.attrib['Volumes'] = reagent_data
                    break
        tree.write(instrument_state_file)
        return

    except ET.ParseError:
        print("Error parsing the XML file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Return the first four decimal digits of the float value as a string prefixed by '0.'
def strip_decimal(value: float) -> float:
    decimal_part = str(value).split('.')[-1]  # Get the decimal part
    four_digits = decimal_part[:4]  # Get the first four digits
    return float(f"0.{four_digits}")  # Format it as '0.xxxx'


# Return number of whole digits
def count_whole_digits(s: str) -> int:
    integer_part = s.split('.')[0]
    return sum(c.isdigit() for c in integer_part)


tool_config = load_config_data()
print(f'Assuming {tool_name}\n')
run_program()
