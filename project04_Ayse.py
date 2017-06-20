# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 03
# Written in Python 3

import sys, unittest, time
from datetime import datetime

from prettytable import PrettyTable
from inspect import signature

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

# list of tuples (Name, DOB) to prevent duplicates
NAME_AND_BIRTHDAY = []

# buffer to hold person/family info
current = None
# buffer to store what a DATE tag is for
date_for = None

# helper function to save buffer into collection
# identifies what type of object is in "current"
# then saves it into the corresponding dictionary
def persist(current):
    if current.get("INDI"):
        # create a tuple that is used to check for uniqueness
        name_birthday = (current.get("NAME", ""), current.get("BIRT"))
        # check if dates are legitimate 
        if name_birthday in NAME_AND_BIRTHDAY:
            raise ValueError("Duplicate individual detected in file:", name_birthday)
        # check to see if individual already in individual collection
        if current.get("INDI") in INDI:
            dupINDI(current.get("INDI"), current.get("NAME"))
        else:
            # add user into the collection
            INDI[current.get("INDI")] = current
            # update the list with the buffer
            NAME_AND_BIRTHDAY.append(name_birthday)
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

def marriagable(ident):
    # able to wed - get dob & wedding date
    try:
        if(ident):
            #does not process first line
            birthday = INDI.get(ident, {}).get("BIRT").get("DATE")
            marriages = INDI.get(ident, {}).get("FAMS", [])
            birthday = datetime.strptime(birthday, "%d %b %Y")
        for marriage in marriages:
            wedding_date = FAM.get(marriage, {}).get("MARR")
            wedding_date = datetime.strptime(wedding_date, "%d %b %Y")
            if ((wedding_date.year - birthday.year) - (1 if (wedding_date.month, wedding_date.day) < (birthday.month, birthday.day) else 0) < 14):
                print(INDI.get(ident, {}).get("BIRT") + " was illegally married.")
                #FAM[INDI.get("MARR")] = "NA"
                #FAM[INDI.get("HUSB")] = "NA"
                #FAM[INDI.get("WIFE")] = "NA"
                #if(FAM.get(marriage, {}).get("CHIL") != "NA" and (calc_age(birthday) - calc_age(FAM.get(marriage, {}).get("CHIL")
        return 0
    except:
        return 0

def dupINDI(ident, name):
    # another individual added with same ID as another individual already recorded
    raise ValueError ("Error US22: " + name + " (" + ident + ") has the same ID as " + lookup_name(ident))

def dupFAM(ident):
    raise ValueError ("Error US22: Another family already has the ID: " + ident)

def legitDate(theDate, name, ident):
    dateFormat = "%d %b %Y"
    try:
        theDate = datetime.strptime(theDate, dateFormat)
    except:
        raise ValueError ("Error US42: " + theDate + " is not a real date. Please fix "+ name + " (" + ident + ")'s information before running again.")
        
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
            if current.get("INDI") in INDI:
                dupINDI(current.get("INDI"), current.get("NAME"))
            elif current.get("FAM") in FAM:
                dupFAM(current.get("FAM"))
            else:
                persist(current)

        # now initalize the new record
        if tag == "INDI":
            current = {"INDI": arguments}
            marriagable(current)
        else:
            current = {"FAM": arguments}
    else:
        tag = parsed[1].upper()
        arguments = " ".join(parsed[2:])


    # add info to dict
    if current:
        # get rid of junk tags
        if tag in TAG_FILTER:
            # capture dates prefix
            if tag in DATE_TAGS:
                date_for = tag
            # special case to combine date with preceding tag
            elif tag == "DATE":
                legitDate(arguments, current.get("NAME"), current.get("INDI"))
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

f.close()

# persist final buffer
if current:
    persist(current)


if __name__ == "__main__":
    # setup the identity table
    id_table = PrettyTable()
    id_table.field_names = ["ID", "Name", "Gender", "Birthday", "Age", "Alive",
                            "Death", "Child", "Spouse"]
    for key, person in INDI.items():
        id_table.add_row([key, person.get("NAME"), person.get("SEX"),
                          person.get("BIRT"), calc_age(person.get("BIRT")), (person.get("DEAT") == None),
                          person.get("DEAT", "NA"),
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

class TestUS22(unittest.TestCase):
    def test1Akin(self):
        # Ensures existance of dupINDI & dupFAM
        self.assertTrue(dupINDI is not None)
        self.assertTrue(dupFAM is not None)
    def test2Akin(self):
        # Remove individuals and names & birthday records
        INDI.clear()
        NAME_AND_BIRTHDAY.clear()
        new_user = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
        # Make sure new user can be added normally
        persist(new_user)
        add_user = {'@I1@': new_user}
        self.assertEqual(INDI, add_user, msg = "Persist did not function as expected")
    def test3Akin(self):
        # Check duplicate individual ID function against a random user not being inserted
        new_user = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
        with self.assertRaises(ValueError):
            dupINDI(new_user.get("INDI"), new_user.get("NAME"))
    def test4Akin(self):
        # Try to insert individual with same ID as someone already inserted
        new_user = {'INDI': '@I1@', 'NAME': 'Rainer /Shine/', 'SEX': 'M', 'BIRT': '1 AUG 1975', 'FAMC': '@F5@'}
        with self.assertRaises(ValueError):
            persist(new_user)
    def test5Akin(self):
        # Checks duplicate family ID function against a random family not being inserted
        with self.assertRaises(ValueError):
            dupFAM('@F2@')

class TestUS42(unittest.TestCase):
    def test1Akin(self):
        # Ensures existance of legitDate
        self.assertTrue(legitDate is not None)
    def test2Akin(self):
        INDI.clear()
        NAME_AND_BIRTHDAY.clear()
        #Make sure new_user can still be added with legitimate date
        new_user = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
        persist(new_user)
    def test3Akin(self):
        new_user = {'INDI': '@I2@', 'NAME': 'Phil /Dunfee/', 'SEX': 'M', 'BIRT': '35 MAY 1972', 'FAMC': '@F1@'}
        with self.assertRaises(ValueError):
            legitDate(new_user.get("BIRT"), new_user.get("NAME"), new_user.get("INDI"))


# run automated tests using unittest
def run_test_harness():
    unittest.main()
