#!/usr/bin/env
"""
Name:           cloet
Date Created:   06/22/2018
Late Updated:   11/03/2016
Author:         Katherine A. Phillps
Uses:           Python 3.5
Institute:      U.S. EPA / ORD / NERL / CED / HEDMB
Purpose:        Occupational exposure calculations performed within OPPT for new and
                existing chemicals are usually performed with the ChemSTEER program
                (https://www.epa.gov/tsca-screening-tools/chemsteer-chemical-screening-tool-exposures-and-environmental-releases).
                This program contains six models for dermal occupational exposure and
                eleven models for inhalation occupational exposure. However, only one
                dermal and one inhalation model can be evaluted at a time with the
                current program user interface.
                The Command Line Occupational Exposure Tool (CLOET) Python
                package uses equations, scenarios, and parameter defaults
                accquired from the ChemSTEER User Guide to recreate ChemSTEER
                models so that they can be used in a high-throughput manner to
                evaluate multiple combinations of models, parameters and
                chemicals.
"""
from . import checks
from . import exposures
from . import dermal
from . import inhalation
from . import reports
