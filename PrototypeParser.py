import os
import sys
import re
from enum import Enum

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
        toState = self.owner.owner.states[self.iToState]
        line = "shift to {0} by ".format( toState.getStateTag() )
        for iToken in self.iTokens:
            token = self.owner.owner.tokens[iToken]
            line += "<{0}> ".format( token.name )
        line = line[:-1] if len( line ) > 0 else line
        return line

class StateType( Enum ):
    Unknown = 0
    Map = 1
    Reduce = -1
    Start = 10
    End = -10

    def __str__( self ):
        if self == self.Unknown: return 'U'
        if self == self.Map: return 'M'
        if self == self.Reduce: return 'R'
        if self == self.Start: return 'S'
        if self == self.End: return 'E'

class State:
    def __init__( self, owner, stateType, id, iRule, iiToken ):
        self.owner = owner
        self.stateType = stateType
        self.id = id
        self.iRule = iRule
        self.iiToken = iiToken
        self.shifts = []

    def getStateTag( self ):
        rule = self.owner.rules[self.iRule]
        return "{0}{1}<{2}, {3}, {4}> = ".format( self.stateType, self.id, self.iRule, self.iiToken, self.getReduceTokenName() )

    def __repr__( self ):
        rule = self.owner.rules[self.iRule]
        line = self.getStateTag()
        for iiToken in range( self.iiToken - 1 ):
            iToken = rule.iTokens[iiToken]
            line += "<{0}> ".format( self.owner.tokens[iToken].name )

        if self.stateType == StateType.Map:
            line += ". {0}".format( self.owner.tokens[rule.iTokens[self.iiToken]].name )
        elif self.stateType == StateType.Reduce:
            line += "{0} .".format( self.owner.tokens[rule.iTokens[self.iiToken]].name )

        line += "\n"
        for shift in self.shifts:
            line +=  "\t{0}\n".format( shift )
        line = line[:-1]

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

    def getReduceTokenName( self ):
        return self.owner.rules[self.iRule].getReduceTokenName()

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

    def addState( self, stateType, iRule, iiToken ):
        iState = len( self.states )
        self.states.append( State( self, stateType, len( self.states ), iRule, iiToken ) )
        return iState

    def findToken( self, name ):
        for iToken in range( len( self.tokens ) ):
            token = self.tokens[iToken]
            if token.name == name:
                return iToken
        return -1

    def findState( self, stateType, iRule, iiToken ):
        for iState in range( len( self.states ) ):
            state = self.states[iState]
            if state.stateType == stateType and state.iRule == iRule and state.iiToken == iiToken:
                return iState
        return -1

    def findRuleGenerateToken( self, iToken ):
        returnRules = []
        for iRule in range( len( self.rules ) ):
            rule = self.rules[iRule]
            if rule.iReduceToken == iToken:
                returnRules.append( iRule )
        return returnRules

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

    class StateBranch:
        def __init__( self, owner, iRule, iiToken, iTargetRule ):
            self.owner = owner
            self.iRule = iRule
            self.iiToken = iiToken
            self.iTargetRule = iTargetRule

        def __repr__( self ):
            return "Branch({0}, {1}, {2}) -> R({3})".format( self.iRule, self.iiToken, self.owner.owner.tokens[self.owner.owner.rules[self.iRule].iTokens[self.iiToken]].name, self.iTargetRule )

    class ParsingContext:
        def __init__( self, owner ):
            self.owner = owner
            self.branchHistory = []
            self.terminals = []
            self.iLastMapState = -1
            self.mapStates = []
            self.reduceStates = []
            self.terminalsStack = []
        
        def addBranch( self, branch ):
            ret = len( self.branchHistory )
            self.branchHistory.append( branch )
            return ret

        def findBranch( self, branch ):
            for iBranch in range( len( self.branchHistory ) ):
                testBranch = self.branchHistory[iBranch]
                if branch.owner == testBranch.owner and branch.iRule == testBranch.iRule and branch.iiToken == testBranch.iiToken and branch.iTargetRule == testBranch.iTargetRule:
                    return iBranch
            return -1

    def ntab( self, depth ):
        return ''.join( '\t' * depth )

    # investigate rule iRule at iiToken
    def extractState( self, context, iRule, depth ):
        rule = self.rules[iRule]
        iParentMapState = context.mapStates[-1] if len( context.mapStates ) > 0 else None
        iParentReduceState = context.reduceStates[-1] if len( context.reduceStates ) > 0 else None
        context.iLastMapState = iParentMapState

        for iiCurrentToken in range( len( rule.iTokens ) ):
            iCurrentToken = rule.iTokens[iiCurrentToken]
            currentToken = self.tokens[iCurrentToken]

            if currentToken.isTerminal:
                context.terminals.append( iCurrentToken )
            else:
                # ensure map state
                if len( context.terminals ) > 0:
                    iMapState = self.findState( StateType.Map, iRule, iiCurrentToken )
                    if iMapState < 0:
                        iMapState = self.addState( StateType.Map, iRule, iiCurrentToken )

                    # add shift
                    lastState = self.states[context.iLastMapState]
                    iFindShift = lastState.findShift( context.terminals, context.iLastMapState, iMapState )
                    if iFindShift < 0:
                        lastState.addShift( context.terminals, context.iLastMapState, iMapState )
                    context.terminals.clear()
                    context.iLastMapState = iMapState

                # ensure reduce state
                iReduceState = -1
                if iiCurrentToken + 1 < len( rule.iTokens ):
                    iReduceState = self.findState( StateType.Reduce, iRule, iiCurrentToken )
                    if iReduceState < 0:
                        iReduceState = self.addState( StateType.Reduce, iRule, iiCurrentToken )
                else:
                    iReduceState = iParentReduceState
            
                # branch
                iiRulesGenerateCurrentToken = self.findRuleGenerateToken( iCurrentToken )
                ruleGenerateCurrentTokenCount = len( iiRulesGenerateCurrentToken )
                for iiRuleGenerateCurrentToken in range( ruleGenerateCurrentTokenCount ):
                    iRuleGenerateCurrentToken = iiRulesGenerateCurrentToken[iiRuleGenerateCurrentToken];
                    branch = self.StateBranch( context, iRule, iiCurrentToken, iRuleGenerateCurrentToken )
                    iFoundBranch = context.findBranch( branch )
                    if iFoundBranch < 0:
                        context.addBranch( branch )
                        
                        context.mapStates.append( context.iLastMapState )
                        context.reduceStates.append( iReduceState )
                        context.terminalsStack.append( context.terminals )

                        self.extractState( context, iRuleGenerateCurrentToken, depth + 1 )

                        # add shift
                        if len( context.terminals ) > 0:
                            lastState = self.states[context.iLastMapState]
                            iFindShift = lastState.findShift( context.terminals, context.iLastMapState, iReduceState )
                            if iFindShift < 0:
                                lastState.addShift( context.terminals, context.iLastMapState, iReduceState )
                        context.terminals.clear()

                        context.terminals = context.terminalsStack.pop()
                        iReduceState = context.reduceStates.pop()
                        context.iLastMapState = context.mapStates.pop()
                
                context.iLastMapState = iReduceState

    def extractStates( self ):
        iStartState = -1
        iEndState = -1
        for iRule in range( len( self.rules ) ):
            rule = self.rules[iRule]
            if self.tokens[rule.iReduceToken].name.lower() == "start":

                if iStartState < 0:
                    iStartState = self.addState( StateType.Map, iRule, 0 )
                if iEndState < 0:
                    iEndState = self.addState( StateType.Reduce, iRule, 0 )

                context = self.ParsingContext( self )
                context.iLastMapState = iStartState
                context.mapStates.append( iStartState )
                context.reduceStates.append( iEndState )
                self.extractState( context, iRule, 0 )
                context.mapStates.pop()
                context.reduceStates.pop()
                
                if len( context.terminals ):
                    context.iLastMapState

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
            print( ".{0}".format( self.states[iState] ) )

    def parse( tokens ):
        self.iState = 0

        for iiToken in range( len( tokens ) ):
            iToken = tokens[iiToken]

            

        


if __name__ == "__main__":
    path = "./ParserTokens.txt"
    gen = Generator()
    gen.load( path )
    gen.printTokens()
    gen.extractRules()
    gen.printRules()
    gen.extractStates()
    gen.printStates()
    # gen.mergeStates()