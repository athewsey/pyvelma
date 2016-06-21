"""py.test tests for the velma.game module

There isn't much to test in velma.game: Only the approximate function
``dicerollstomove()``

"""

################################################################################
#### LIBRARIES #################################################################
#
from .. import game # Under test
import numpy as np  # Utilities


################################################################################
#### TEST CLASSES ##############################################################
#
class TestDiceRollsToMove(object):
    """Tests for function velma.game.dicerollstomove()"""
    testDists = [-1,0,1,2,3,4,5,10,20,np.inf]
    #
    def test_run(self):
        for dist in self.testDists:
            print('Doin')
            approx = game.dicerollstomove(dist)
            exact = dicerollstomove_closedform(dist)
            if approx != exact:
                assert (np.abs(exact-approx) / exact < 0.01), \
                    "Error on dicerollstomove() exceeds accuracy threshold."


################################################################################
#### UTILITY FUNCTIONS #########################################################
#
def dicerollstomove_closedform(distance):
    """Calculate in closed form the expected throws to move a given distance.
    
    This function is very slow for large distances!
    
    """
    if distance < 0:
        return np.inf
    elif distance == 0:
        return 0.
    elif distance == np.inf:
        return np.inf
    else:
        nodes = [0] 
        nodePs = [1.]
        expDiceRolls = 0.
        pCommitted = 0.
        #
        diceRolls = 1.
        while len(nodes) and pCommitted < 0.999:
            newNodes = []
            newPs = []
            #
            for ixNode in range(len(nodes)):
                for diceThrow in range(len(game.DICEPS)):
                    if game.DICEPS[diceThrow] > 0.:
                        newLoc = nodes[ixNode] + diceThrow
                        newP = nodePs[ixNode] * game.DICEPS[diceThrow]
                        if newLoc >= distance:
                            expDiceRolls += newP * diceRolls
                            pCommitted += newP
                        else:
                            newNodes.append(newLoc)
                            newPs.append(newP)
            #            
            nodes = newNodes
            nodePs = newPs    
            diceRolls += 1.
        #    
        return expDiceRolls
#
#### EOF #######################################################################
################################################################################
