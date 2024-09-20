import xml.etree.ElementTree as ET
from random import randint
from math import floor
import json

instrumentStateFile = 'C:\\Projects\\State\\InstrumentState.xml'
reagents = {'left': 0, 'right': 1}

# Load config.json data into a dictionary
def loadData() -> dict:
    try:
        with open("config.json", 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


# Parse through InstrumentState, look for Wash reagent, update data
def parseInstrumentState(washString, reagentIndex):
    try:
        tree = ET.parse(instrumentStateFile)
        root = tree.getroot()
        reagentCfgElem = root.find('Reagents')[reagentIndex]  # Get the left or right ReagentCfg element
        for reagent in reagentCfgElem.findall('Reagent'):  # Iterate through all 'Reagent' elements
            if reagent.attrib['Volumes'].startswith("Wash"):  # Once find 'Wash' reagent, update data
                reagent.attrib['Volumes'] = washString
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
def calculateNewVolume(percent) -> dict:
    volumeList = {'initial': 0.0000, 'usable': 0.0000, 'used': 0.0000, 'past': 0.0000, 'current': 0.0000,
                  'available': 0.0000, 'reserved': 0.0000}
    volumeList['initial'], volumeList['usable'] = data['initialWash'], data['usableWash']
    volumeList['available'] = floor(volumeList['usable'] * (percent/100))
    volumeList['used'] = (volumeList['usable'] - volumeList['available']) + data['washDecimal']
    volumeList['past'] = volumeList['used']
    volumeList['usable'] = volumeList['usable'] + 0.7903
    return volumeList


# create new wash header string based on new volume calculations
def generateNewWashHeader(volumeList) -> str:
    for volumeHeader in volumeList:  # Iterate through all headers in volume list
        volumeList[volumeHeader] = f"{volumeList[volumeHeader]:.4f}"  # Ensure header has 4 decimal digits
        volumeList[volumeHeader] = str(volumeList[volumeHeader])
        while len(volumeList[volumeHeader]) < 9:  # Set spacing between each value correctly
            volumeList[volumeHeader] = ' ' + volumeList[volumeHeader]

    return (f"Wash       "
            f"{volumeList['initial']}   {volumeList['usable']}   {volumeList['used']}   "
            f"{volumeList['past']}   {volumeList['current']}   {volumeList['available']}   "
            f"{volumeList['reserved']}")


data = loadData()
for reagent in reagents:
    if data["randomPercent"]:
        percent = randint(0, 100)
    else:
        percent = int(input(f'Enter {reagent} reagent volume percent, as an integer (0-100)'))
    volumeList = calculateNewVolume(percent)
    washString = generateNewWashHeader(volumeList)
    parseInstrumentState(washString, reagents[reagent])
