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
        character.
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


def parseRDF( rdfFile ):
    global prefixDict
    
    # The @base or BASE defined URI
    base = ""
    
    # The line number of the parsed file
    lineNum = 0
    
    for line in rdfFile:
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

