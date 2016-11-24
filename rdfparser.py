import re
import shlex

prefixDict = {}
tripleList = []

'''
rdfparser handles triples using a state machine on whitespace separated elements of a .ttl file.

Currently handles:
    Basic prefix mapping 

'''

def createRDFtuple( curSubject, curPredicate, curObject ):
    global tripleList
    tripleList.append( ["<" + curSubject + ">", 
                        "<" + curPredicate + ">",
                        "<" + curObject + ">"] )
    print( "NEW TRIPLE:", tripleList[-1] )

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
        
        print( "\n" * 3 )
        
        print( "LINE:", line )
        
        ''' DO WE NEED TO CONSIDER COMMENT LINES? '''
        
        # Check if the line defines a prefix
        if re.match( "@prefix", line, re.IGNORECASE ):
            # Use regex to group the values and store them as a key:value pair
            matchObj = re.match( "@prefix ?([^_]*:).*<(.*)> .", line )
            if matchObj:
                key = matchObj.group(1) 
                value = matchObj.group(2) 
                if key in prefixDict:
                    # If the prefix is already defined, print a warning
                    print( "Warning: prefix redefined on line", lineNum )
                print( "PREFIX ADDED key:", key, "value:", value )
                prefixDict[key] = value
            else:
                # if we reach here we failed to match the expected prefix format.
                print( "Error: prefix match failure on line", lineNum )
                exit(1)
            continue; # Continue to the next line
        
        line = multiple_replace(prefixDict, line)
        
        split = shlex.split(line) 
        print( "SPLIT: ", split )
        
        for elem in split:
            tripleStateMachine( elem, lineNum )
    
    # print out some statistics about the parsing.
    global tripleList
    print( "found", len(tripleList), "triples, and", len( prefixDict), "prefixes" )
    print( "file had", lineNum, "lines" )
    print( "potentially missed:", len(tripleList) + len(prefixDict) - lineNum )
        
# curState = The last read element (hence we start on 0)
STATE_SUBJECT = 1
STATE_PREDICATE = 2
STATE_OBJECT = 3
STATE_COMMA = 4
STATE_PERIOD = 5
STATE_SEMICOLON = 6
curState = STATE_PERIOD
curSub = ""
curPred = ""
curObj = ""
def tripleStateMachine( currentElem, lineNum ):
    global curState, STATE_SUBJECT, STATE_PREDICATE, STATE_OBJECT, STATE_COMMA
    global STATE_PERIOD, STATE_SEMICOLON, curSub, curPred, curObj
    
    # initial state or after a period 
    if curState == STATE_PERIOD:
        checkForEnding( currentElem, lineNum )
        curSub = currentElem
        curState = STATE_SUBJECT
    
    # last saw a subject, looking for predicate
    elif curState == STATE_SUBJECT or curState == STATE_SEMICOLON:
        checkForEnding( currentElem, lineNum )
        if currentElem == "a":
            curPred = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        else:
            curPred = currentElem
        curState = STATE_PREDICATE
        
    # last saw a predicate, looking for an object
    elif curState == STATE_PREDICATE or curState == STATE_COMMA:
        checkForEnding( currentElem, lineNum )
        curObj = currentElem
        createRDFtuple( curSub, curPred, curObj )
        curState = STATE_OBJECT
    
    # Saw an object, looking for [.|,|;]
    elif curState == STATE_OBJECT:
        if currentElem == ".":
            curState = STATE_PERIOD
        elif currentElem == ",":
            curState = STATE_COMMA
        elif currentElem == ";":
            curState = STATE_SEMICOLON
        else:
            print( "Unexpected element", currentElem, "on line", lineNum )
            print( "Was expecting: [.|,|;]" )
            exit(1)

# Terminates the program if the element if one of [.|;|,]
def checkForEnding( elem, lineNum ):
    if elem == ".":
        val = True
    elif elem == ",":
        val = True
    elif elem == ";":
        val = True
    else:
        val = False
        
    if val:
        print( "Unexpected ending character on line", lineNum )
        exit()

''' >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> '''
        
# gave up :(
def parseRDFold( rdfFile ):
    global prefixDict
    curSubject = ""
    curPredicate = ""
    curMode ="."
    lineNum = 0
    for line in rdfFile:
        lineNum += 1 
        
        print( "PROCESSING:", line )
        
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
        print( "SPLIT:", split )
        
        # check valid state transitions  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        
        # check that the line ending is valid.
        if ( split[-1] != "." ) and ( split[-1] != "," ) and ( split[-1] != ";" ):
            print( "Error: Illegal line ending \"" + split[-1] + "\" on line", lineNum )
            exit(1)
        
        # If this line comes after a "."
        if ( curMode == "." ):
            # There must be a "?subject ?predicate ?object [.|,|;]"
            if ( len(split) < 4 ):
                print( "Error, missing subject, predicate, or object on line", lineNum )
                exit(1)
                
            curSubject = split[0]
            curPredicate = split[1]
            
            createRDFtuple( curSubject, curPredicate, split[2] )
            curMode = split[3]
            continue;
                
            
        
        # curMode = "."
        # ?sub ?pred ?obj [.|,|;]
        
        
        # curMode = ","
        # ?obj [.|,]
        
        
        # curMode = ";"
        # ?pred ?obj [;|.]
        
        # Comma is list value, keep object and pred, prepare for new ?subject ?op
        
        # Semicolon is keep object but prepare for new ?pred ?subject ?op
        
        print( "COULD NOT PROCESS:", split )
        
        curMode = split[-1]
        
    