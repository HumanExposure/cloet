# CLOET
Command Line Occupational Exosure Tool

## Description
The High-throughput Command Line Occupational Exposure Tool (CLOET) is a
Python module for the dermal and inhalation occupational exposure models found
in EPA's Chemical Screening Tool for Exposures and Environmental Releases
(ChemSTEER), which is a graphical user interface (GUI) used to estimate
workplaceexposures and environmental releases for chemicals manufactured and
used in industrial/commercial settings.

Rather than relying on manual user input and interacting with the ChemSTEER GUI,
CLOET allows users to run the ChemSTEER dermal and inhalation exposure models
either directly from the Python command line or from within a Python script.
This allows multiple models with varying inputs to be run at once with options
for how to output and store model inputs and outputs.

## Requirements
Python 3.5+

## Installation
```
pip install cloet_ht
```

## Usage
```python
## Import the module
import cloet

## Run the default exposure scenario for the Automobile Spray Coating
## Inhalation exposure model
auto_spray = cloet.inhalation.automobile_spray_coating()

## Get the model run inputs
print(auto_spray.inputs)
{'ED': 1,
 'NWexp': 3,
 'NS': 1,
 'EY': 40,
 'BW': 70,
 'ATc': 70,
 'AT': 40,
 'KCk': 18.4,
 'b': 1.25,
 'h': 8}

## Get the model run outputs
print(auto_spray.outputs)
{'Cm': 18.4,
 'NW': 3,
 'LADD': 0.004115180318702823,
 'ADD': 0.007201565557729941,
 'APDR': 2.6285714285714286,
 'I': 184.0}

## Dump model inputs and output to file
cs.reports.file_report(model=auto_spray,file='autospray_coating_report.txt')
```

## Authors
* Katherine A. Phillips

## Acknowledgments
* Ashley Jackson
* Cody Addington
* Kristin Isaacs
* John Wambaugh

## License
GNU GPLv3
