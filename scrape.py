from base64 import encode
from operator import contains
from xml.etree.ElementTree import tostring
import requests
from bs4 import BeautifulSoup
import json
import re

import seaborn as sns

subjects = [
    "CMPUT",
    "ZOOL",
    "PHYSL",
    "ANAT",
    "CELL",
    "BIOCH",
    "MDGEN",
    "NEURO",
    "ONCOL",
    "PMCOL",
    "CHEM",
    "BIOIN",
    "ASTRO",
    "PSYCO",
    "MICRB",
    "PHYS",
    "MATH",
    "STAT",
    "BIOL",
    "GENET",
    "IMIN",
    "ENGG",
    "ANTHR",
    "FS",
    "ENGL",
    "WRS",
    "HIST",
    "PHIL",
    "SOC",
    "ECON",
    "ENT",
    "FIN"
]

subjects.sort()

colorDict = dict(zip(subjects, ["rgb" + str(tuple(int(c*255) for c in cs)) for cs in sns.color_palette("husl", len(subjects))]))

scrapeData = []

def getNodes(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    results = soup.find_all("div", class_="course first")

    for element in results:
        title = element.find("a") 
        desc = element.find("p")

        if title: 
            descTitle = re.search("(?<=- ).*", title.text)
            title = re.search("^.*?(?= -)", title.text)

            if desc:
                scrapeData.append({ "title" : title.group(), "desc" : descTitle.group() + " -- \n" + desc.text })
            else:
                scrapeData.append({ "title" : title.group(), "desc" : "No description" })


BASE_URL = "https://apps.ualberta.ca/catalogue/course/"

def getSubjects() -> list:
    page = requests.get(BASE_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    URLs = [BASE_URL + re.search(r"(?<=\/)\w+$", tag["href"]).group() for tag in soup.find_all("a", class_="d-block")]

    return URLs

URLs = getSubjects()

# print(URLs)

for URL in URLs:
    getNodes(URL)


# with open('course2.json', encoding = 'utf-8') as json_file:
#     data = json.load(json_file)
# highestNode = max(data["nodes"], key = lambda node: node["id"])
# nodeIdCounter = highestNode["id"]

data = {
    "nodes" : [],
    "links" : [],
    "subjects": subjects,
    "noLinks": [],
}
nodeIdCounter = 0

scrapeTitles = []


def toUpper(matchObj):
    return matchObj.group().upper()
def parseReqs(string, target, rORc):
    #split string based on different courses


    ##TODO: A and B get equal treatment PHYSL 210A vs B
    reqArray = re.split("(?:(?:;)? and )|; ", string)
    for req in reqArray:
        
        #Check if string has a 3 digit number
        if re.search("\d{3}", req) == None:
            # print("Skipping: " + req)
            continue
        #Check if a string has a 3 digit number at the beginning
        if re.search("^\d{3}(?!-| level)", req):
            index = reqArray.index(req)
            i = 1
            siblingReq = None
            while siblingReq == None:
                siblingReq = re.search("(?<![^A-Z ])[A-Z ]+(?= \d{3})", reqArray[index - i])
                i += 1
            req = siblingReq.group() + " " + req

        #Check if a string has been spelt without uppercase by accident...
        req = re.sub("[A-Z][a-z]\w+", toUpper, req)

        #Find course codes by looking for all caps followed by a 3 digit number
        duplicates = re.findall("(?:(?<![^A-Z (])[A-Z ]+ \d{3})(?!-| level)|(?:\d{3})(?!-| level)", req)

        if len(duplicates) > 1:
            #assign special link
            
            for dup in duplicates:
                index = duplicates.index(dup)
                if re.search("^\d{3}", dup):
                    siblingDup = None
                    i = 1
                    while siblingDup == None:
                        siblingDup = re.search("(?<![^A-Z ])[A-Z ]+(?= \d{3})", duplicates[index - i])
                        i += 1
                    duplicates[index] = siblingDup.group() + " " + dup

                source = duplicates[index]
                if index > 0:
                    data["links"].append({ "source": source, "target": target, "type": "multi" + rORc, "duplicate": True})
                else:
                    data["links"].append({ "source": source, "target": target, "type": "multi" + rORc})
            # source = duplicates[0]

            # for dup in duplicates:
            #     matches = [node["title"] for node in data["nodes"] if node["title"] == dup]
            #     if len(matches) > 0:
            #         source = dup
            #         break

            # data["links"].append({ "source": source, "target": target, "type": "multi" + rORc})

        elif len(duplicates) == 1:
            #assign normal link
            source = duplicates[0]
            data["links"].append({ "source": source, "target": target, "type": "norm" + rORc})
            
        else:
            #check for common exceptions
            if "consent" in req:
                break
            #get manual input
            valid = False
            while valid == False:
                ### Currently set to skip for developing ###

                # print("**Need manual input**")
                # print("Requisite: " + req)
                source = "skip"
                
                if source == "skip":
                    break
                if source == "more info":
                    print("Class: " + target)
                    print("Parsed description:")
                    print(reqArray)
                    continue
                if source == "two":
                    #create two sources
                    #by adding a duplicate req to the next entry in reqArray
                    index = reqArray.index(req)
                    reqArray.insert(index, req)
                source = re.findall("[A-Z]+ \d{3}", source)
                if len(source) == 1:
                    valid = True
                    data["links"].append({ "source": source[0], "target": target, "type": "multi" + rORc})
                else:
                    valid = False
                    print("**Invalid entry**")
        
def addNodes():
    #Create new nodes and links
    for node in scrapeData:
        desc = re.sub(" {2,}", " ", node["desc"])
        if desc == "No description":
            # print("No description for: " + node["title"] + ". Skipping node")
            continue
        
        matches = [dNode["title"] for dNode in data["nodes"] if dNode["title"] == node["title"]]
        if len(matches) > 0:
            print("Already have nodes for: " + node["title"] + ". Skipping node")
            continue
        
        subject = re.search(".*(?= \d)", node["title"])
        color = colorDict[subject.group()]
        global nodeIdCounter
        data["nodes"].append({ "id": nodeIdCounter, "title": node["title"], "desc": desc, "color": color})
        nodeIdCounter += 1

        coreqs = re.search("((?<=Corequisites: ).*?(?=(\.)|(.$)))|((?<=Corequisite: ).*?(?=(\.)|(.$)))|((?<=Corequisite ).*?(?=\.|(.$)))|((?<=Corequisites ).*?(?=\.|(.$)))",
            desc)
        prereqs = re.search("((?<=Prerequisites: ).*?(?=\.|(.$)))|((?<=Prerequisite: ).*?(?=(\.)|(.$)))|((?<=Prerequisite ).*?(?=\.|(.$)))|((?<=Prerequisites ).*?(?=\.|(.$)))",
            desc)
        if coreqs and prereqs:
            parseReqs(prereqs.group(), node["title"], "R")
            parseReqs(coreqs.group(), node["title"], "C")
        elif prereqs:
            parseReqs(prereqs.group(), node["title"], "R")
        elif coreqs:
            parseReqs(coreqs.group(), node["title"], "C")
        else:
            continue
addNodes()
# def updateDesc():
#     for node in scrapeData:
#         scrapeTitles.append(node["title"])

#     def getDesc(title):
#         for node in scrapeData:
#             if node["title"] == title:
#                 return node["desc"]


#     for node in data["nodes"]:
#         if node["title"] in scrapeTitles and "desc" not in node:
#             node.update({"desc": "From course catalogue: " + getDesc(node["title"])})
# updateDesc()

def renameLinks():
    for link in data["links"]:

        if type(link["source"]) is int:
            continue

        sourceId = [node["id"] for node in data["nodes"] if link["source"] in node["title"]]
        targetId = [node["id"] for node in data["nodes"] if node["title"] == link["target"]]
        if len(sourceId) > 0 and len(targetId) > 0:
            link["source"] = sourceId[0]
            link["target"] = targetId[0]
        elif len(sourceId) == 0:
            source = link["source"]
            print("Could not find id for: " + source + ". Target: " + link["target"])
            data["links"] = [dLink for dLink in data["links"] if dLink["target"] != link["target"]]
        else:
            print("Undefined error: " + link["target"])
renameLinks()

def removeNodes():
    for node in data["nodes"]:
        linksThatTarget = [link for link in data["links"] if link["target"] == node["id"]]
        linksThatUse = [link for link in data["links"] if link["source"] == node["id"]]

        if len(linksThatTarget) == 0 and len(linksThatUse) == 0:
            data["noLinks"].append(node["title"])
            # data["nodes"] = [dNode for dNode in data["nodes"] if dNode["title"] != node["title"]]
removeNodes()

with open("../TonyinBio.github.io/projects/bigplanner/dags/UPcourse2.json", "w") as outfile:
    json.dump(data, outfile)