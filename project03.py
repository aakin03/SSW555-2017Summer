# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 03
# Written in Python 3

import sys
from datetime import datetime
from prettytable import PrettyTable

TAGS = {
    "INDI": "0", "NAME": "1", "SEX": "1",
    "BIRT": "1", "DEAT": "1", "FAMC": "1",
    "FAMS": "1", "FAM": "0", "MARR": "1",
    "HUSB": "1", "WIFE": "1", "CHIL": "1",
    "DIV": "1", "DATE": "2", "HEAD": "0",
    "TRLR": "0", "NOTE": "0"
}
TAG_FILTER = ["NAME", "SEX", "BIRT", "DEAT", "DATE", "MARR", "DIV", "HUSB", "WIFE", "CHIL", "FAMC", "FAMS"]
DATE_TAGS = ["BIRT", "DEAT", "MARR", "DIV"]

# Setup individual and family collections
INDI = {}
FAM = {}

# buffer to hold person/family info
current = None
# buffer to store what a DATE tag is for
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

    # catch record starting point
    if len(parsed) is 3 and parsed[2] in ["INDI", "FAM"]:
        tag = parsed[2].upper()
        arguments = parsed[1]

        # persist buffer information to collections
        if current:
            if current.get("INDI"):
                INDI[current.get("INDI")] = current
            elif current.get("FAM"):
                FAM[current.get("FAM")] = current

        # now initalize the new record
        if tag == "INDI":
            current = {"INDI": arguments}
        else:
            current = {"FAM": arguments}
    else:
        tag = parsed[1].upper()
        arguments = " ".join(parsed[2:])

    # deprecated information
    # level = parsed[0]
    # valid = "Y" if TAGS.get(tag) is level else "N"

    # add info to dict
    if current:
        # get rid of junk tags
        if tag in TAG_FILTER:
            # capture dates prefix
            if tag in DATE_TAGS:
                date_for = tag
            # special case to combine date with preceding tag
            elif tag == "DATE":
                current[date_for] = arguments
            # handle possibility of multiple tag values
            elif tag in ["CHIL", "FAMS"]:
                if current.get(tag):
                    current[tag] += [arguments]
                else:
                    current[tag] = [arguments]
            # non-date/child tag
            else:
                current[tag] = arguments


# persist final buffer
if current:
    if current.get("INDI"):
        INDI[current.get("INDI")] = current
    elif current.get("FAM"):
        FAM[current.get("FAM")] = current

# helper functions for table
def lookup_name(ident):
    # looks up name for given ID
    if ident:
        return INDI.get(ident, {}).get("NAME")
    return None

def calc_age(dob):
    # age calculator
    try:
        today = datetime.today()
        birthday = datetime.strptime(dob, "%d %b %Y")
        return today.year - birthday.year - (1 if (today.month, today.day) <
                                            (birthday.month, birthday.day) else 0)
    except:
        return 0

def get_children(ident):
    children = []
    marriages = INDI.get(ident, {}).get("FAMS", [])
    for marriage in marriages:
        children += FAM.get(marriage, {}).get("CHIL", [])
    return children or "NA"


def get_spouse(ident):
    spouses = []
    marriages = INDI.get(ident, {}).get("FAMS", [])
    for marriage in marriages:
        husb = FAM.get(marriage, {}).get("HUSB")
        wife = FAM.get(marriage, {}).get("WIFE")
        spouses.append(husb if husb != ident else wife)
    return spouses

# setup the identity table
id_table = PrettyTable()
id_table.field_names = ["ID", "Name", "Gender", "Birthday", "Age", "Alive",
                        "Death", "Child", "Spouse"]
for key, person in INDI.items():
    id_table.add_row([key, person.get("NAME"), person.get("SEX"),
     person.get("BIRT"), calc_age(person.get("BIRT")), (person.get("DEAT") == None), person.get("DEAT", "NA"),
     get_children(key), get_spouse(key)])

print("Individuals")
print(id_table)


fam_table = PrettyTable()
fam_table.field_names = ["ID", "Married", "Divorced", "Husband ID", "Husband Name",
                        "Wife ID", "Wife Name", "Children"]
for key, family in FAM.items():
    fam_table.add_row([family.get("FAM"), family.get("MARR", "NA"), family.get("DIV", "NA"),
    family.get("HUSB"), lookup_name(family.get("HUSB")), family.get("WIFE"),
    lookup_name(family.get("WIFE")), str(family.get("CHIL"))])

print("Families")
print(fam_table)
