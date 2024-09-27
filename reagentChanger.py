import xml.etree.ElementTree as ET
import sys
from random import randint
from math import floor
import json
# import pdb; pdb.set_trace()

instrumentStateFile = sys.argv[1] + '\\InstrumentState.xml'
drawers = {'left': 0, 'right': 1}
reagentNames = ['A', 'C', 'T', 'G', 'A-', 'C-', 'T-', 'G-', 'Wash', 'Cleave', 'MiniWash']

# Load config.json data into a dictionary
def loadData() -> dict:
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


# Parse through InstrumentState, look for target reagent, update data
def parseInstrumentState(reagentName, reagentData, reagentDrawer):
    try:
        tree = ET.parse(instrumentStateFile)
        root = tree.getroot()
        reagentCfgElem = root.find('Reagents')[reagentDrawer]  # Get the left or right ReagentCfg element
        for reagent in reagentCfgElem.findall('Reagent'):  # Iterate through all 'Reagent' elements
            if reagent.attrib['Volumes'].startswith(reagentName):  # Once find 'Wash' reagent, update data
                reagent.attrib['Volumes'] = reagentData
                break
        else:
            print("No reagent with Volumes found.")
        tree.write(instrumentStateFile)
        print("Changes saved to the XML file.")
        return

    except ET.ParseError:
        print("Error parsing the XML file. Please check the file format.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Calculate new wash header volumes based on percent input
def calculateNewVolume(reagentName, percent) -> dict:
    volumeList = {'initial': 0.0000, 'usable': 0.0000, 'used': 0.0000, 'past': 0.0000, 'current': 0.0000,
                  'available': 0.0000, 'reserved': 0.0000}

    reagentInitial = 'initial' + reagentName
    reagentUsable = 'usable' + reagentName
    reagentDecimalValue = stripDecimal(data[reagentUsable])

    volumeList['initial'], volumeList['usable'] = data[reagentInitial], data[reagentUsable]
    volumeList['available'] = floor(volumeList['usable'] * (percent/100))
    volumeList['used'] = (volumeList['usable'] - volumeList['available']) + reagentDecimalValue
    volumeList['past'] = volumeList['used']
    volumeList['usable'] = volumeList['usable'] + reagentDecimalValue
    return volumeList


# Return the first four decimal digits of the float value as a string prefixed by '0.'
def stripDecimal(value) -> float:
    decimal_part = str(value).split('.')[-1]  # Get the decimal part
    four_digits = decimal_part[:4]  # Get the first four digits
    return float(f"0.{four_digits}")  # Format it as '0.xxxx'


# create new reagent data string based on new volume calculations
def generateNewWashHeader(reagent, volumeList) -> str:
    for volumeHeader in volumeList:  # Iterate through all headers in volume list
        volumeList[volumeHeader] = f"{volumeList[volumeHeader]:.4f}"  # Ensure header has 4 decimal digits
        volumeList[volumeHeader] = str(volumeList[volumeHeader])
        while len(volumeList[volumeHeader]) < 9:  # Set spacing between each value correctly
            volumeList[volumeHeader] = ' ' + volumeList[volumeHeader]

    reagentName = reagent
    if reagentName in ['A', 'C', 'G', 'T']:
        reagentName += ' ' * 10
    elif reagentName in ['A-', 'C-', 'G-']:
        reagentName += ' ' * 9
    elif reagentName == 'T-':
        reagentName += ' ' * 9
    elif reagentName == 'Wash':
        reagentName += ' ' * 7
    elif reagentName == 'Cleave':
        reagentName += ' ' * 5
    elif reagentName == 'MiniWash':
        reagentName += ' ' * 3

    return (f"{reagentName}"
            f"{volumeList['initial']}   {volumeList['usable']}   {volumeList['used']}   "
            f"{volumeList['past']}   {volumeList['current']}   {volumeList['available']}   "
            f"{volumeList['reserved']}")


data = loadData()

for drawer in drawers:
    percent = -1
    if data["randomPercent"]:
        percent = randint(0, 100)
    else:
        while not (percent.is_integer() and 0 <= percent <= 100):
            percent = int(input(f'Enter {drawer} reagent volume percent, as an integer (0-100)\n'))
    for reagentName in reagentNames:
        volumeList = calculateNewVolume(reagentName, percent)
        reagentString = generateNewWashHeader(reagentName, volumeList)
        parseInstrumentState(reagentName, reagentString, drawers[drawer])
