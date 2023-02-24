from bs4 import BeautifulSoup
from ics import Calendar, Event
import arrow
import requests
import re

# replace Intake= and Week
URL = "https://api.apiit.edu.my/timetable-print/index.php?Week=YYYY-MM-DD&Intake=XXXXXXXXXX&Intake_Group=All&print_request=print_tt"
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')
tf = soup.find_all("tr")

redundancychk = -1

c = Calendar()

for tfs in tf:
    tfa = tfs.select("tr > td")
    i = 0
    day = -1
    
    e = Event()
    
    for tfb in tfa:
        if i == 0:
            day = tfb.contents[0].split()[1]

            # holidays 
            if str(day) == "DD-Mmm-YYYY":
                break

        elif i == 1:
            range = tfb.contents[0].split()
            fromTime = arrow.get(str(day) + " " + range[0] + " +08:00", "DD-MMM-YYYY HH:mm ZZ")
            toTime = arrow.get(str(day) + " " + range[2] + " +08:00", "DD-MMM-YYYY HH:mm ZZ")
        elif i == 2:
            loc = tfb.contents[0] + " | APU Campus"
        elif i == 4:

            if redundancychk == tfb.contents[0]:
                break

            redundancychk = tfb.contents[0]

            pattern = re.compile(r"(^(CT|MPU|BM)\d{3})-\d-\d-(\w+?)-(\w+)-\d+(?: (\((?:Fully )?Online\)))?", re.MULTILINE | re.DOTALL)
            mat = pattern.search(tfb.contents[0])

            # subjects
            if mat:
                # subjects from SOC
                if mat.group(2) == "CT":
                    if mat.group(3) == "ISE":
                        subject = "Imaging & Special Effects"
                    elif mat.group(3) == "CSLLT":
                        subject = "Computer System Low Level Techniques"
                    else:
                        break
                    
                    # class type (L/T/LAB)
                    if mat.group(4) == "L":
                        subject +=  " (Lecture)"
                    elif mat.group(4) == "T":
                        subject +=  " (Tutorial)"
                    elif mat.group(4) == "LAB":
                        subject +=  " (Lab)"
                # subjects from SOB
                elif mat.group(2) == "BM":
                    if mat.group(3) == "CRI":
                        subject = "Creativity & Innovation"
                    else:
                        break

                    # section code (L/T/LAB)
                    if mat.group(4) == "L":
                        subject +=  " (Lecture)"
                    elif mat.group(4) == "T":
                        subject +=  " (Tutorial)"
                    elif mat.group(4) == "LAB":
                        subject +=  " (Lab)"
                
                if mat.group(5) == "(Fully Online)":
                    loc = "Online"
            else:
                pattern = re.compile(r"((MPU)\d{4})-(\w+(\(\w+\))?)-(...)(\S|\s)(\((?:Fully )?Online\)?)?", re.MULTILINE | re.DOTALL)
                mat = pattern.search(tfb.contents[0])
                
                # MPU subjects
                if mat.group(2) == "MPU":

                    if mat.group(3) == "TITAS(LS)":
                        subject = "Islamic Civilization & Asian Civilization"
                    else:
                        break

                    if mat.group(7) == "(Fully Online)":
                        loc = "Online"
    
            e.name = subject
            e.begin = fromTime
            e.end = toTime
            e.location = loc

            c.events.add(e)

        i = i + 1

with open('timetable.ics', 'w') as f:
    f.writelines(c.serialize_iter())
