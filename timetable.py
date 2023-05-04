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

            pattern = re.compile(r"^((CT|MPU|BM)\d{3,4})-(3-2-)?(\w{3,5}(\(..\))?)-((LAB|L|T))(\s|-)(T-)?\d{1,2}( )?(\(Online\)|\(Hybrid\))?", re.MULTILINE)
            mat = pattern.search(tfb.contents[0])

            if mat:
                # subject code (e.g TITAS(LS), BMK(FS), WPCS)
                if mat.group(4) == "ISE":
                    subject = "Imaging and Special Effects"
                elif mat.group(4) == "TITAS(LS)":
                    subject = "Islamic Civilization & Asian Civilization"                    else:
                else:
                    break
                    

                # section code (L/T/LAB)
                if mat.group(4) == "L":
                    subject +=  " (Lecture)"
                elif mat.group(4) == "T":
                    subject +=  " (Tutorial)"
                elif mat.group(4) == "LAB":
                    subject +=  " (Lab)"
                
                if mat.group(5) == "(Online)":
                    loc = "Online"
                elif mat.group(5) == "(Hybrid)":
                    loc = "Hybrid"
    
            e.name = subject
            e.begin = fromTime
            e.end = toTime
            e.location = loc

            c.events.add(e)

        i = i + 1

with open('timetable.ics', 'w') as f:
    f.writelines(c.serialize_iter())