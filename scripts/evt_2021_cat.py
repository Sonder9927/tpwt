# evt_2021_cat.py
# author  : sonder
# version : 1.0
"""
This will use 2021_30.csv and 2021_120.csv event files
to get 30--120 event.cat

Those .py which are used to cut event 
will be update as I'm free.
"""

str1 = []
with open("2021_30.csv", "r", encoding="utf-8") as f1:
    for line in f1.readlines():
        str1.append(line.replace("\n", ""))

str2 = []
with open("2021_120.csv", "r", encoding="utf-8") as f2:
    for line in f2.readlines():
        str2.append(line.replace("\n", ""))

for i in str2:
    if not i in str1:
        with open("event.cat", "r", encoding="utf-8") as f:
            f.write(i[:19].replace("-", "/").replace("T", ",") + "\n")
