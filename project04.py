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

# list of notices
STATEMENTS = []

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
            ERRORS.append("Error US23: Duplicate individual detected in file: " + current.get("NAME") + " (" + current.get("INDI") + ") with birthday: " + current.get("BIRT"))
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
                ERRORS.append("Error US10: "+ INDI.get(ident, {}).get("NAME").replace('/','') + " was illegally married (under 14 years old at marriage).")
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
    ERRORS.append("Error US22: There are multiple families with the ID: " + ident)

def legitDate(theDate, name, ident):
    now = datetime.now()
    try:
        theDate = datetime.strptime(theDate, "%d %b %Y")
        if theDate.year > now.year:
            theDate = datetime.strftime(theDate, "%d %b %Y")
            ERRORS.append("Error US01: " + theDate + " is in the future. Please fix " + name + " (" + ident + ")'s information before running again.")
    except ValueError:
        ERRORS.append("Error US42: " + theDate + " is not a real date. Please fix "+ name + " (" + ident + ")'s information before running again.")

def orphans(famID):
    famMom = INDI.get(FAM.get(famID).get("WIFE"))
    famDad = INDI.get(FAM.get(famID).get("HUSB"))
    famKids = []
    if FAM.get(famID).get("CHIL"):
        for kid in FAM.get(famID).get("CHIL"):
            try:
                birthday = INDI.get(kid).get("BIRT")
                if calc_age(birthday) < 18:
                    famKids.append(INDI.get(kid).get("NAME") + " (" + kid + ")")
            except AttributeError:
                pass
    if famMom:
        if famMom.get("DEAT") and famDad:
                if famDad.get("DEAT") and famKids:
                    STATEMENTS.append("US33 - The following kids are orphans: " + str(famKids))

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
        STATEMENTS.append("US38 - Upcoming Birthday: " + name + ", " + bday_og)
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
            STATEMENTS.append("US39 - Upcoming Anniversary: " + marr1 + " for " + husb + " & " + wife)
        return 1
    return 0

	
def birthb4death(ident):
    if ident:
        if INDI.get(ident, {}).get("DEAT"):
            dday = INDI.get(ident, {}).get("DEAT")
            bday = INDI.get(ident, {}).get("BIRT")
            dday = datetime.strptime(dday, "%d %b %Y")
            bday = datetime.strptime(bday, "%d %b %Y")
            name = INDI.get(ident, {}).get("NAME")
            if(dday - bday <timedelta(days=0)):
                ERRORS.append("Error US03: Birth before Death: " + name)
                return 1
        return 0

def recent_births(ident):
    today = datetime.today()
    name = INDI.get(ident, {}).get("NAME")
    bday_og = INDI.get(ident, {}).get("BIRT")
    bday = datetime.strptime(bday_og, "%d %b %Y")
    margin = today + timedelta(days = 30)
    if(INDI.get(ident, {}).get("DEAT")):
        return
    if(today - bday < timedelta(days = 30) and today - bday > timedelta(days = 0)):
        STATEMENTS.append("US35 - Recent Birth: " + name + ", " + bday_og)
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
    birthb4death(person)
    recent_births(person)

for family in FAM:
    upcoming_marr(family)
    orphans(family)

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

    for s in STATEMENTS:
        print (s)