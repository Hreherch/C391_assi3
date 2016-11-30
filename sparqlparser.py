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

# modifies the use of the 
def getSQLFilter( filterLine ):
    print( "testing filter", filterLine )
    if filterLine == []:
        return ""
    
    matchObj = re.search( '\(regex\((.*),(.*)\)\)', filterLine, re.IGNORECASE )
    if matchObj:
        string = matchObj.group(1)
        pattern = matchObj.group(2)
        print( string, pattern )
        return ( "FILTER( '" + string + "', 'REGEX', '" + pattern + "' )")
    
    matchObj = re.search( '\((.*)([=|>|<|<=|>=])(.*)\)', filterLine, re.IGNORECASE )
    if matchObj:
        val1 = matchObj.group(1)
        val2 = matchObj.group(2)
        val3 = matchObj.group(3)
        print( val1, val2, val3 )
        return( "FILTER( '" + val1.strip() + "', '" + val2 + "', '" + val3.strip() + "' )" )


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
        
        # If the WHERE clause is found on a new line rather than with the SELECT
        elif parseLine[0] == "WHERE":
            lineNum = 1
            continue
            print("Here")

        # If the line is FILTER
        elif parseLine[0] == "FILTER":
            print( parseLine )
            filterLine = " ".join( parseLine )
            print( filterLine )
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
    
# returns something like "t1.s" based on the input
def getTValue( str ):
    return "t" + str[0] + "." + str[1]
    
# returns something like "t1.s = t2.o" based on input
def getEquality( str1, str2 ):
    return getTValue(str1) + " = " + getTValue(str2)
    
# assuming the list is >= 2 elements, returns a full conditional statement 
# to relate the elements of variableUsageDict[key]
# returns something like "t1.s = t2.o AND t2.o = t4.s ..."
# Q for question-mark like in ?city
def getQConds( key, variableUsageDict ):
    value = ""
    list = variableUsageDict[key]
    size = len(list)
    for index in range(size-1):
        value += getEquality( list[index], list[index + 1]) 
        if index+1 != size-1:
            value += " AND "
    return value
        
        

def writeSQL(dbPath):
    global prefixDict
    global variableUsageDict
    global parsedTriples
    global selectedVariables
    global lineNum
    global partsOfTriple
    SQLiteQuery = ""
    
    # The SELECT clause
    SQLiteQuery += "SELECT "
    # Go over the variables in SELECT and write them to the query
    for var in selectedVariables:
        end = ", " if selectedVariables.index(var) != len(selectedVariables) - 1 else "\n"
        if selectedVariables == ["*"]:
            SQLiteQuery += "*" + "\n"
        # Place the specifier tx.{s,p,o} and rename it to be the same as in SPARQL
        else:
            SQLiteQuery += "t" + variableUsageDict[var][0][0] + "." + variableUsageDict[var][0][1] + " AS " + var.replace("?", "") + end
    
    # The FROM clause
    SQLiteQuery += "FROM "
    i = 1
    # There are as many joined tables as there are lines
    while i <= len(parsedTriples):
        end = "\n" if i == lineNum - 1 else ", "
        SQLiteQuery += "Triples t" + str(i) + end
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
            andStatements += "t" + str(belongsToTable) + "." + partsOfTriple[triple.index(part)] + " = " + "'" + part + "'" + end
        
        belongsToTable += 1
    
    # > > RELATE THE ?VARS < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < 
    SQLiteQuery += "WHERE "     # begin the WHERE
    conditionalLine = ""        # start a independent string for variable equality
    for key in variableUsageDict:
        # if the list is len <= 1, then we don't need to relate any elements
        if len(variableUsageDict[key]) <= 1:
            continue
            
        # if the line is empty so far, and the current variable has equality needed
        if conditionalLine == "":
            conditionalLine += getQConds( key, variableUsageDict ) + "\n"
        
        # ("AND " b/c line is not empty)
        elif conditionalLine != "":
            conditionalLine += "AND " + getQConds( key, variableUsageDict ) + "\n"

    SQLiteQuery += conditionalLine # add the relational lines to the query.
     
    # remove annoying newline after the variable relations
    if SQLiteQuery[-1] == '\n':
        SQLiteQuery += '\b'
     
    # append the and statements parsed earlier
    SQLiteQuery += andStatements

    # If any matching symbols were contained in the filter, it was a comparison filter
    SQLiteQuery += getSQLFilter( filterLine )

    # Don't forget the semicolon
    SQLiteQuery += ";"

    return SQLiteQuery
    








