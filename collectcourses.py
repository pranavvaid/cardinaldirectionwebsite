import requests
import xmltodict
from datetime import datetime
import time
from stanfordclasses import StanfordClass
import pickle
import os

BASEURL = "https://explorecourses.stanford.edu/"
DEPARTMENTURLMODIFER = "?view=xml-20140630"
COURSEURLMODIFIER = "search?view=xml-20140630&academicYear=&q={DEPARTMENT}&filter-departmentcode-{DEPARTMENT}=on&filter-coursestatus-Active=on"
numDirectCourseRelations = 0
numIndirectCourseRelations = 0

# This function retrieves the all departments
def retrieveDepartments():
    allDepartments = []
    r = requests.get(BASEURL+DEPARTMENTURLMODIFER)
    courseDictionary = xmltodict.parse(r.text, force_list = ('school', 'department'))
    for school in courseDictionary['schools']['school']:
        for department in school['department']:
            currentDepartment = {
                'name': department['@name'],
                'longname' : department['@longname'],
                'school' : school['@name']
            }
            allDepartments.append(currentDepartment)
    return allDepartments

def retrieveDepartmentCourses(departmentName):
    departmentCourseModifier = COURSEURLMODIFIER.format(DEPARTMENT=departmentName)
    r = requests.get(BASEURL+departmentCourseModifier)
    entireCourseData = xmltodict.parse(r.text, force_list = ('course'))
    importantCourseData = []
    if entireCourseData['xml']['courses'] is None:
        return importantCourseData
    for course in entireCourseData['xml']['courses']['course']:
        importantData = {key:course[key] for key in course.keys() & {'title', 'description', 'unitsMin', 'unitsMax', 'subject', 'code'}}
        importantCourseData.append(importantData)
    return importantCourseData

def findPrerequisiteString(courseDescription):
    if courseDescription is None:
        return ""
    preReqKeyPhrases = ["Prerequisites", "Prerequisite", "Pre-requisite", "Prerequsite"]
    keyPhraseLen = 0
    for keyPhrase in preReqKeyPhrases:
        prereqIndex = courseDescription.find(keyPhrase)
        if prereqIndex != -1:
            keyPhraseLen = len(keyPhrase)
            break
    if prereqIndex == -1:
        return ""
    endPrereqIndex = courseDescription.find(".", prereqIndex)
    if endPrereqIndex != -1:
        prerequisiteString = courseDescription[prereqIndex+keyPhraseLen:endPrereqIndex]
    else:
        prerequisiteString = courseDescription[prereqIndex+keyPhraseLen:]
    return prerequisiteString


def extractClassNames(str, departmentCode, allDepartments):
    if str is None:
        return
    latestDepartment = departmentCode
    currentlyBuildingDepartment = False
    latestNumber = ""
    currentlyBuildingNumber = False
    allClasses = [];
    i = 0
    while i < len(str):
        if str[i].isdigit():
            if not currentlyBuildingNumber:
                latestNumber = str[i]
                currentlyBuildingNumber = True
            else:
                latestNumber+=str[i]
            if i+1 == len(str):
                newClass = latestDepartment + " " + latestNumber
                if newClass not in allClasses:
                    allClasses.append(newClass)
        else:
            if currentlyBuildingNumber:
                # Some courses might have a number in their code
                for j in range (i, len(str)):
                    if str[j].isalpha():
                        latestNumber += str[j]
                    else:
                        i = j-1
                        break
                newClass = latestDepartment + " " + latestNumber
                if newClass not in allClasses:
                    allClasses.append(newClass)
            currentlyBuildingNumber = False
        
        if str[i].isupper():
            newDepartmentName = ""
            nameToCodeConversion = ""
            for d in allDepartments:
                possDepCode = d['name']
                possDepFullName = d['longname']
                if len(possDepCode) > len(newDepartmentName) and i+len(possDepCode) <= len(str) and str[i:i+len(possDepCode)].upper() == possDepCode.upper():
                    newDepartmentName = possDepCode
                    nameToCodeConversion = ""
                if len(possDepFullName) > len(newDepartmentName) and i+len(possDepFullName) <= len(str) and str[i:i+len(possDepFullName)].upper() == possDepFullName.upper():
                    newDepartmentName = possDepFullName
                    nameToCodeConversion = possDepCode
            if newDepartmentName != "":
                i = i + len(newDepartmentName) - 1
                if nameToCodeConversion != "":
                    latestDepartment = nameToCodeConversion
                else:
                    latestDepartment = newDepartmentName
                
        i = i + 1
    return allClasses

def findAllCourses(departmentNames):
    allCourses = []
    for department in departmentNames:
        print("RETRIEVING DEPARTMENT COURSES FOR " + department['name'] + " AT " + datetime.now().strftime('%H:%M:%S'))
        toAdd = retrieveDepartmentCourses(department['name'])
        if toAdd is not None:
            allCourses.extend(toAdd)
    return allCourses

def createCourseMap(allCourses, allDepartments):
    StanfordClassList = []
    allClassTitles = set([c['subject'] + " " + c['code'] for c in allCourses])
    usedClassTitles = set([])
    # For each course
    for course in allCourses:
        preReqString = findPrerequisiteString(course['description'])
        preReqClasses = extractClassNames(preReqString, course['subject'], allDepartments)
        currentCourse = next((x for x in StanfordClassList if x.name == course['subject'] + " " + course['code']), None)
        # If there is no course currently in the list with this course's name create a new course, otherwise just update the variables of the existing course
        if currentCourse is None:
            currentCourse = StanfordClass(course['title'], course['description'], course['unitsMin'], course['unitsMax'], course['subject'] + " " + course['code'], [], [])
        else:
            currentCourse.title = course['title']
            currentCourse.description = course['description']
            currentCourse.minUnits = course['unitsMin']
            currentCourse.maxUnits = course['unitsMax']
        # For each prequisite class for this course
        for preReq in preReqClasses:
            # If the detected prereq isn't a valid class, then ignore it
            if preReq not in allClassTitles:
                continue
            # Find if a class object has already been created for this prereq
            preReqClassObject = next((x for x in StanfordClassList if x.name == preReq), None)
            if preReqClassObject is None:
                preReqClassObject = StanfordClass("TEMPHOLDER", "TEMPHOLDER", -1, -1, preReq, [], [])
                StanfordClassList.append(preReqClassObject)
            global numDirectCourseRelations
            global numIndirectCourseRelations
            numDirectCourseRelations = numDirectCourseRelations + 2
            numIndirectCourseRelations = numIndirectCourseRelations + 2 + len(preReqClassObject.prerequisites)
            preReqClassObject.prereqsOf.append(currentCourse)
            currentCourse.prerequisites.append(preReqClassObject)
        StanfordClassList.append(currentCourse)
    return StanfordClassList


print("RETRIEVING DEPARTMENTS")
allDepartments = retrieveDepartments()
allCourses = findAllCourses(allDepartments)

parseStartTime = time.time()
StanfordClassList = createCourseMap(allCourses, allDepartments)
totalTime = time.time()-parseStartTime
print("COURSE EXTRACTION AND TEXT PROCESSING COMPLETE")
print("Processed the text of " + str(len(allCourses)) + " course descriptions and discovered " + str(numDirectCourseRelations) + " direct relationships and " + str(numIndirectCourseRelations) + " indirect relationships between courses in " + str(totalTime) + " seconds!.")

file1 = open('/pickles/alldepartments.txt', 'w')
for currentDepartment in allDepartments:
    file1.write(currentDepartment['name'] + "\n")
file1.close()


with open('/pickles/stanfordclasslist.pkl', 'wb') as f:
    pickle.dump(StanfordClassList, f)

f.close()

