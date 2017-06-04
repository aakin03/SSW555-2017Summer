# Michael Curry
# SSW 555 Project 02
# Written in Python 3.4


TAGS = {
    "INDI": "0", "NAME": "1", "SEX": "1",
    "BIRT": "1", "DEAT": "1", "FAMC": "1",
    "FAMS": "1", "FAM": "0", "MARR": "1",
    "HUSB": "1", "WIFE": "1", "CHIL": "1",
    "DIV": "1", "DATE": "2", "HEAD": "0",
    "TRLR": "0", "NOTE": "0"
}

f = open("example.ged")

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
    else:
        tag = parsed[1].upper()
        arguments = " ".join(parsed[2:])

    level = parsed[0]
    valid = "Y" if TAGS.get(tag) is level else "N"

    # print input
    print("-->", line.strip('\n'))

    # print result
    print("<--", "|".join([level, tag, valid, arguments]))
