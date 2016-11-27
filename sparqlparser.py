import re
import shlex
from rdfparser import detectPrefix, multiple_replace, prefixDict


prefixDict = {}
# tripleList = []
# queryList = []

# variable usage dict will have each var with key:value, variable: lineNum+partOfTriple(s, p, or o)
variableUsageDict = {}
partsOfTriple = ["s", "p", "o"]
parsedTriples = []
selectedVariables = []
filterLine = []
lineNum = 0

def parseSPARQL(SPARQLfile):
    global prefixDict
    global variableUsageDict
    global parsedTriples
    global selectedVariables
    global filterLine
    global lineNum

    lineNum = 0
    for line in SPARQLfile:
        # Check for prefixes
        if detectPrefix(line, 0):
            continue
        
        # Split the lines
        parseLine = line.split()
        
        # If the line is just whitespace, skip it
        if parseLine == []:
            continue
        
        # If the line is the SELEECT statement
        elif parseLine[0] == "SELECT":
            selectLine = parseLine

            # Find the variables in the string of the select statement
            matchObj = re.match("SELECT (.*) WHERE {", " ".join(selectLine))

            # If any matches were made, set the global variables to be the list of variables found
            if matchObj:
                variables = matchObj.group(1)
                selectedVariables = variables.split();

            # lineNum represents the amount of triples after the select statement
            lineNum = 1
            continue

        # If the line is FILTER
        elif parseLine[0] == "FILTER":
            filterLine = parseLine
            continue

        # Skip the closing bracket line
        elif parseLine[0] == "}":
            continue 
             
        # Otherwise, the line is a triple
        else:

            # A temp triple, we will append to it the parsed parts of the triple
            tempTriple = []

            # Iterate over each part (subject predicate object) of the triple
            for part in parseLine:

                # If the part starts with a ? it is a variable
                if part.startswith("?"):
                    variable = part

                    # If this variable is not found in the usage dictionary 
                    if variable not in variableUsageDict:
                        variableUsageDict[variable] = []
                        
                    # If it is, append another usage
                    variableUsageDict[variable].append(str(lineNum) + partsOfTriple[parseLine.index(part)])
                    tempTriple.append(part)
                    
                # If the part starts with a " it is a literal
                elif part[0] == '"':
                    tempTriple.append(part.strip('"'))

                # The period siginifies the end of a triple
                elif part == ".":
                    break

                # Otherwise it is a prefix with a value, replace it with its full URI
                else:
                    # print("Parsing part: " + part)
                    tempTriple.append("<" + multiple_replace(prefixDict, part) + ">")

            # Append the parsed triple into a list of parsed triples
            parsedTriples.append(tempTriple)
        
        lineNum += 1

    # print("\nThese are the parsed triples: ")
    # for triple in parsedTriples:
    #     print(triple) 
    # print("\nPrefix dictionary")
    # print(prefixDict)
    # print("\nVariable Usage Dictionary")
    # print(variableUsageDict)

def writeSQL:
    global prefixDict
    global variableUsageDict
    global parsedTriples
    global selectedVariables
    global lineNum







