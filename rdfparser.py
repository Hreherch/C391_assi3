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
    
    Expectations:
        Each token is separated by at least one space or .split()-able 
        character. Example:
            subject predicate object . #comment
        We allow strings other than @en.
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
    print( "NEW TRIPLE:", tripleList[-1] )


# http://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex-in-python
def multiple_replace(dict, text):
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 
    
# Takes a string that represents a clean triple element and tries to convert it to <URI>
def realize( string, isURI ):
    global prefixDict, base
    if isURI:
        URI = string[ 1 : len(string)-1 ]
        # Check if the URI is relative using urllib.parse.urlparse
        if urlparse( URI ).scheme == "":
            # if it is only relative, we add base to the URI
            return "<" + base + URI + ">"
        else:
            return string
    else:
        return "<" + multiple_replace( prefixDict, string ) + ">"
   
# returns true if it parsed a valid prefix or base, otherwise prints an error and quits. 
def detectPrefix( line, lineNum ):
    global prefixDict
    global base
    
    # Match any @prefix, PREFIX, @base, BASE and grab their values (case insensitive)
    if re.match( "@prefix|@base|base|prefix", line, re.IGNORECASE ):
    
        # match @prefix declaration
        matchObj = re.match( "^@prefix ([^_]*:).*<(.*)> . *$", line,  re.IGNORECASE )
        if matchObj:
            key = matchObj.group(1)
            value = matchObj.group(2)
            prefixDict[key] = value
            print( "HANDLE PREFIX:", line )
            print( "PREFIX:", key, "VALUE:", value )
            return True
        
        # match PREFIX declaration
        matchObj = re.match( "^PREFIX ([^_]*:).*<(.*)> *$", line, re.IGNORECASE )
        if matchObj:
            key = matchObj.group(1)
            value = matchObj.group(2)
            prefixDict[key] = value
            print( "HANDLE PREFIX:", line )
            print( "PREFIX:", key, "VALUE:", value )
            return True
        
        # match @base declaration
        matchObj = re.match( "^@base <(.*)> . *$", line, re.IGNORECASE )
        if matchObj:
            print( "HANDLE BASE:", line )
            base = matchObj.group(1)
            print( "BASE IS NOW:", base )
            return True
        
        # match BASE declaration
        matchObj = re.match( "^BASE <(.*)> *$", line, re.IGNORECASE )        
        if matchObj:
            print( "HANDLE BASE:", line )
            base = matchObj.group(1)
            print( "BASE IS NOW:", base )
            return True
            
        # reached end without parsing any definition properly
        print( "ERROR: declared prefix or base match failure on line", lineNum )
        exit(1)
    else:
        return False
    
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
    elemList = []
    curElem = ""
    quoteCount = 0

    lineNum = 0
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
            # 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # We are expecting whitespace here (that we will ignore)
            # curElem should be empty
            print( "state =", curState, "ch =", ch, "curElem =", curElem )
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
            # 
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
            # 
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
                        print( "Error: something weird went on here" )
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
            # 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_EXPECT_WS:
                if (ch.isspace()):
                    curState = STATE_WS
                    continue
                else:
                    print( "Error, expecting whitespace after token on line", lineNum )
                    exit(1)
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_DOUBQ:
                if ch in "\n\r\\":
                    print( "Error: \"-type literals must not contain newlines or '\\'. On line", lineNum )
                    exit(1)
                
                elif ch == '"':
                    curState = STATE_STRING_END
                    elemList.append( curElem + ch )
                    curElem = ""
                    continue
                    
                else:
                    curElem += ch
                
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_SINGQ:
                if ch in "\n\r\\":
                    print( "Error: \"-type literals must not contain newlines or '\\'. On line", lineNum )
                    exit(1)
                
                elif ch == "'":
                    curState = STATE_STRING_END
                    elemList.append( curElem + ch )
                    curElem = ""
                    continue
                    
                else:
                    curElem += ch
                    
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # 
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
            # 
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
            # 
            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            elif curState == STATE_STRING_END:
                if ch == " ":
                    curState = STATE_WS
                    continue
                else:
                    curElem += ch
                
    return elemList
                       


def parseRDF( ttlFile ):
    global prefixDict
    
    # The @base or BASE defined URI
    base = ""
    # The line number of the parsed file
    lineNum = 0
    
    elemList = preParse( ttlFile )
    print( elemList )
    exit(0)
    
    for line in ttlFile:
        lineNum += 1
        line = line.strip()
        
        print( "\n" * 3 )
        
        print( "LINE:", line )
        
        # Match any @prefix, PREFIX, @base, BASE and grab their values (case insensitive)
        if re.match( "@prefix|@base|base|prefix", line, re.IGNORECASE ):
            # match @prefix declaration
            matchObj = re.match( "^@prefix ([^_]*:).*<(.*)> . *$", line,  re.IGNORECASE )
            if matchObj:
                key = matchObj.group(1)
                value = matchObj.group(2)
                prefixDict[key] = value
                print( "HANDLE PREFIX:", line )
                print( "PREFIX:", key, "VALUE:", value )
                continue # continue to the next line
            
            # match PREFIX declaration
            matchObj = re.match( "^PREFIX ([^_]*:).*<(.*)> *$", line, re.IGNORECASE )
            if matchObj:
                key = matchObj.group(1)
                value = matchObj.group(2)
                prefixDict[key] = value
                print( "HANDLE PREFIX:", line )
                print( "PREFIX:", key, "VALUE:", value )
                continue # continue to the next line
            
            # match @base declaration
            matchObj = re.match( "^@base <(.*)> . *$", line, re.IGNORECASE )
            if matchObj:
                print( "HANDLE BASE:", line )
                base = matchObj.group(1)
                print( "BASE IS NOW:", base )
                continue # continue to the next line
            
            # match BASE declaration
            matchObj = re.match( "^BASE <(.*)> *$", line, re.IGNORECASE )        
            if matchObj:
                print( "HANDLE BASE:", line )
                base = matchObj.group(1)
                print( "BASE IS NOW:", base )
                continue # continue to the next line
                
            # reached end without parsing any definition properly
            print( "ERROR: prefix or base match failure on line", lineNum )
            exit(1)
            

        # shlex splits elements like shell, so "objects like this" will appear as 
        # one element in the split array
        split = shlex.split(line) 
        print( "SPLIT: ", split )
        
        
        for elem in split: 
            # If it matches a <URI>
            matchObj = re.match( "^<(.*)>$", elem )
            if matchObj:
                # Check if the URI is relative using urllib.parse.urlparse
                if urlparse( matchObj.group(1) ).scheme == "":
                    # if it is only relative, we add base to the URI
                    elem = "<" + base + matchObj.group(1) + ">"
                # else we input the URI to the state machine. 
                tripleStateMachine( elem, lineNum )
                continue  # done work, can continue to next element
            
            if elem != "." and elem != "," and elem != ";" and elem != "a":
                if urlparse( elem[1:len(elem)-2] ).scheme != "":
                    elem = "<" + multiple_replace( prefixDict, elem ) + ">"
           
            tripleStateMachine( elem, lineNum )
                
    
    # print out some statistics about the parsing.
    global tripleList
    
    print()
    print( "TRIPLES:" )
    for trip in tripleList:
        print( trip[0], trip[1], trip[2] )
    
    print()
    print( "found", len(tripleList), "triples, and", len( prefixDict), "prefixes" )
    print( "file had", lineNum, "lines" )
    print( "potentially missed:", lineNum - (len(tripleList) + len(prefixDict)) )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
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
            curPred = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
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

