from scrape import scrape, generateColors
from requisite import parseReqs

import re
import json
from pprint import pprint

def nodeIsInvalid(node, desc, data) -> bool:
    if desc == "No description":
        # print("No description for: " + node["title"] + ". Skipping node")
        return True

    matches = [dNode["title"] for dNode in data["nodes"] if dNode["title"] == node["title"]]
    if len(matches) > 0:
        print("Already have nodes for: " + node["title"] + ". Skipping node")
        return True
    
    return False

def generateLinks(node, desc, data) -> None:
    """
    Creates links for the node
    """
    coreqPattern = r"((?<=Corequisites: ).*?(?=(\.)|(.$)))|((?<=Corequisite: ).*?(?=(\.)|(.$)))|((?<=Corequisite ).*?(?=\.|(.$)))|((?<=Corequisites ).*?(?=\.|(.$)))"
    prereqPattern = r"((?<=Prerequisites: ).*?(?=\.|(.$)))|((?<=Prerequisite: ).*?(?=(\.)|(.$)))|((?<=Prerequisite ).*?(?=\.|(.$)))|((?<=Prerequisites ).*?(?=\.|(.$)))"
    coreqs = re.search(coreqPattern, desc)
    prereqs = re.search(prereqPattern, desc)

    if coreqs and prereqs:
        parseReqs(prereqs.group(), node["title"], "R", data)
        parseReqs(coreqs.group(), node["title"], "C", data)
    elif prereqs:
        parseReqs(prereqs.group(), node["title"], "R", data)
    elif coreqs:
        parseReqs(coreqs.group(), node["title"], "C", data)

def generateNode(course, desc, data, colorMap, nodeIdCounter):
    if nodeIsInvalid(course, desc, data): return False
    
    subjectCodePattern = r".*(?= \d)"
    subject = re.search(subjectCodePattern, course["title"])

    color = colorMap[subject.group()]
    data["nodes"].append({ "id": nodeIdCounter, "title": course["title"], "desc": desc, "color": color})

    return True

def processData(scrapeData, colorMap, subjects) -> dict:
    # create new nodes and links
    data = {
        "nodes" : [],
        "links" : [],
        "subjects": subjects,
        "noLinks": [],
    }
    nodeIdCounter = 0

    for course in scrapeData:
        desc = re.sub(" {2,}", " ", course["desc"])
        success = generateNode(course, desc, data, colorMap, nodeIdCounter)
        if success:
            generateLinks(course, desc, data)
            nodeIdCounter += 1
    
    return data

def labelLinklessNodes(data) -> None:
    for node in data["nodes"]:
        linksThatTarget = [link for link in data["links"] if link["target"] == node["id"]]
        linksThatUse = [link for link in data["links"] if link["source"] == node["id"]]

        if len(linksThatTarget) == 0 and len(linksThatUse) == 0:
            data["noLinks"].append(node["title"])

def save(filePath, data):
    with open(filePath, "w") as outfile:
        json.dump(data, outfile)

def main():
    # print("Sending request")
    # scrapeRaw, subjects = scrape()

    with open("./cache/scrape-raw.json", "r") as file:
        scrapeRaw = json.load(file)
    with open("./cache/subjects.json", "r") as file:
        subjects = json.load(file)

    # TODO: Not enough color combs. Need to give multiple subjects same color. Can I do group them based on how close they are connected?
    print("Generating colors")
    colorMap = generateColors(subjects=subjects)
    # pprint(colorMap)

    print("Processing data")
    data = processData(scrapeRaw, colorMap, subjects)

    labelLinklessNodes(data)

    save("./courses.json", data)

if __name__ == "__main__":
    main()