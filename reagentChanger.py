import xml.etree.ElementTree as ET
import sys
from random import randint
from math import floor
import json
# import pdb; pdb.set_trace()

instrumentStateFile = sys.argv[1] + '\\InstrumentState.xml'
# instrumentStateFile = 'C:\\Projects\\State\\InstrumentState.xml'

drawers = {'Left': 0, 'Right': 1}
reagentNames = ['A', 'C', 'T', 'G', 'A-', 'C-', 'T-', 'G-', 'Wash', 'Cleave', 'MiniWash']

# Load config.json data into a dictionary
def loadConfigData() -> dict:
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
            print(f"No reagent with Volumes found for {reagentName}.")
        tree.write(instrumentStateFile)
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


# Return number of whole digits
def countWholeDigits(s):
    integer_part = s.split('.')[0]
    return sum(c.isdigit() for c in integer_part)


# create new reagent data string based on new volume calculations
def generateNewWashHeader(reagentName, volumeList) -> str:
    for volumeHeader in volumeList:  # Iterate through all headers in volume list
        volumeList[volumeHeader] = f"{volumeList[volumeHeader]:.4f}"  # Ensure header has 4 decimal digits
        volumeList[volumeHeader] = str(volumeList[volumeHeader])
        while len(volumeList[volumeHeader]) < 9 and volumeHeader != 'initial':  # Set spacing between each value correctly, except space between reagent name and initial
            volumeList[volumeHeader] = ' ' + volumeList[volumeHeader]
    digits = countWholeDigits(volumeList['initial'])-3  # Set spacing between reagent name and initial
    while len(reagentName) + digits < 12:
        reagentName += ' '

    return (f"{reagentName}"
            f"{volumeList['initial']}   {volumeList['usable']}   {volumeList['used']}   "
            f"{volumeList['past']}   {volumeList['current']}   {volumeList['available']}   "
            f"{volumeList['reserved']}")


data = loadConfigData()
for drawer in drawers:
    percent = -1
    if data["randomPercent"]:
        percent = randint(0, 100)
    else:
        percent = int(input(f'Enter required *{drawer} Reagent* volume percent, as an integer (0-100)\n'))
    for reagentName in reagentNames:
        volumeList = calculateNewVolume(reagentName, percent)
        reagentString = generateNewWashHeader(reagentName, volumeList)
        parseInstrumentState(reagentName, reagentString, drawers[drawer])
    print(f"{drawer} Reagent Drawer changes saved to {instrumentStateFile}.\n\n")
