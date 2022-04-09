from base64 import encode
from operator import contains
from xml.etree.ElementTree import tostring
import requests
from bs4 import BeautifulSoup
import json
import re

scrapeData = []

def getNodes(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    results = soup.find_all("div", class_="course first")

    for element in results:
        title = element.find("a") 
        desc = element.find("p")

        if title: 
            title = re.search(".+(?= -)", title.text)
            if desc:
                scrapeData.append({ "title" : title.group(), "desc" : desc.text })
            else:
                scrapeData.append({ "title" : title.group(), "desc" : "No description" })

URLs = [
    "https://apps.ualberta.ca/catalogue/course/cmput",
    # "https://apps.ualberta.ca/catalogue/course/zool",
    # "https://apps.ualberta.ca/catalogue/course/physl"
]
for URL in URLs:
    getNodes(URL)


with open('course2.json', encoding = 'utf-8') as json_file:
    data = json.load(json_file)

scrapeTitles = []


def parseReqs(string, target, rORc):
    #split string based on different courses

    greqArray = re.split("(?:(?:;)? and )|; ", string)
    for greq in greqArray:
        #find multiple possible courses
        if re.search("^\d{3}", greq):
            print(greq)
            index = greqArray.index(greq)
            prevGreq = re.search("[A-Z]*", greqArray[index - 1])

            greq = prevGreq.group() + " " + greq

        duplicates = re.findall("(?:[A-Z]+ \d{3})|(?:\d{3}(?!-))", greq)

        for dup in duplicates:
            if re.search("^\d{3}", dup):
                prevDup = re.search("[A-Z]*", duplicates[0])

                index = duplicates.index(dup)
                duplicates[index] = prevDup.group() + " " + dup

        if len(duplicates) > 1:
            #assign special link

            source = duplicates[0]

            for dup in duplicates:
                
                matches = [node["title"] for node in data["nodes"] if node["title"] == dup]
                if len(matches) > 0:
                    source = dup
                    break
     
            data["links"].append({ "source": source, "target": target, "type": "multi" + rORc})

        elif len(duplicates) == 1:
            #assign normal link

            source = duplicates[0]
            
            data["links"].append({ "source": source, "target": target, "type": "norm" + rORc})
            
        else:
            #check for common exceptions
            if "consent of the instructor" in greq:
                break

            #get manual input
            valid = False
            while valid == False:
                print("**Need manual input**")
                print("Requisite: " + greq)
                
                source = input()

                if source == "skip":
                    break
                if source == "more info":
                    print("Class: " + target)
                    print("Parsed description:")
                    print(greqArray)
                    continue
                if source == "two":
                    #create two sources
                    #by adding a duplicate greq to the next entry in greqArray
                    index = greqArray.index(greq)
                    greqArray.insert(index, greq)

                source = re.findall("[A-Z]+ \d{3}", source)
                if len(source) == 1:
                    valid = True
                    data["links"].append({ "source": source[0], "target": target, "type": "multi" + rORc})
                    print("Course entered: " + source[0])
                else:
                    valid = False
                    print("**Invalid entry**")
        

highestNode = max(data["nodes"], key = lambda node: node["id"])
nodeIdCounter = highestNode["id"]

#Create new nodes and links
for node in scrapeData:
    desc = node["desc"]
    if desc == "No description":
        print("No description for: " + node["title"] + ". Skipping node")
        continue
    
    matches = [dNode["title"] for dNode in data["nodes"] if dNode["title"] == node["title"]]
    if len(matches) > 0:
        print("Already have nodes for: " + node["title"] + ". Skipping node")
        continue

    data["nodes"].append({ "id": nodeIdCounter, "title": node["title"], "desc": node["desc"]})
    nodeIdCounter += 1

    coreqs = re.search("(?<=Corequisites: ).*(?=.$)", desc)
    reqs = re.search("(?<=Prerequisites: ).*(?=.$)", desc)
    if coreqs and reqs:

        reqs = re.search("(?<=Prerequisites: ).*(?=. Corequisites)", desc)
        parseReqs(reqs.group(), node["title"], "R")
        parseReqs(coreqs.group(), node["title"], "C")

    elif reqs:
        parseReqs(reqs.group(), node["title"], "R")
    elif coreqs:
        parseReqs(coreqs.group(), node["title"], "C")

    else:
        continue

def updateDesc():
    for node in scrapeData:
        scrapeTitles.append(node["title"])

    def getDesc(title):
        for node in scrapeData:
            if node["title"] == title:
                return node["desc"]


    for node in data["nodes"]:
        if node["title"] in scrapeTitles and "desc" not in node:
            node.update({"desc": "From course catalogue: " + getDesc(node["title"])})
updateDesc()



def renameLinks():
    for link in data["links"]:
        sourceId = [node["id"] for node in data["nodes"] if node["title"] == link["source"]]
        targetId = [node["id"] for node in data["nodes"] if node["title"] == link["target"]]

        if len(sourceId) > 0 and len(targetId) > 0:
            link["source"] = sourceId[0]
            link["target"] = targetId[0]
        elif len(sourceId) == 0:
            source = str(link["source"])
            print("Could not find id for: " + source)

            data["links"] = [dLink for dLink in data["links"] if dLink["target"] != link["target"]]
        else:
            print("I'm not sure what happened")
renameLinks()

        




with open("UPcourse2.json", "w") as outfile:
    json.dump(data, outfile)