import os.path
import sys
import rdfparser

def main():
    print()
    
    # Check that there are an appropriate amount of command line args.
    if len( sys.argv ) != 3:
        print( "Error: missing or too many arguments" )
        print( "Usage: python3 q8.py dbPath rdfPath" )
        exit(1)
        
    # Get the command line arguments
    dbPath = sys.argv[1]
    rdfPath = sys.argv[2]
    
    # Check that the dbPath exists
    if not os.path.exists( dbPath ):
        print( "Error: file not found: \"" + dbPath + "\"" )
        print( "Message: The database was not found, are you sure you wrote the correct file path?" )
        exit(1)
      
    # Check that the rdfPath exists
    if not os.path.exists( rdfPath ):
        print( "Error: file not found: \"" + rdfPath + "\"" )
        print( "Message: The file of RDF triples was not found, are you sure you wrote the correct file path?" )
        exit(1)
        
    # Create a file object and pass it into the 
    rdfFile = open( rdfPath, 'r' )
    parsedFile = rdfparser.parseRDF( rdfFile )
     
main()