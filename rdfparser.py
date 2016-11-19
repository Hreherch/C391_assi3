import re
import shlex

prefixDict = {}

# http://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex-in-python
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def parseRDF( rdfFile ):
    global prefixDict
    lineNum = 0
    for line in rdfFile:
        lineNum += 1 
        line = line
        
        # Check if the line defines a prefix
        if re.match( "@prefix", line, re.IGNORECASE ):
            # Use regex to group the values and store them as a key:value pair
            matchObj = re.match( ".* (.*:).*<(.*)> .", line )
            if matchObj:
                key = matchObj.group(1) 
                value = matchObj.group(2) 
                if key in prefixDict:
                    # If the prefix is already defined, print a warning
                    print( "Warning: prefix redefined on line", lineNum )
                prefixDict[key] = value
            else:
                # if we reach here we failed to match the expected prefix format.
                print( "Error: prefix match failure on line", lineNum )
                exit(1)
            continue; # Continue to the next line
        
        line = multiple_replace(prefixDict, line)
        
        split = shlex.split(line) 
        
        # ?obj ?pred ?subject ?operation
        
        # Comma is list value, keep object and pred, prepare for new ?subject ?op
        
        # Semicolon is keep object but prepare for new ?pred ?subject ?op
        
        
    #print( prefixDict )