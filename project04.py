# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 03
# Written in Python 3

import sys, unittest
from datetime import datetime, timedelta

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

# list of errors
ERRORS = []

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
        if name_birthday in NAME_AND_BIRTHDAY:
            raise ValueError("Duplicate individual detected in file:", name_birthday)
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
            birthday = INDI.get(ident, {}).get("BIRT")
            marriages = INDI.get(ident, {}).get("FAMS", [])
            birthday = datetime.strptime(birthday, "%d %b %Y")
        for marriage in marriages:
            wedding_date = FAM.get(marriage, {}).get("MARR")
            wedding_date = datetime.strptime(wedding_date, "%d %b %Y")
            if ((wedding_date.year - birthday.year) - (1 if (wedding_date.month, wedding_date.day) < (birthday.month, birthday.day) else 0) < 14):
                print(INDI.get(ident, {}).get("NAME").replace('/','') + " was illegally married (under 14 years old at marriage).")
                return False
                #FAM[INDI.get("MARR")] = "NA"
                #FAM[INDI.get("HUSB")] = "NA"
                #FAM[INDI.get("WIFE")] = "NA"
                #if(FAM.get(marriage, {}).get("CHIL") != "NA" and (calc_age(birthday) - calc_age(FAM.get(marriage, {}).get("CHIL")
        return True
    except:
        return False

def dupINDI(ident, name):
    # another individual added with same ID as another individual already recorded
    ERRORS.append("Error US22: " + name + " (" + ident + ") has the same ID as " + lookup_name(ident))

def dupFAM(ident):
    ERRORS.append("Error US22: Another family already has the ID: " + ident)

def legitDate(theDate, name, ident):
    try:
        theDate = datetime.strptime(theDate, "%d %b %Y")
    except:
        ERRORS.append("Error US42: " + theDate + " is not a real date. Please fix "+ name + " (" + ident + ")'s information before running again.")

def upcoming_bdays(ident):
    today = datetime.today()
    name = INDI.get(ident, {}).get("NAME")
    bday_og = INDI.get(ident, {}).get("BIRT")
    bday = datetime.strptime(bday_og, "%d %b %Y")
    bday = bday.replace(year = today.year)
    margin = today + timedelta(days = 30)
    if(INDI.get(ident, {}).get("DEAT")):
        return
    if(bday - today < timedelta(days = 30) and bday - today > timedelta(days = 0)):
        print("Upcoming Birthday: " + name + ", " + bday_og)
        return 1
    return 0

def upcoming_marr(ident):
    today = datetime.today()
    if FAM.get(ident, {}).get("MARR"):
        marr1 = FAM.get(ident, {}).get("MARR")
        husb = FAM.get(ident, {}).get("HUSB")
        husb = lookup_name(husb)
        wife = FAM.get(ident, {}).get("WIFE")
        wife = lookup_name(wife)
        marr = datetime.strptime(marr1, "%d %b %Y")
        marr = marr.replace(year = today.year)
        margin = today + timedelta(days = 30)
        if(marr - today < timedelta(days = 30) and marr - today > timedelta(days = 0)):
            print("Upcoming Anniversary: " + marr1 + " for " + husb + " & " + wife)
        return 1
    return 0

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

for person in INDI:
    upcoming_bdays(person)
    marriagable(person)

for family in FAM:
    upcoming_marr(family)

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

    print("\nIndividuals")
    print(id_table)

    fam_table = PrettyTable()
    fam_table.field_names = ["ID", "Married", "Divorced", "Husband ID", "Husband Name",
                             "Wife ID", "Wife Name", "Children"]
    for key, family in FAM.items():
        fam_table.add_row([family.get("FAM"), family.get("MARR", "NA"), family.get("DIV", "NA"),
                           family.get("HUSB"), lookup_name(family.get("HUSB")), family.get("WIFE"),
                           lookup_name(family.get("WIFE")), str(family.get("CHIL"))])

    print("\nFamilies")
    print(fam_table)

    for e in ERRORS:
        print (e)

class TestUS23(unittest.TestCase):
    def test1(self):
        # ensure the persist() function exists in the program
        self.failUnless(persist is not None)
    def test2(self):
        self.assertEqual(len(signature(persist).parameters), 1, msg="Incorrect number of params for persist()")
    def test3(self):
        # remove everything
        INDI.clear()
        example = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
        persist(example)
        # make sure user can be added in normally
        expected = {'@I1@': example}
        self.assertEqual(INDI, expected, msg="Persist did not function as expected")
    def test4(self):
        # try to insert duplicate:
        try:
            example = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
            persist(example)
            self.fail("Duplicate error was not raised")
        except:
            pass
    def test5(self):
        # ensure return value is set to None
        example = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
        res = persist(example)
        self.assertEqual(res, None, msg="Incorrect return type")
    
class TestUS38(unittest.TestCase):
    def test1(self):
        #ensures the existance of upcoming_bdays
        self.failUnless(upcoming_bdays is not None)
    def test2(self):
        #insert bday that requires 3 months for 30 days
        try:
            pers = {'INDI': '@I1@', 'NAME': 'Zoe /Dunfee/', 'SEX': 'F', 'BIRT': '10 FEB 1993', 'FAMC': '@F1@'}
            num = upcoming_bdays(pers.get("INDI"))
            if num != 0:
                self.fail("Incorrectly predicted a birthday.")
        except:
            pass
    def test3(self):
        #insert earlier bday
        try:
            pers = {'INDI': '@I1@', 'NAME': 'Zoe /Dunfee/', 'SEX': 'F', 'BIRT': '10 JAN 1993', 'FAMC': '@F1@'}
            num = upcoming_bdays(pers.get("INDI"))
            if num != 0:
                self.fail("Incorrectly predicted a birthday.")
        except:
            pass
    def test4(self):
        #insert upcoming bday
        try:
            pers = {'INDI': '@I1@', 'NAME': 'Zoe /Dunfee/', 'SEX': 'F', 'BIRT': '10 JUL 1993', 'FAMC': '@F1@'}
            num = upcoming_bdays(pers.get("INDI"))
            if num != 0:
                self.fail("Incorrectly predicted a birthday.")
        except:
            pass
    def test5(self):
        #insert bday that requires flip from Dec to Jan
        try:
            INDI.clear()
            pers = {'INDI': '@I1@', 'NAME': 'Zoe /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
            num = upcoming_bdays(pers.get("INDI"))
            if num != 0:
                self.fail("Incorrectly predicted a birthday.")
        except:
            pass

class TestUS22(unittest.TestCase):
    def test1Akin(self):
        # Ensures existance of dupID
        self.failUnless(dupINDI is not None)
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
        try:
            new_user = {'INDI': '@I1@', 'NAME': 'Hayley /Dunfee/', 'SEX': 'F', 'BIRT': '10 DEC 1993', 'FAMC': '@F1@'}
            dupINDI(new_user.get("INDI"), new_user.get("NAME"))
            self.fail("Duplicate individual ID error was not raised")
        except:
            pass
    def test4Akin(self):
        # Try to insert individual with same ID as someone already inserted
        try:
            new_user = {'INDI': '@I1@', 'NAME': 'Rainer /Shine/', 'SEX': 'M', 'BIRT': '1 AUG 1975', 'FAMC': '@F5@'}
            persist(new_user)
            self.fail("Duplicate individual ID error was not raised")
        except:
            pass
    def test5Akin(self):
        # Checks duplicate family ID function against a random family not being inserted
        try:
            dupFAM('@F2@')
            self.fail("Duplicate family ID error was not raised")
        except:
            pass

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
