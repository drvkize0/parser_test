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

    def getReduceTokenName( self ):
        return self.owner.tokens[self.iReduceToken].name

class Shift:
    def __init__( self, owner, iTokens, iFromState, iToState ):
        self.owner = owner
        self.iTokens = iTokens.copy()
        self.iFromState = iFromState
        self.iToState = iToState

    def __repr__( self ):
        line = "shift from S({0}) to S({1}) by ".format( self.iFromState, self.iToState )
        for iToken in self.iTokens:
            token = self.owner.owner.tokens[iToken]
            line += "<{0}> ".format( token.name )
        line = line[:-1]
        return line

class State:
    def __init__( self, owner, iRule, iiLastToken ):
        self.owner = owner
        self.iRule = iRule
        self.iiLastToken = iiLastToken
        self.shifts = []

    def __repr__( self ):
        rule = self.owner.rules[self.iRule]
        line = "<{0}> = ".format( self.owner.tokens[rule.iReduceToken].name )
        for iiToken in range( self.iiLastToken ):
            iToken = rule.iTokens[iiToken]
            line += "<{0}> ".format( self.owner.tokens[iToken].name )
        line = line[:-1]
        line += "\n"
        for shift in self.shifts:
            line +=  "\t{0}\n".format( shift )

        return line

    def findShift( self, iTokens, iFromState, iToState ):
        for iShift in range( len( self.shifts ) ):
            shift = self.shifts[iShift]
            if shift.iFromState == iFromState and shift.iToState == iToState:
                # compare shift.iTokens and iTokens
                areAllTokenSame = True
                if len( shift.iTokens ) == len( iTokens ):
                    for iiToken in range( len( shift.iTokens ) ):
                        if iTokens[iiToken] != shift.iTokens[iiToken]:
                            areAllTokenSame = False
                            break
                if areAllTokenSame:
                    return iShift
        return -1

    def addShift( self, iTokens, iFromState, iToState ):
        self.shifts.append( Shift( self, iTokens, iFromState, iToState ) )

    def getRule( self ):
        return self.owner.rules[self.iRule]

    def getReduceToken( self ):
        return self.owner.rules[self.iRule].iReduceToken

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

    def addState( self, iRule, iiLastToken ):
        iState = len( self.states )
        self.states.append( State( self, iRule, iiLastToken ) )
        return iState
        # iState = self.findState( iLastRule, iNextRule, iiToken )
        # if iState < 0:
            
        # return iState

    def findToken( self, name ):
        for iToken in range( len( self.tokens ) ):
            token = self.tokens[iToken]
            if token.name == name:
                return iToken
        return -1

    def findState( self, iReduceState, iRule, iiToken ):
        for iState in range( len( self.states ) ):
            state = self.states[iState]
            if state.iReduceState == iReduceState and state.iRule == iRule and state.iiToken == iiToken:
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

    def extractState( self, stateStack, iRule, iiStartToken ):
        rule = self.rules[iRule]
        iLastState = stateStack[-1] if len( stateStack ) > 0 else -1
        lastState = self.states[iLastState] if iLastState >= 0 and iLastState < len( self.states ) else None

        iState = self.addState( iRule, iiStartToken )
        stateStack.append( iState )
        state = self.states[iState]

        print( "S({0}) <- S({1}): {2}".format( iState, iLastState, rule ) )

        iShiftTokens = []
        for iiToken in range( iiStartToken, len( rule.iTokens ) ):
            iToken = rule.iTokens[iiToken]
            token = self.tokens[iToken]

            if token.isTerminal:
                iShiftTokens.append( iToken )
                iiStartToken += 1
            else:
                if len( iShiftTokens ) > 0:
                    lastState.addShift( iShiftTokens, iLastState, iState )
                    iShiftTokens.clear()
                    print( "meet nonterminal add shift: {0}".format( lastState.shifts[-1] ) )

                for iShiftRule in range( len( self.rules ) ):
                    shiftRule = self.rules[iShiftRule]
                    if shiftRule.iReduceToken == iToken:
                        # shift to nonterminal rule
                            
                        # search for exist state on iShiftRule, 0
                        # reuse the state if found
                        iFoundState = -1
                        for iExistState in range( len( self.states ) ):
                            existState = self.states[iExistState]
                            if existState.iRule == iShiftRule and existState.iiLastToken == 0:
                                iFoundState = iExistState
                        
                        if iFoundState < 0:
                            iReturnState = self.extractState( stateStack, iShiftRule, 0 )
                        else:
                            # prevent recursive loop
                            iExistShift = state.findShift( [], iState, iFoundState )
                            if iExistShift < 0:
                                state.addShift( [], iState, iFoundState )

        if len( iShiftTokens ) > 0:
            state.addShift( iShiftTokens, iLastState, iState )
            iShiftTokens.clear()
            print( "end token add shift: {0}".format( state.shifts[-1] ) )
        
        stateStack.pop()
        return iState

    def extractStates( self ):
        for iRule in range( len( self.rules ) ):
            rule = self.rules[iRule]
            if self.tokens[rule.iReduceToken].name.lower() == "start":
                iStartState = self.addState( -1, 0 )
                self.extractState( [iStartState], iRule, 0 )

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
    # gen.mergeStates()