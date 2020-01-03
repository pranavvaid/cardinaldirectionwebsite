from stanfordclasses import StanfordClass
import pickle

def retrieveClass(classlist, classTitle = "", className = ""):
    if className != "":
        className = className.replace(" ", "")
        return next((x for x in classlist if x.name.upper().replace(" ", "") == className.upper()), None)
    if classTitle != "":
        return next((x for x in classlist if x.title.upper() == classTitle.upper()), None)
    return None


def list_contains(sublist, mainlist):
    if all(x in mainlist for x in sublist):
        return True
    return False

def determineFutureClasses(completedClassesList, StanfordClassList):
    possibleFutureClasses = set([])
    for completedClass in completedClassesList:
        classToCheck = retrieveClass(StanfordClassList, className = completedClass)
        if classToCheck is not None:
            possibleFutureClasses.update(classToCheck.prereqsOf)
    actualFutureClasses = set([])
    for possibleFutureClass in possibleFutureClasses:
        preReqsOfFutureClass = possibleFutureClass.prerequisites
        if list_contains([c.name for c in preReqsOfFutureClass], completedClassesList):
            actualFutureClasses.add(possibleFutureClass)
    return actualFutureClasses

def determineAllNonPrerequisiteCourses(StanfordClassList):
    futureClasses = set([])
    for possibleClass in StanfordClassList:
        if len(possibleClass.prerequisites) == 0:
            futureClasses.add(possibleClass)
    return futureClasses

def determineAllRequiredPrerequisites(classToDetermine):
    allRequiredClasses = set([])
    if (classToDetermine.prerequisites is None) or len(classToDetermine.prerequisites) == 0 :
        return allRequiredClasses
    for preReqCourse in classToDetermine.prerequisites:
        allRequiredClasses.add(preReqCourse)
        allRequiredClasses.update(determineAllRequiredPrerequisites(preReqCourse))
    return allRequiredClasses

with open('stanfordclasslist.pkl', 'rb') as f:
    StanfordClassList = pickle.load(f)
f.close()

print("")
print("")
print("")
print("WELCOME TO CARDINAL DIRECTION, LET'S HELP YOU FIND WHAT PATHS YOUR COURSES CAN TAKE YOU!")
print("-------------------------------------------------------------------------------------------------------------------------")
while True:
    print("=============================================================================")
    print("What would you like to do?")
    print("1: Retrieve path information about a course.")
    print("2: Help me find what courses I can take.")
    print("3: I'd like to know all the classes I have to take before a certain course")
    print("4: Print out course catalog with path information")
    print("5: Show me all courses with no required prequisites")
    print("6: Quit program")
    print("=============================================================================")
    userChoice = input("Choose an option: ")
    print("")
    if userChoice == "1":
        print("What course would you like to learn more about? Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter course: ")
        classData = retrieveClass(StanfordClassList, className = courseChoice)
        if classData is None:
            classData = retrieveClass(StanfordClassList, classTitle = courseChoice)
        if classData is None:
            print("Oops!! That course isn't offered at Stanford")
        else:
            print("")
            print("")
            classData.printOutCourse()
    elif userChoice == "2":
        userClasses = []
        print("Let's help you out! Enter all the courses you have completed so far. When you are done entering courses, type \"DONE\" or press enter")
        print("Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter a course: ")
        while (courseChoice.upper() != "DONE" and courseChoice != ""):
            userClasses.append(courseChoice.upper())
            courseChoice = input("Enter a course: ")
        allPossibleClasses = determineFutureClasses(userClasses, StanfordClassList)
        print("")
        print("Here are the classes that you have acquired the prerequisites for! (note: this doesn't include courses with no prereqs)")
        print("-------------------------------------------------------------------------------------------------------------------------")
        for possibleClass in allPossibleClasses:
            print(possibleClass.name + ": " + possibleClass.title)
    elif userChoice == "3":
        print("For what course would you like to know ALL the classes you must take prior to it? Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter course: ")
        classToDetermine = retrieveClass(StanfordClassList, className = courseChoice)
        if classToDetermine is None:
            classToDetermine = retrieveClass(StanfordClassList, classTitle = courseChoice)
        if classToDetermine is None:
            print("Oops!! That course isn't offered at Stanford")
        else:
            print("")
            print("")
            allPreReqs = determineAllRequiredPrerequisites(classToDetermine)
            print("")
            print("Here are all the classes you must take before you may take " + classToDetermine.name)
            print("Warning: some courses may be equivalent courses, and only one needs to be taken")
            print("-------------------------------------------------------------------------------------------------------------------------")
            for requiredClass in allPreReqs:
                print(requiredClass.name + ": " + requiredClass.title)
    elif userChoice == "4":
        for course in StanfordClassList:
            print("")
            print("----------------------------------------------------------------")
            course.printOutCourse()
    elif userChoice == "5":
        nonreqs = determineAllNonPrerequisiteCourses(StanfordClassList)
        for possibleClass in nonreqs:
            print(possibleClass.name + ": " + possibleClass.title)
        print("")
        print("")
        print("Above is a list of all courses that have no prerequisites!")
    elif userChoice == "6":
        break
    else:
        print("Sorry, that's not an option :/")
    print("  ")
    print("")
