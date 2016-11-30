import os.path
import sys
from sparqlparser import parseSPARQL, writeSQL, variableUsageDict, getTValue
import sqlite3
import re
# returns (boolean, value) of a converted string to a number 
# The bool represents if the conversion was successful
def getNumeric( string ):
    try:
        value, int( string )
        return True, value
    except:
        pass # do nothing
        
    try:
        value = float( string )
        return True, value
    except:
        return False, string
        
def switchCond( var1, cond, var2 ):
    if cond == "=":
        return var1 == var2
    elif cond == ">":
        return var1 > var2
    elif cond == "<":
        return var1 < var2
    elif cond == "<=":
        return var1 <= var2
    elif cond == ">=":
        return var1 >= var2
    elif cond == "!=":
        return var1 != var2
    

def filterFunc(var1, operator, var2):
    if operator == "REGEX":
        if re.search(var2, var1):
            return 1
        else: 
            return 0
    
    isNum1, val1 = getNumeric( var1 )
    isNum2, val2 = getNumeric( var2 )
    
    if (isNum1 and isNum2):
        return switchCond( val1, operator, val2 )
    else:
        return switchCond( var1, operator, var2)

def main():
    if len(sys.argv) != 3:
        print("Missing or too many arguments:")
        print("Usage: python3 q9.py dbPath queryPath")

    # Get command line args
    dbPath = sys.argv[1]
    queryPath = sys.argv[2]

    # Check that dbPath exists
    if not os.path.exists(dbPath):
        print("Error: file not found: \"" + dbPath + "\"")
        exit(1)
    
    # Check that queryPath exists
    if not os.path.exists(queryPath):
        print("Error: file not found: \"" + queryPath + "\"")
        exit(1)

    # Read in the query in queryPath as a string
    SPARQLqueryFile = open(queryPath, "r")
    # queryString = ""
    # for line in SPARQLqueryFile:
    #     queryString += line
    # print(queryString)
    SQLqueryString = parseSPARQL(SPARQLqueryFile)
    SQLparsedQuery = writeSQL(dbPath)
    print(SQLparsedQuery)

    conn = sqlite3.connect(dbPath)
    conn.create_function("FILTER", 3, filterFunc)
    curs = conn.cursor()
    curs.execute(SQLparsedQuery)
    result = curs.fetchall()
    print("\nResults")
    for row in result:
        print(row)




main()