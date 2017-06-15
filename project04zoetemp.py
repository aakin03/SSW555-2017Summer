# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 03
# Written in Python 3

import sys, unittest
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
def persist(buffer):
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
        husb = FAM.get(marriage, {}).get("MARR")
        wife = FAM.get(marriage, {}).get("WIFE")
        spouses.append(husb if husb != ident else wife)
    return spouses

def get_earlier_marr(ident):
    marriages = INDI.get(ident, {}).get("FAMS", [])
    date_low = 0
    for marriage in marriages:
        if(marriage != 0 and marriage != ""):
            print(marriage)
            date = FAM.get(marriage, {}).get("HUSB")
            #print(date)
            #date = datetime.strptime(date, "%d %b %Y")
            #if date_low == 0 or ((date.year - date_low.year) - (1 if (date.month, date.day) < (date_low.month, date_low.day) else 0) < 0):
                #date_low = date
    return date_low



def marriagable(ident):
    if current.get("INDI"):
        birthday = current.get("BIRT")
        if(birthday):
            birthday = datetime.strptime(birthday, "%d %b %Y")
            marriage = get_earlier_marr(current.get("INDI"))
            #print(marriage)
            
    #try:
     #   if(ident):
            #print(ident)
      #      birthday = INDI.get(ident, {}).get("BIRT")
       #     marriages = INDI.get(ident, {}).get("FAMS", [])
        #    birthday = datetime.strptime(birthday, "%d %b %Y")
        #for marriage in marriages:
         #   wedding_date = FAM.get(marriage, {}).get("MARR")
          #  wedding_date = datetime.strptime(wedding_date, "%d %b %Y")
           # if ((wedding_date.year - birthday.year) - (1 if (wedding_date.month, wedding_date.day) < (birthday.month, birthday.day) else 0) < 14):
            #    raise ValueError("Individual has an illegal marriage:", INDI.get(ident, {}).get("NAME"))
       # return 0
    #except:
     #   return 0

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
            persist(current)
            marriagable(current)

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
    marriagable(current)


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
    
class TestUS10(unittest.TestCase):
    def test1(self):
        #ensures the existance of marriagable
        self.failUnless(marriagable is not None)
        
    

# run automated tests using unittest
def run_test_harness():
    unittest.main()
