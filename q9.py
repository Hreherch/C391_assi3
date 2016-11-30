import os.path
import sys
import sparqlparser

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
    SQLqueryString = sparqlparser.parseSPARQL(SPARQLqueryFile)



main()