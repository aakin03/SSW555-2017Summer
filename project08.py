# Michael Curry, Zoë Millard, Ayse Akin
# SSW 555 Project 07
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
TAG_FILTER = ["NAME", "SEX", "BIRT", "DEAT", "DATE", "MARR", "DIV", "HUSB", "WIFE", "CHIL", "FAMC", "FAMS", "_CURRENT"]
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
        if current.get("FAM") in FAM:
            dupFAM(current.get("FAM"))
        else:
            FAM[current.get("FAM")] = current

# helper functions for table
def lookup_name(ident):
    # looks up name for given ID
    if ident:
        return INDI.get(ident, {}).get("NAME")
    return None

def calc_age(dob, endDay):
    # age calculator
    try:
        endDay = datetime.strptime(endDay, "%d %b %Y")
        birthday = datetime.strptime(dob, "%d %b %Y")
        return endDay.year - birthday.year - (1 if (endDay.month, endDay.day) <
                                            (birthday.month, birthday.day) else 0)
    except:
        try:
            birthday = datetime.strptime(dob, "%d %b %Y")
            return endDay.year - birthday.year - (1 if (endDay.month, endDay.day) <
                                            (birthday.month, birthday.day) else 0)
        except:
            return 0

def check_age(ident):
    if INDI.get(ident, {}).get("DEAT"):
        theAge = calc_age(INDI.get(ident, {}).get("BIRT"), INDI.get(ident, {}).get("DEAT"))
    else:
        theAge = calc_age(INDI.get(ident, {}).get("BIRT"), datetime.today())
    if not INDI.get(ident, {}).get("DEAT") and theAge >= 150:
        ERRORS.append("Error US07: Person " + INDI.get(ident, {}).get("NAME") + " must be less than 150 years old")

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
            # check to ensure person is born before marriage
            if ((wedding_date.year - birthday.year) - (1 if (wedding_date.month, wedding_date.day) < (birthday.month, birthday.day) else 0) < 0):
                ERRORS.append("Error US02: "+ INDI.get(ident, {}).get("NAME").replace('/','') + " was married before birth.")
                return False
            # check to make sure it is not a posthumus marriage
            dead = INDI.get(ident, {}).get("DEAT")
            if dead:
                death_date = datetime.strptime(dead, "%d %b %Y")
                if ((wedding_date.year - death_date.year) - (1 if (wedding_date.month, wedding_date.day) < (death_date.month, death_date.day) else 0) >= 0):
                    ERRORS.append("Error US05: "+ INDI.get(ident, {}).get("NAME").replace('/','') + " was married after death.")
            # check for legal marriage age
            elif ((wedding_date.year - birthday.year) - (1 if (wedding_date.month, wedding_date.day) < (birthday.month, birthday.day) else 0) < 14):
                ERRORS.append("Error US10: "+ INDI.get(ident, {}).get("NAME").replace('/','') + " was illegally married (under 14 years old at marriage).")
                return False
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
            ERRORS.append("Error US01: " + theDate + " is in the future. " + name + " (" + ident + ")'s information is incorrect.")
    except ValueError:
        ERRORS.append("Error US42: " + theDate + " is not a real date.")

def orphans(famID, famMom, famDad):
    famKids = []
    if FAM.get(famID).get("CHIL"):
        for kid in FAM.get(famID).get("CHIL"):
            try:
                birthday = INDI.get(kid).get("BIRT")
                if not INDI.get(kid).get("DEAT") and calc_age(birthday, datetime.today()) < 18:
                    famKids.append(INDI.get(kid).get("NAME") + " (" + kid + ")")
            except AttributeError:
                pass
    if famMom and famDad:
        if famMom.get("DEAT") and famDad.get("DEAT") and famKids:
            STATEMENTS.append("US33 - The following kids are orphans: " + str(famKids))

def livingMarried(famMom, famDad):
    if famMom and famDad:
        if not famMom.get("DEAT") and not famDad.get("DEAT"):
            STATEMENTS.append("US30 - " + famMom.get("NAME") + " (" + famMom.get("INDI") + ") and " + famDad.get("NAME") + " (" + famDad.get("INDI") + ") are living married people.")

def livingSingle(famID, famMom, famDad):
    famKids = FAM.get(famID).get("CHIL")
    if famMom and not famDad:
        STATEMENTS.append("US31 - The following individual is alive and has never been married: " + famMom.get("NAME") + " (" + famMom.get("INDI") + ")")
    if famDad and not famMom:
        STATEMENTS.append("US31 - The following individual is alive and has never been married: " + famDad.get("NAME") + " (" + famDad.get("INDI") + ")")
    if famKids:
        for kid in famKids:
            try:
                if not INDI.get(kid).get("DEAT") and calc_age(INDI.get(kid).get("BIRT"), datetime.today()) > 30 and not INDI.get(kid).get("FAMS"):
                        STATEMENTS.append("US31 - The following individual is alive and has never been married: " + INDI.get(kid).get("NAME") + " (" + INDI.get(kid).get("INDI") + ")")
            except AttributeError:
                pass

#list of deceased
deadIDs = {}
def deceased(famID, famMom, famDad):
    famKids = FAM.get(famID).get("CHIL")
    if famMom and famMom.get("DEAT"):
        deadIDs [famMom.get("INDI")] = 1
    if famDad and famDad.get("DEAT"):
        deadIDs[famDad.get("INDI")] = 1
    if famKids:
        for kid in famKids:
            if INDI.get(kid).get("DEAT"):
                deadIDs[INDI.get(kid).get("INDI")] = 1

def dNames(deadIDs):
    for key in deadIDs:
        STATEMENTS.append("US29 - " + lookup_name(key) + " (" + INDI.get(key).get("INDI") + ") is deceased.")

def marryDead(famID, famMom, famDad):
    if famMom and famDad and FAM.get(famID).get("DIV"):
        mDate = FAM.get(famID).get("MARR")
        mdDate = famMom.get("DEAT")
        ddDate = famDad.get("DEAT")
        try:
            if mdDate < mDate:
                ERRORS.append("Error US06 - " + famMom.get("NAME") + " (" + famMom.get("INDI") + ") died before her divorce.")
            if ddDate < mDate:
                ERRORS.append("Error US06 - " + famDad.get("NAME") + " (" + famDad.get("INDI") + ") died before his divorce.")
        except TypeError:
            pass

def upcoming_bdays(ident):
    today = datetime.today()
    name = INDI.get(ident, {}).get("NAME")
    bday_og = INDI.get(ident, {}).get("BIRT")
    try:
        bday = datetime.strptime(bday_og, "%d %b %Y")
        bday = bday.replace(year = today.year)
        margin = today + timedelta(days = 30)
        if(INDI.get(ident, {}).get("DEAT")):
            return
        if(bday - today < timedelta(days = 30) and bday - today > timedelta(days = 0)):
            STATEMENTS.append("US38 - Upcoming Birthday: " + name + ", " + bday_og)
    except ValueError:
        pass

def upcoming_marr(ident):
    today = datetime.today()
    if FAM.get(ident, {}).get("MARR"):
        marr1 = FAM.get(ident, {}).get("MARR")
        husb = lookup_name(FAM.get(ident, {}).get("HUSB"))
        wife = lookup_name(FAM.get(ident, {}).get("WIFE"))
        marr = datetime.strptime(marr1, "%d %b %Y")
        marr = marr.replace(year = today.year)
        margin = today + timedelta(days = 30)
        if(marr - today < timedelta(days = 30) and marr - today > timedelta(days = 0)):
            STATEMENTS.append("US39 - Upcoming Anniversary: " + marr1 + " for " + husb + " & " + wife)

def birthb4death(ident):
    try:
        if ident:
            if INDI.get(ident, {}).get("DEAT"):
                dday = datetime.strptime(INDI.get(ident, {}).get("DEAT"), "%d %b %Y")
                bday = datetime.strptime(INDI.get(ident, {}).get("BIRT"), "%d %b %Y")
                name = INDI.get(ident, {}).get("NAME")
                if(dday - bday <timedelta(days=0)):
                    ERRORS.append("Error US03: Birth before Death: " + name)
    except ValueError:
        pass

def recent_births(ident):
    today = datetime.today()
    name = INDI.get(ident, {}).get("NAME")
    try:
        bday_og = INDI.get(ident, {}).get("BIRT")
        bday = datetime.strptime(bday_og, "%d %b %Y")
        margin = today + timedelta(days = 30)
        if(INDI.get(ident, {}).get("DEAT")):
            return
        if(today - bday < timedelta(days = 30) and today - bday > timedelta(days = 0)):
            STATEMENTS.append("US35 - Recent Birth: " + name + ", " + bday_og)
    except ValueError:
        pass

def check_bigamy(ident):
    fams = INDI.get(ident, {}).get("FAMS", [])
    fam_current = False
    for fam in fams:
        if FAM.get(fam, {}).get("_CURRENT") == "Y":
            # this is an active family
            if fam_current:
                # person has two active families at current time
                ERRORS.append("Error US11: Bigamy is not allowed for person " + INDI.get(ident,{}).get("NAME"))
            fam_current = True

def cougarCheck(ident):
    if FAM.get(ident, {}).get("MARR"):
        marr1 = FAM.get(ident, {}).get("MARR")
        marr_date = datetime.strptime(marr1, "%d %b %Y")

        husb = FAM.get(ident, {}).get("HUSB")
        if (INDI.get(husb, {}).get("DEAT")):
            husb_age = calc_age(INDI.get(husb, {}).get("BIRT"), INDI.get(husb, {}).get("DEAT"))
        else:
            husb_age = calc_age(INDI.get(husb, {}).get("BIRT"), datetime.today())
        husb = lookup_name(FAM.get(ident, {}).get("HUSB"))

        wife = FAM.get(ident, {}).get("WIFE")
        if (INDI.get(wife, {}).get("DEAT")):
            wife_age = calc_age(INDI.get(wife, {}).get("BIRT"), INDI.get(wife, {}).get("DEAT"))
        else:
            wife_age = calc_age(INDI.get(wife, {}).get("BIRT"), datetime.today())
        wife = lookup_name(FAM.get(ident, {}).get("WIFE"))

        if(husb_age > wife_age*2):
            STATEMENTS.append("US34 - Large age difference: " + husb + " is over 2xs as old as " + wife)
        if(wife_age > husb_age*2):
            STATEMENTS.append("US34 - Large age difference: " + wife + " is over 2xs as old as " + husb)

def siblingSpacing(ident):
    if FAM.get(ident, {}).get("CHIL"):
        #iterate thru all siblings
        kids = FAM.get(ident, {}).get("CHIL")
        sib2 = -1
        for kid in kids:
            sib1d = INDI.get(kid, {}).get("BIRT")
            try:
                sib1 = datetime.strptime(sib1d, "%d %b %Y")
                sib1n = INDI.get(kid, {}).get("NAME")
                if(sib2 == -1):
                    sib2 = sib1
                    sib2n = sib1n
                else:
                    if((sib2 - sib1) < timedelta(days = 243) and sib2 - sib1 > timedelta(days = 2)):
                        ERRORS.append("Error US13: Sibling Spacing too small: " + sib1n + ", " + sib2n)
            except ValueError:
                pass

def marriageB4divorce(ident):
    if FAM.get(ident, {}).get("DIV"):
        div = FAM.get(ident, {}).get("DIV")
        if FAM.get(ident, {}).get("MAR"):
            mar = FAM.get(ident, {}).get("MAR")
            div = datetime.strptime(div, "%d %b %Y")
            mar = datetime.strptime(mar, "%d %b %Y")
            if((div - mar) < timedelta(days = 30)):
                ERRORS.append("Error US04: Marriage before divorce")

def noIncestAllowed(ident):
    if FAM.get(ident, {}).get("HUSB"):
        husb = FAM.get(ident, {}).get("HUSB")
        husbf = INDI.get(husb, {}).get("FAMS")
        if FAM.get(ident, {}).get("WIFE"):
            wife = FAM.get(ident, {}).get("WIFE")
            wifef = INDI.get(wife, {}).get("FAMCS")
            if(husbf == wifef):
                ERRORS.append("Error US18: Incest occuring: " + lookup_name(husb) + " & " + lookup_name(wife))

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
    check_age(person)
    check_bigamy(person)

for family in FAM:
    famMom = INDI.get(FAM.get(family).get("WIFE"))
    famDad = INDI.get(FAM.get(family).get("HUSB"))
    upcoming_marr(family)
    cougarCheck(family)
    orphans(family, famMom, famDad)
    livingMarried(famMom, famDad)
    livingSingle(family, famMom, famDad)
    siblingSpacing(family)
    deceased(family, famMom, famDad)
    marryDead(family, famMom, famDad)
    marriageB4divorce(family)
    noIncestAllowed(family)

if __name__ == "__main__":
    # setup the identity table
    id_table = PrettyTable()
    id_table.field_names = ["ID", "Name", "Gender", "Birthday", "Age", "Alive",
                            "Death", "Child", "Spouse"]
    for key, person in INDI.items():
        if (person.get("DEAT")):
           theAge = calc_age(person.get("BIRT"), person.get("DEAT"))
        else:
            theAge = calc_age(person.get("BIRT"), datetime.today())
        id_table.add_row([key, person.get("NAME"), person.get("SEX"),
                          person.get("BIRT"), theAge, (person.get("DEAT") == None),
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

    dNames(deadIDs)
    for s in STATEMENTS:
        print (s)