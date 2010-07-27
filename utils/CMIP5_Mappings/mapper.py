"""
This maps CMIP5 experiments to storage machines in the CEDA pool.
"""

# The following table is based on Appendix 1.1 from the DRS spec (http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf)

shortnameMapping = {"10- or 30-year run initialized in year XXXX":"", ###############
"volcano-free hindcasts":"", ################
"prediction with 2010 volcano":"volcIn2010",
"chemistry-focused runs":"**", #####################
"pre-industrial control":"piControl",
"historical":"historical",
"mid-Holocene":"midHolocene",
"last glacial maximum":"lgm",
"last millennium":"past1000",
"RCP4.5":"rcp45",
"RCP8.5":"rcp85",
"RCP2.6":"rcp26",
"RCP6":"rcp60",
"ESM pre-industrial control":"esmControl",
"ESM historical":"esmHistorical",
"Emission-driven historical":"esmHistorical", ## Not in Appendix 1.1
"ESM RCP8.5":"esmrcp85",
"emission-driven RCP8.5":"esmrcp85", ## Not in Appendix 1.1
"ESM fixed climate 1":"esmFixClim1",
"ESM fixed climate 2":"esmFixClim2",
"ESM feedback 1":"esmFdbk1",
"ESM feedback 2":"esmFdbk2",
"1 percent per year CO2":"1pctCO2",
"abrupt 4XCO2":"abrupt4xCO2",
"natural-only":"historicalNat",
"GHG-only":"historicalGHG",
"other-only":"historical?**",    #################
"AMIP":"amip",
"2030 time-slice":"sst2030",
"control SST climatology":"sstClim",
"CO2 forcing":"sstClim4xCO2",
"all aerosol forcing":"sstClimAerosol",
"sulfate aerosol forcing":"sstClimSulfate",
"4xCO2 AMIP":"amip4xCO2",
"AMIP plus patterned anomaly":"amipFuture",
"aqua planet control":"aquaControl",
"aqua planet: control run":"aquaControl", ## Not in Appendix 1.1
"4xCO2 aqua planet":"aqua4xCO2",
"aqua planet: cloud response to imposed 4xCO2":"aqua4xCO2", ## Not in Appendix 1.1
"aqua planet plus 4K anomaly":"aqua4K",
"AMIP plus 4K anomaly":"amip4K"}


# Read in the models/experiments together with volume estimates from the the CSV file

import csv
exptReader = csv.reader(open('volume_by_expt.csv'), delimiter=',')

for row in exptReader:
    matchFound = False
    for i in shortnameMapping.keys():
        if i == row[1]:
            matchFound = True
            break
        else:
            continue
    if not matchFound:
        print "Match not found : %s" % row[1]


# Obtain the list of storage volumes in the CEDA pool that are currently allocated to CMIP5 


# Perform the allocation of experiments to storage volumes in the pool


# Write allocation out to a config file


# Setup directories and symlinks to perform the above allocation

