# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 03
# Written in Python 3

import prettytable, sys

TAGS = {
    "INDI": "0", "NAME": "1", "SEX": "1",
    "BIRT": "1", "DEAT": "1", "FAMC": "1",
    "FAMS": "1", "FAM": "0", "MARR": "1",
    "HUSB": "1", "WIFE": "1", "CHIL": "1",
    "DIV": "1", "DATE": "2", "HEAD": "0",
    "TRLR": "0", "NOTE": "0"
}
TAG_FILTER = ["NAME", "SEX", "BIRT", "DEAT", "DATE", "MARR", "DIV", "HUSB", "WIFE", "CHIL"]
DATE_TAGS = ["BIRT", "DEAT", "MARR", "DIV"]

# Setup individual and family collections
INDI = {}
FAM = {}
# buffer to hold current tags
current = None
date_for = None

try:
    f = open("example.ged")
except:
    print("Error reading input file")
    sys.exit(1)


for line in f:

    # parse the line
    parsed = line.split()

    # ignore bad lines
    if len(parsed) < 2:
        continue

    # catch special cases
    if len(parsed) is 3 and parsed[2] in ["INDI", "FAM"]:
        tag = parsed[2].upper()
        arguments = parsed[1]

        # add information to collections
        if current:
            if current.get("INDI"):
                INDI[current.get("INDI")] = current
            elif current.get("FAM"):
                FAM[current.get("FAM")] = current

        if tag is "INDI":
            current = {"INDI": arguments}
        else:
            current = {"FAM": arguments}
    else:
        tag = parsed[1].upper()
        arguments = " ".join(parsed[2:])

    level = parsed[0]
    valid = "Y" if TAGS.get(tag) is level else "N"

    # add info to dict
    if current:
        # get rid of junk tags
        if tag in TAG_FILTER:
            # special case
            if tag is "DATE":
                current[date_for] = arguments

if current:
    if current.get("INDI"):
        INDI[current.get("INDI")] = current
    elif current.get("FAM"):
        FAM[current.get("FAM")] = current
