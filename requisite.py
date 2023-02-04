import re

def toUpper(matchObj):
    return matchObj.group().upper()

def isInvalid(req):
    #Check if string has a 3 digit number
    if re.search("\d{3}", req) == None:
        # print("Skipping: " + req)
        return True

    return False

def deduceCourseCode(num, index, parentArray, grandParentI = None, grandParentArray = None) -> str:
    siblingReq = None
    subjectCodePattern = r"(?<![^A-Z ])[A-Z ]+(?= \d{3})"
    while siblingReq == None and index > 0:
        siblingReq = re.search(subjectCodePattern, parentArray[index - 1])
        if siblingReq: 
            siblingReq = siblingReq.group()
        index -= 1

    while siblingReq == None:
        matches = re.findall(subjectCodePattern, grandParentArray[grandParentI - 1])
        if len(matches) > 0:
            siblingReq = matches[-1]
        grandParentI -= 1

    return siblingReq + " " + num

def parseReqs(string, target, reqType, data):
    """
        reqType: "r" - requisite, "c" - corequisite    
    """
    #split string based on different courses
    ##TODO: A and B get equal treatment PHYSL 210A vs B

    # group requisites based on if they are equivalent
    requisitePattern = r"(?:(?:;)? and )|; "
    reqArray = re.split(requisitePattern, string)
    for reqI, req in enumerate(reqArray):
        if isInvalid(req): continue

        #Check if a string has a 3 digit number at the beginning
        if re.search("^\d{3}(?!-| level)", req):
            # print(target, req, reqArray)
            req = deduceCourseCode(req, reqI, reqArray, 1, [target])

        #Check if a string has been spelt without uppercase by accident...
        req = re.sub("[A-Z][a-z]\w+", toUpper, req)

        #Find course codes by looking for all caps followed by a 3 digit number
        duplicates = re.findall("(?:(?<![^A-Z (])[A-Z ]+ \d{3})(?!-| level)|(?:\d{3})(?!-| level)", req)

        if len(duplicates) > 1:
            #assign special link
            
            for dupI, dup in enumerate(duplicates):
                if re.search("^\d{3}", dup):
                    # print(dup, duplicates, reqArray)
                    duplicates[dupI] = deduceCourseCode(dup, dupI, duplicates, reqI, reqArray)

                source = duplicates[dupI]
                if dupI > 0:
                    data["links"].append({ "source": source, "target": target, "type": "multi" + reqType, "duplicate": True})
                else:
                    data["links"].append({ "source": source, "target": target, "type": "multi" + reqType})
            # source = duplicates[0]

            # for dup in duplicates:
            #     matches = [node["title"] for node in data["nodes"] if node["title"] == dup]
            #     if len(matches) > 0:
            #         source = dup
            #         break

            # data["links"].append({ "source": source, "target": target, "type": "multi" + reqType})

        elif len(duplicates) == 1:
            #assign normal link
            source = duplicates[0]
            data["links"].append({ "source": source, "target": target, "type": "norm" + reqType})
            
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
                    data["links"].append({ "source": source[0], "target": target, "type": "multi" + reqType})
                else:
                    valid = False
                    print("**Invalid entry**")


