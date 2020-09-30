import re

class Token:
    def __init__( self, name, content, isTerminal ):
        self.name = name
        self.content = content
        self.isTerminal = isTerminal

    def __repr__( self ):
        return "{0}<{1}> = {2}".format( "T" if self.isTerminal else "", self.name, self.content )

class Rule:
    def __init__( self, owner, iReduceToken, iTokens ):
        self.owner = owner
        self.iReduceToken = iReduceToken
        self.iTokens = iTokens
    
    def __repr__( self ):
        line = "<{0}> = ".format( self.owner.tokens[self.iReduceToken].name )
        for iToken in self.iTokens:
            line += "<{0}> ".format( self.owner.tokens[iToken].name )
        line = line[:-1]
        return line

class Shift:
    def __init__( self, owner, iToken, iLastState, iNextState ):
        self.owner = owner
        self.iToken = iToken
        self.iLastState = iLastState
        self.iNextState = iNextState

    def isReduce( self ):
        return self.owner.states[self.iNextState].isReduce()

    def __repr__( self ):
        return "shift from S({0}) to S({1}) by <{2}>".format( self.iLastState, self.iNextState, self.owner.tokens[self.iToken].name )

class State:
    def __init__( self, owner, iRule, iiNextToken ):
        self.owner = owner
        self.iRule = iRule
        self.iiNextToken = iiNextToken
        self.shifts = []

    def __repr__( self ):
        rule = self.owner.rules[self.iRule]
        line = "<{0}> = ".format( self.owner.tokens[rule.iReduceToken].name )
        for iiToken in range( len( rule.iTokens ) ):
            iToken = rule.iTokens[iiToken]
            token = self.owner.tokens[iToken]
            if self.iiNextToken == iiToken:
                line += ". "
            line += "<{0}> ".format( token.name )
            
        if self.isReduce():
            line += ". "

        line = line[:-1]
        line += "\n"

        if self.isReduce() == False:
            for shift in self.shifts:
                line +=  "\t{0}\n".format( shift )
        else:
            line += "\treduce to {0}\n".format( self.owner.tokens[self.getReduceToken()].name )

        return line

    def findShift( self, iToken, iLastState, iNextState ):
        for iShift in range( len( self.shifts ) ):
            shift = self.shifts[iShift]
            if shift.iToken == iToken and shift.iLastState == iLastState and shift.iNextState == iNextState:
                return iShift
        return -1

    def addShift( self, owner, iToken, iLastState, iToState ):
        iShift = self.findShift( iToken, iLastState, iToState )
        if iShift < 0:
            self.shifts.append( Shift( owner, iToken, iLastState, iToState ) )

    def getReduceToken( self ):
        return self.owner.rules[self.iRule].iReduceToken
    
    def isStart( self ):
        return self.iiNextToken == 0

    def isReduce( self ):
        return len( self.shifts ) == 0

class Generator:
    def __init__( self ):
        self.tokens = []
        self.rules = []
        self.states = []

    def addToken( self, name, regex, isTerminal ):
        iToken = len( self.tokens )
        self.tokens.append( Token( name, regex, isTerminal ) )
        return iToken

    def addRule( self, iReduceToken, iTokens ):
        iRule = len( self.rules )
        self.rules.append( Rule( self, iReduceToken, iTokens ) )
        return iRule

    def addState( self, iRule, iiNextToken ):
        iState = self.findState( iRule, iiNextToken )
        if iState < 0:
            iState = len( self.states )
            self.states.append( State( self, iRule, iiNextToken ) )
        return iState

    def findToken( self, name ):
        for iToken in range( len( self.tokens ) ):
            token = self.tokens[iToken]
            if token.name == name:
                return iToken
        return -1

    def findState( self, iRule, iiNextToken ):
        for iState in range( len( self.states ) ):
            state = self.states[iState]
            if state.iRule == iRule and state.iiNextToken == iiNextToken:
                return iState
        return -1

    def load( self, path ):
        terminal_re = r'T<(\w*)>\s*=\s*(.*)'
        nonterminal_re = r'<(\w*)>\s*=\s*(.*)'

        with open( path, "r" ) as f:
            for line in f:
                match = re.match( terminal_re, line )
                if match and len( match.groups() ) == 2:
                    self.addToken( match.groups()[0], match.groups()[1], True )
                else:
                    match = re.match( nonterminal_re, line )
                    if match and len( match.groups() ) == 2:
                        self.addToken( match.groups()[0], match.groups()[1], False )

    def extractRules( self ):
        for iReduceToken in range( len( self.tokens ) ):
            reduceToken = self.tokens[iReduceToken]
            if reduceToken.isTerminal:
                continue
            for rule in reduceToken.content.split( "|" ):
                iTokens = []
                rule = rule.strip()
                for word in rule.split():
                    word = word.strip( "<>" )
                    iToken = self.findToken( word )
                    if iToken == -1:
                        print( "[Generator::extractRules()]: Can't find token {0} in rule <{1}> = {2}".format( word, reduceToken.name, rule ) )
                        iTokens.clear()
                    else:
                        iTokens.append( iToken )
                if len( iTokens ) > 0:
                    self.addRule( iReduceToken, iTokens )

    def extractState( self, stack, iLastState, iLastTerminalToken ):
        iRule, iiNextToken = stack[-1]
        rule = self.rules[iRule]

        # debug current rule, iiNextToken
        line = "extracting <{0}> = ".format( self.tokens[rule.iReduceToken].name )
        for iiToken in range( len( rule.iTokens ) ):
            token = self.tokens[rule.iTokens[iiToken]]
            if iiToken == iiNextToken:
                line += ". "
            line += "<{0}> ".format( token.name )
        if iiNextToken >= len( rule.iTokens ):
            line += ". "
        line = line[:-1]
        print( line )

        if iiNextToken < len( rule.iTokens ):
            iNextToken = rule.iTokens[iiNextToken]
            nextToken = self.tokens[iNextToken]
            if nextToken.isTerminal == False:
                # if nextToken is not terminal
                # for any rule reduces to iNextToken
                for iShiftRule in range( len( self.rules ) ):
                    shiftRule = self.rules[iShiftRule]
                    if shiftRule.iReduceToken == iNextToken and iShiftRule != iRule:
                        
                        # are we in a recursive loop
                        found = False
                        for e in stack:
                            if e == ( iShiftRule, 0 ):
                                found = True

                        if found == False:
                            # add state if not exist
                            # iNextState = self.addState( iRule, iiNextToken )
                            # if iLastState >= 0:
                            #     self.states[iLastState].addShift( self, iLastTerminalToken, iLastState, iNextState )
                            # if not in a recursive loop, recursive extract current iShiftRule
                            stack.append( ( iShiftRule, 0 ) )
                            self.extractState( stack, iLastState, iLastTerminalToken )
                        else:
                            # if in a loop, means, current iShiftRule is already been working on, try next iShiftRule
                            continue
            else:
                # if nextToken is terminal
                # add state if not exist
                iNextState = self.addState( iRule, iiNextToken )
                # iLastState < 0 represents start state, skip start state
                if iLastState >= 0:
                    self.states[iLastState].addShift( self, iLastTerminalToken, iLastState, iNextState )
                # we are done with this token, working on the next one in the iRule
                stack.pop()
                stack.append( ( iRule, iiNextToken + 1 ) )
                self.extractState( stack, iNextState, iNextToken )

        elif iiNextToken == len( rule.iTokens ):
            # iLastState, iLastTerminalToken is the end token of the rule
            iNextState = self.addState( iRule, iiNextToken )
            # iLastState < 0 represents start state, skip start state
            if iLastState >= 0:
                self.states[iLastState].addShift( self, iLastTerminalToken, iLastState, iNextState )

    def mergeStates( self ):
        # merge states with the same reduce token and same next tokens
        for iState in range( len( self.states ) ):
            state = self.states[iState]
            for iShift in range( len( state.shifts ) ):
                shift = state.shifts[i]

        return

    def extractStates( self ):
        # for any rule reduces to "start"
        for iRule in range( len( self.rules ) ):
            rule = self.rules[iRule]
            if self.tokens[rule.iReduceToken].name == "start":
                self.extractState( [( iRule, 0 )], -1, -1 )
        return

    def printTokens( self ):
        print( "{0} tokens".format( len( self.tokens ) ) )
        for iToken in range( len( self.tokens ) ):
            print( "T({0}): {1}".format( iToken, self.tokens[iToken] ) )

    def printRules( self ):
        print( "{0} rules".format( len( self.rules ) ) )
        for iRule in range( len( self.rules ) ):
            print( "R({0}): {1}".format( iRule, self.rules[iRule] ) )

    def printStates( self ):
        print( "{0} states".format( len( self.states ) ) )
        for iState in range( len( self.states ) ):
            print( "S({0}): {1}".format( iState, self.states[iState] ) )

if __name__ == "__main__":
    path = "./ParserTokens.txt"
    gen = Generator()
    gen.load( path )
    # gen.printTokens()
    gen.extractRules()
    # gen.printRules()
    gen.extractStates()
    gen.printStates()

# known issues:
# deduction stopped when there is already a state generated, should continue regardless and just don't regenerate existing state