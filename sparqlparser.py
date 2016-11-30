import re
import shlex
from rdfparser import detectPrefix, multiple_replace, prefixDict


# tripleList = []
# queryList = []

# variable usage dict will have each var with key:value, variable: lineNum+partOfTriple(s, p, or o)
variableUsageDict = {}
# The column names in the table in the database are subject (s), predicate (p), object (o)
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
        print("line", line)
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
            filterLine = (" ".join(parseLine).replace("(", "").replace(")", "")).split()
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
                print("part: " + part)

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
                    # print("prefixDict:", prefixDict)
                    # print("Parsing part: " + part)
                    tempTriple.append("<" + multiple_replace(prefixDict, part) + ">")

            # Append the parsed triple into a list of parsed triples
            parsedTriples.append(tempTriple)
        
        lineNum += 1

    print("\nThese are the parsed triples: ")
    for triple in parsedTriples:
        print(triple) 
    # print("\nPrefix dictionary")
    # print(prefixDict)
    print("\nVariable Usage Dictionary")
    print(variableUsageDict)
    print("\nThese are the variables in SELECT")
    print(selectedVariables)

def writeSQL():
    global prefixDict
    global variableUsageDict
    global parsedTriples
    global selectedVariables
    global lineNum
    global partsOfTriple
    SQLiteQuery = ""
    
    SQLiteQuery += "SELECT "
    # Go over the variables in SELECT and write them to the query
    # for var in selectedVariables:
    #     end = ", " if selectedVariables.index(var) != len(selectedVariables) - 1 else "\n"
    #     SQLiteQuery += var.replace("?", "") + end

    for var in selectedVariables:
        end = ", " if selectedVariables.index(var) != len(selectedVariables) - 1 else "\n"
        if selectedVariables == ["*"]:
            SQLiteQuery += "*" + "\n"
        else:
            SQLiteQuery += "t" + variableUsageDict[var][0][0] + "." + variableUsageDict[var][0][1] + " AS " + var.replace("?", "") + end 
    
    SQLiteQuery += "FROM "
    i = 1
    while i <= len(parsedTriples):
        end = "\n" if i == lineNum - 1 else ", "
        SQLiteQuery += "triples t" + str(i) + end
        i += 1

    # a string with all the and statements that go table.{s,p,o} = URI
    andStatements = "\n"
    belongsToTable = 1
    for triple in parsedTriples:
        for part in triple:
            # Skip any variables, only parsing literals and uris, variables are later
            if part.startswith("?"):
                continue
            end = "" if triple.index(part) == len(triple) else "\n"
            andStatements += "AND "
            andStatements += "t" + str(belongsToTable) + "." + partsOfTriple[triple.index(part)] + " = " + "\"" + part + "\"" + end
        
        belongsToTable += 1
    
    # print("\nThese are the and statements with URIs and literals")
    # print(andStatements)
    # print()

    # SQLiteQuery += "WHERE "
    whereStatement = True
    writtenVars = []
    for var in variableUsageDict:
        writtenVars.append(var)
        beginning = "WHERE " if whereStatement or var == variableUsageDict[var][-1] else "AND "
        endLine = "\n" if var not in writtenVars or whereStatement else ""
        whereStatement = False
        SQLiteQuery += beginning
        i = 0
        while i <= len(variableUsageDict[var]) - 1:
            # print(variableUsageDict[var][i])
            endVars = "" if i == len(variableUsageDict[var]) - 1 else "\n"
            if i == 0:
                firstEquals = "t" + variableUsageDict[var][i][0] + "." + variableUsageDict[var][i][1]
            else: 
                if (i >= 2):
                    SQLiteQuery += "AND "
                SQLiteQuery += firstEquals + " = " + "t" + variableUsageDict[var][i][0] + "." + variableUsageDict[var][i][1] + endVars
            i += 1 
        SQLiteQuery += endLine
        # if len(variableUsageDict[var]) > 1:
        #     for usage in variableUsageDict[var]:
        #         end = "\n" if variableUsageDict[var].index(usage) == len(variableUsageDict[var]) - 1 else " "
        #         SQLiteQuery += 

        #         end = "\n" if variableUsageDict[var].index(equalsUsage) == len(variableUsageDict[var]) - 1 else ""
        #         SQLiteQuery += "t" + usage[0] + "." + usage[1] + " = " + "t" + equalsUsage[0] + "." + equalsUsage[1] + end

    SQLiteQuery += andStatements

    print("This is the filter line: ")
    print(filterLine)

    
    mathFilterSymbols = ["<", ">", "=", "<=", ">="]
    for symbol in mathFilterSymbols:
        if symbol in filterLine:
            SQLiteQuery += "AND "
            # identifier = 
            SQLiteQuery += "t" + variableUsageDict[filterLine[filterLine.index(symbol) - 1]][0].replace("?", "") + "." + " " + symbol + " " + filterLine[filterLine.index(symbol) + 1]


    SQLiteQuery += ";"
    return SQLiteQuery
    








