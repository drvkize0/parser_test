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
                            # if in a loop, means, current iShiftRule is already exist, shift to it
                            iNextState = self.addState( iShiftRule, 0 )
                            # self.states[iLastState].addShift( self, iLastTerminalToken, iLastState, iNextState )
                            stack.append( ( iShiftRule, 0 ) )
                            self.extractState( stack, iNextState, iLastTerminalToken )
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
        similarShifts = []
        for iState in range( len( self.states ) ):
            state = self.states[iState]
            iShift = 0
            while iShift < len( state.shifts ):
                shift = state.shifts[iShift] 
                reduceToken = shift.getReduceToken()
                similarShifts.clear()
                for iTestShift in range( iShift + 1, len( state.shifts ) ):
                    testShift = state.shifts[iTestShift]
                    if reduceToken == testShift.getReduceToken() and shift.iToken == testShift.iToken:
                        similarShifts.append( iTestShift )

                # if len( similarShifts ) > 0:
                #     print( "similar shift ({0}) in S({1}):".format( len( similarShifts ), iState ) )
                #     for iSimilarShift in similarShifts:
                #         print( state.shifts[iSimilarShift] )

                # self.addRule( reduceToken, )
                # self.addState( state.iRule, state. )

                iShift += len( similarShifts ) + 1
                iShift += 1
        return

    def extractStates( self ):
        # for any rule reduces to "start"
        for iRule in range( len( self.rules ) ):
            rule = self.rules[iRule]
            if self.tokens[rule.iReduceToken].name == "start":
                self.extractState( [( iRule, 0 )], -1, -1 )
        return


# def extractState( self, iLastState ):
    #     lastState = self.owner.states[iLastState]
    #     iiLastToken = lastState.iiNextToken
    #     iLastToken = lastState.getRule().iTokens[iiLastToken]
    #     lastToken = self.tokens[iLastToken]
    #     iLastRule = lastState.iRule
    #     lastRule = self.rules[iLastRule]

    #     # last token is terminal, same rule, check next token
    #     iiLastRuleNextToken = lastState.iiNextToken + 1
    #     iLastRuleNextToken = lastRule.iTokens[iiLastRuleNextToken] if iiLastRuleNextToken >= 0 and iiLastRuleNextToken < len( lastRule.iTokens ) else -1
    #     lastRuleNextToken = self.tokens[iLastRuleNextToken] if iLastRuleNextToken >= 0 and iLastRuleNextToken < len( self.tokens ) else None
        
    #     if lastToken.isTerminal:
    #         if lastRuleNextToken is None:
    #             # last token is the end token of it's rule, reduce to lastState.iReduceState
    #             lastState.addShift( Shift( self, iLastToken, iLastState, lastState.iReduceState ) )

    #         else:
    #             # last token is not the end token of it's rule, shift to next token
    #             iLastRuleNextState = self.addState( lastState.iReduceState, lastState.iRule, iiLastRuleNextToken )
    #             lastRuleNextState = self.states[iLastRuleNextState]
    #             lastRuleNextState.addShift( Shift( self, iLastToken, iLastState, iLastRuleNextState ) )
    #             self.extractState( iLastRuleNextState )

    #     else:
    #         # last token is not terminal, shift to first token of all possible rules that generate last token
    #         for iNextRule in range( len( self.rules ) ):
    #             nextRule = self.rules[iNextRule]
    #             if nextRule.iReduceToken == iLastToken:

    #                 # decide reduce state of nextRuleNextState
    #                 if lastRuleNextToken is None:
    #                     # last token is the end token of it's rule, make all subsequence states in nextRule reduce to iLastRuleState.iReduceState
    #                     iNextRuleNextState = self.addState( lastState.iReduceState, iNextRule, 0 )
    #                     self.extractState( iNextRuleNextState )

    #                 else:
    #                     # last token is not the end token of it's rule, create iNextRuleNextState reduce to iLastRuleState.iReduceState and make all subsequence states in nextRule reduce to iNextRuleNextState
    #                     iLastRuleNextState = self.addState( lastState.iReduceState, lastState.iRule, iiLastRuleNextToken )
    #                     iReduceState = iLastRuleNextState
    #                     lastRuleNextState = self.states[iLastRuleNextState]
    #                     lastRuleNextState.addShift( Shift( self, iLastToken, iLastState, iLastRuleNextState ) )
    #                     self.extractState( iLastRuleNextState )

    #                 iiNextRuleNextToken = 0
    #                 iNextRuleNextToken = nextRule.iTokens[iiNextRuleNextToken]
    #                 iNextRuleNextState = self.addState( iNextRule, iiNextRuleNextToken )
    #                 nextRuleNextState = self.states[iNextRuleNextState]
    #                 lastState.addShift( Shift( self, iLastToken, iLastState, iNextRuleNextState ) )
    #                 reduceStack.append( iLastState )
    #                 self.extractRules