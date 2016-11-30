import os.path
import sys
from sparqlparser import parseSPARQL, writeSQL 
import sqlite3

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
    SQLparsedQuery = writeSQL()
    print(SQLparsedQuery)

    # conn = sqlite3.connect(dbPath)
    # curs = conn.cursor
    # curs.execute(SQLparsedQuery)
    # result = curs.fetchall()
    # for row in result:
    #     print(row)



main()