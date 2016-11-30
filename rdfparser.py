# Copyright 2016 Kieter Philip L. Balisnomo, Bennett Hreherchuk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

''' INFO
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    rdfparser 
    
    See the README for expected input. 
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
'''

import re 
import shlex   
from urllib.parse import urlparse

# A dictionary that maps "prefixKey:" to "URIvalue"
prefixDict = {}

# each element in tripleList is a three element array containing a RDF triple
tripleList = []

def createRDFtuple( curSubject, curPredicate, curObject ):
    global tripleList
    tripleList.append( [ curSubject, 
                         curPredicate,
                         curObject ] )

# http://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex-in-python
def multiple_replace(dict, text):
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 
    
def numericString( string ):
    try:
        int( string )
        return True
    except:
        pass # do nothing
        
    try:
        float( string )
        return True
    except:
        return False
    
# Takes a string that represents a triple element and tries to convert it to <URI>,
# _:blankNode, or "literal"
def realize( string, isURI ):
    global prefixDict, base
    
    # if it's a blank node we just want to match blank nodes.
    if string.startswith( "_:"):
        return string
    
    elif numericString( string ):
        return '"' + string + '"'
        
    elif string == "false":
        return '"false"'
        
    elif string == "true":
        return '"false"'
    
    elif isURI:
        URI = string[ 1 : len(string)-1 ]
        # Check if the URI is relative using urllib.parse.urlparse
        if relativeURI( URI ):
            # if it is only relative, we add base to the URI
            return "<" + base + URI + ">"
        else:
            return string
    elif (string == 'a') and (len(string) == 1):
        return 'a'
    else:
        return "<" + multiple_replace( prefixDict, string ) + ">"
   
def relativeURI( URI ):
    return urlparse( URI ).scheme == ""
   
# returns true if it parsed a valid prefix or base, otherwise prints an error and quits. 
def detectPrefix( line, lineNum ):
    global prefixDict
    global base
    
    # Match any @prefix, PREFIX, @base, BASE and grab their values (case insensitive)
    if re.match( "@prefix|@base|base|prefix", line, re.IGNORECASE ):
    
        # match @prefix declaration
        matchObj = re.match( "^@prefix\s*([^_]*:)\s*<(.*)>\s*\.", line,  re.IGNORECASE )
        if matchObj:
            key = matchObj.group(1)
            value = matchObj.group(2)
            if relativeURI( value ) and key in prefixDict:
                prefixDict[key] += value
            else:
                prefixDict[key] = value
                
            return True
        
        # match PREFIX declaration
        matchObj = re.match( "^PREFIX\s*([^_]*:)\s*<(.*)>", line, re.IGNORECASE )
        if matchObj:
            key = matchObj.group(1)
            value = matchObj.group(2)
            if relativeURI( value ) and key in prefixDict:
                prefixDict[key] += value
            else:
                prefixDict[key] = value
            return True
        
        # match @base declaration
        matchObj = re.match( "^@base\s*<(.*)>\s*\.", line, re.IGNORECASE )
        if matchObj:
            if relativeURI( matchObj.group(1) ):
                base += matchObj.group(1)
            else:
                base = matchObj.group(1)
            return True
        
        # match BASE declaration
        matchObj = re.match( "^BASE\s*<(.*)>", line, re.IGNORECASE )        
        if matchObj:
            if relativeURI( matchObj.group(1) ):
                base += matchObj.group(1)
            else:
                base = matchObj.group(1)
            return True
            
        # reached end without parsing any definition properly
        print( "ERROR: declared prefix or base match failure on line", lineNum )
        exit(1)
    else:
        return False

# The preparser separates the .ttl file into a list of each element, for use with 
# the TURTLE state machine later on.  
def preParse( ttlFile ):
    STATE_WS = 0            # separating elems by whitespace
    STATE_STARTQUOTE = 1    # currently determining what quote state to go to
    STATE_SINGQ = 2         # currently in ' ... '
    STATE_DOUBQ = 3         # currently in " ... "
    STATE_LONG_SINGQ = 4    # currently in ''' ... '''
    STATE_LONG_DOUBQ = 5    # currently in """ ... """ 
    STATE_URI = 6           # currently in < ... >
    STATE_NONWS = 7         # parsing some non-whitespace substring
    STATE_EXPECT_WS = 8     # need to wait for whitespace (otherwise it violates rules)
    STATE_STRING_END = 9    # filter and confirm that string ending is correct. (i.e. @en, etc...)
    curState = STATE_WS
    elemList = []           # list of elements from the TURTLE file to be returned
    curElem = ""
    quoteCount = 0          # counts the number of times a '"' or "'" occurs in LONG state.

    lineNum = 0             # provide useful line information in case of error.
    for line in ttlFile:
        lineNum += 1
        
        # detect if the line contains a prefix and go to the next line after parsing it
        # Should be STATE_WS because we shouldn't parse these in literals or URIs (an error)
        if curState == STATE_WS:
            if detectPrefix( line, lineNum ):
                continue
    
        # We will individually go over each character in the line. 
        for ch in line:
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_WS
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            #
            # We are expecting whitespace here (that we will ignore).
            # curElem should be empty.
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # print( "state =", curState, "ch =", ch, "curElem =", curElem )
            if curState == STATE_WS:
                # Check if we are encountering a string
                if (ch == "'") or (ch == '"'):
                    curElem += ch
                    curState = STATE_STARTQUOTE
                    continue
                    
                # check if we are encountering a comment
                elif (ch == "#"):
                    break # we stop parsing the line (for loop picks up next line)
                
                # Check if we encountered an ending
                elif (ch == ".") or (ch == ";") or (ch == ","):
                    elemList.append( ch )
                    curState = STATE_EXPECT_WS
                    continue
                
                # check if we are encountering the start of a URI
                elif (ch == "<"):
                    curElem += ch
                    curState = STATE_URI
                    continue;
                
                # We just filter out whitespace
                elif (ch.isspace()):
                    continue
                
                # we are encountering a non-whitespace character, switch states
                else:
                    curState = STATE_NONWS
                    curElem += ch
                    continue
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_NONWS || STATE_URI
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            #
            # Parsing an element that we will use the realize( string )
            # function on. 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_NONWS or curState == STATE_URI:
                # keep adding to the current element until we hit whitespace
                if (not ch.isspace()):
                    curElem += ch
                    continue
                    
                # attempt to resolve the non-whitespace element
                else:
                    if curState == STATE_URI:
                        curElem = realize( curElem, True )
                        elemList.append( curElem )
                    elif curState == STATE_NONWS:
                        curElem = realize( curElem, False )
                        elemList.append( curElem )
                    curState = STATE_WS
                    curElem = ""
                    continue
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # STATE_STARTQUOTE
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            #
            # Encountered a " or a ' need to determine if we are going into
            # a multiline literal or a regular one.
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            elif curState == STATE_STARTQUOTE:
                curElem += ch
                if ( len(curElem) == 3 and curElem[0] == curElem[1] ):
                    if curElem[2] == curElem[0]:
                        if curElem[0] == '"':
                            curState = STATE_LONG_SINGQ
                            continue
                        elif curElem[0] == "'":
                            curState = STATE_LONG_SINGQ
                            continue
                    else:
                        # TODO: perhaps check for whitespace (i.e. '"" ')
                        print( "Error: unexpected termination on line", lineNum )
                        exit(1)
                        
                elif ( len(curElem) == 2 and curElem[0] == curElem[1] ):
                    # need to check for third
                    continue
                    
                else:
                    if (curElem[0] == '"'):
                        curState = STATE_DOUBQ
                        continue
                    else:
                        curState = STATE_SINGQ
                        continue
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_EXPECT_WS
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # 
            # Terminates and prints an error if the current character is not
            # whitespace
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_EXPECT_WS:
                if (ch.isspace()):
                    curState = STATE_WS
                    continue
                else:
                    print( "Error, expecting whitespace after token on line", lineNum )
                    exit(1)
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_DOUBLQ (")
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_DOUBQ:
                if ch in "\n\r":
                    print( "Error: \"-type literals must not contain newlines, found on line", lineNum )
                    exit(1)
                
                elif ch == '"':
                    curState = STATE_STRING_END
                    elemList.append( curElem + ch )
                    curElem = ""
                    continue
                    
                else:
                    curElem += ch
                
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_SINGQ (')
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_SINGQ:
                if ch in "\n\r":
                    print( "Error: \"-type literals must not contain newlines, found on line", lineNum )
                    exit(1)
                
                elif ch == "'":
                    curState = STATE_STRING_END
                    elemList.append( curElem + ch )
                    curElem = ""
                    continue
                    
                else:
                    curElem += ch
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_LONG_DOUBQ (""")
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_LONG_DOUBQ:
                curElem += ch
                # If we have 2 concurrent "s, and the third is seen, the literal is done
                if quoteCount == 2 and ch == '"':
                    curState = STATE_STRING_END
                    quoteCount = 0
                    elemList.append( curElem )
                    curElem = ""
                    continue
                    
                # We add a count for each concurrent double quote we encounter
                elif ch == '"':
                    quoteCount += 1
                    continue
                    
                # go to the next 
                else:
                    quoteCount = 0
                    continue
            
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_LONG_SINGQ (''')
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_LONG_SINGQ:
                curElem += ch
                # If we have 2 concurrent 's, and the third is seen, the literal is done
                if quoteCount == 2 and ch == "'":
                    curState = STATE_STRING_END
                    elemList.append( curElem )
                    quoteCount = 0
                    curElem = ""
                    continue
                    
                # We add a count for each single quote we encounter
                elif ch == "'":
                    quoteCount += 1
                    continue
                
                # else we continue to the next character
                else:
                    quoteCount = 0
                    continue
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # STATE_STRING_END
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_STRING_END:
                curElem += ch
                if ch == " ":
                    curElem = ""
                    curState = STATE_WS
                    continue
                
                # if the first character after a literal is [.|;|.] 
                # we want to be able to catch it.
                elif len( curElem ) == 1:
                    if curElem == '.' or curElem == ',' or curElem == ';':
                        elemList.append( curElem )
                        curElem = ""
                        curState = STATE_WS
                # do more stuff
                
    return elemList
                       
# Main function of rdfparser.py, calls preParse and tripleStateMachine.
def parseRDF( ttlFile ):
    global prefixDict
  
    elemList = preParse( ttlFile )
    # print( elemList )        
        
    for elem in elemList: 
        tripleStateMachine( elem, 0 )
    
    global tripleList
    
    # print()
    # print( "TRIPLES:" )
    # for trip in tripleList:
    #     print( trip[0], trip[1], trip[2] )
    
    # print()
    print( "found", len(tripleList), "triples, and", len( prefixDict), "prefixes" )
    return tripleList
        

# State represents what was 'seen' last.
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
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # initial state or after a period 
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if curState == STATE_PERIOD:
        checkForEnding( currentElem, "a URI." )
        
        # we allow blank nodes
        if currentElem.startswith( "_:" ):
            pass
            
        # ensure that the thing passed in is the value <URI> (not literal)
        elif currentElem[0] != '<' or currentElem[-1] != '>':
            print( "Error, expected a <URI> not '" + currentElem + "'.")
            exit(1)
            
        curSub = currentElem
        curState = STATE_SUBJECT
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # last saw a subject, looking for predicate
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    elif curState == STATE_SUBJECT or curState == STATE_SEMICOLON:
        checkForEnding( currentElem, "a URI or 'a'." )
        
        if currentElem == "a":
            curPred = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
            
        # ensure that the thing passed in is the value 'a' or a <URI> (not literal)
        elif currentElem[0] != '<' or currentElem[-1] != '>':
            print( "Error, expected a <URI> or 'a' not '" + currentElem + "'.")
            exit(1)
            
        else:
            curPred = currentElem
            
        curState = STATE_PREDICATE
        
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # last saw a predicate, looking for an object
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    elif curState == STATE_PREDICATE or curState == STATE_COMMA:
        checkForEnding( currentElem, "a URI or a literal" )
        curObj = currentElem
        
        # if it's a URI do nothing.
        if curObj[0] == '<' or curObj[-1] == '>':
            pass
            
        elif curObj.startswith( "_:" ):
            pass
            
        # if it's a literal, remove the quotes.
        elif (curObj[0] == '"' and curObj[-1] == '"') or (curObj[0] == "'" and curObj[-1] == "'"):
            if ( len(curObj) > 5 ) and curObj[0] == curObj[1] and curObj[0] == curObj[2]:
                curObj = curObj[ 3: len(curObj)-3 ]
            else:
                curObj = curObj[ 1 : len(curObj)-1 ]
        else:
            print( "Error, expected literal or URI got", currentElem )
            exit(1)
            
        createRDFtuple( curSub, curPred, curObj )
        curState = STATE_OBJECT
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # Saw an object, looking for [.|,|;]
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    elif curState == STATE_OBJECT:
        if currentElem == ".":
            curState = STATE_PERIOD
        elif currentElem == ",":
            curState = STATE_COMMA
        elif currentElem == ";":
            curState = STATE_SEMICOLON
        else:
            print( "Unexpected element '" + currentElem + "' was expecting: [.|,|;]" )
            exit(1)

# Terminates the program if the element if one of [.|;|,]
def checkForEnding( elem, expectedType ):
    if elem == ".":
        val = True
    elif elem == ",":
        val = True
    elif elem == ";":
        val = True
    else:
        val = False
    
    if val:
        print( "Unexpected ending character,", elem, "should have been", expectedType )
        exit(1)

