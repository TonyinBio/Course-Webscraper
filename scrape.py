import requests
from bs4 import BeautifulSoup
import json
import re

import seaborn as sns

from pprint import pprint

# # read the subjects of interest
# with open("./subjects.txt", "r") as file:
#     SUBJECTS = [subject.strip() for subject in file.readlines()]

def generateColors(subjects, palette: str = "husl") -> dict:
    """
    Assign rgb values scaled to 255 for each subject in SUBJECTS
        palette: name of seaborn palette

        return: key=subjectName, value=rgb
    """
    colors = sns.color_palette(palette, len(subjects))
    formattedColors = ["rgb" + str(tuple(int(color)*255 for color in rgb)) for rgb in colors]
    return dict(zip(subjects, formattedColors))

def getNodes(URL: str) -> list[dict]:
    """
    Scan the specific subject for all classes
        URL: URL to subject page

        return: list of classes with associated description
    """
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    results = soup.find_all("div", class_="course first")

    scrapeData = []
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

    return scrapeData

def generateSubjectList(subjectTags: list) -> list:
    subjects = []
    subjectCodePattern = r"^[A-Z ]+"
    for tag in subjectTags:
        subjectCode = re.search(subjectCodePattern, tag.text.strip()).group().strip()
        subjects.append(subjectCode)

    return subjects

def getSubjects(baseUrl: str) -> tuple[list[str], list[str]]:
    """
    Looks on the course catalogue for all subjects of interest
        baseUrl: course catalgoue URL

        return: list of URLs to subject webpages
    """
    page = requests.get(baseUrl)
    soup = BeautifulSoup(page.content, "html.parser")
    subjectTags = soup.find_all("a", class_="d-block")
    urls = [baseUrl + re.search(r"(?<=\/)\w+$", tag["href"]).group() for tag in subjectTags]
    
    subjects = generateSubjectList(subjectTags)

    return urls, subjects

def scrape() -> list:
    """
    Scrape courses
        return: list of classes (across subjects of interest) with associated description
    """
    catalogueUrl = "https://apps.ualberta.ca/catalogue/course/"
    urls, subjects = getSubjects(catalogueUrl)

    scrapeRaw = []
    for url in urls:
        scrapeRaw.extend(getNodes(url))
    
    # saving raw for testing
    with open("./cache/scrape-raw.json", "w") as file:
        json.dump(scrapeRaw, file)
    with open("./cache/subjects.json", "w") as file:
        json.dump(subjects, file)

    return scrapeRaw, subjects


if __name__ == "__main__":
    scrape()