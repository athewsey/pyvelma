"""py.test tests for the velma.core module

They say it ain't but it do.

"""

# TODO: This file is only a very simple start to testing velma.core: Add more!

################################################################################
#### LIBRARIES #################################################################
#
## STANDARD PACKAGES ###########################################################
import numpy as np  # For data manipulation
#
## OTHER PARTS OF VELMA ########################################################
from .. import core # Under test
from .. import game # Necessary board definition stuff



################################################################################
#### UTILITY CLASSES ###########################################################
#
class UnhookedDetective(core.Detective):
    host = None
    def __init__(self,hostObj):
        self.host = hostObj
    def hook_notifyerror(self,msg,subsystem=None):
        self.host.countNotifyError += 1
    def hook_notifydebug(self,msg,subsystem=None):
        self.host.countNotifyDebug += 1
    def hook_notifywait(self,operation,subsystem=None):
        self.host.countNotifyWait += 1
    def hook_notifywaitover(self,operation,subsystem=None):
        self.host.countNotifyWaitOver += 1
    def hook_notifyprogress(self,operation,progress,progressLim=1.,
            subsystem=None):
        self.host.countNotifyProgress += 1
    def hook_greet(self):
        self.host.countGreet += 1
    def hook_collectgamesetup(self):
        self.host.countCollectGameSetup += 1
    def hook_observemove(self):
        self.host.countObserveMove += 1
    def hook_rolldice(self):
        return self.host.event_roll()
    def hook_notifymove(self,nodeStop):
        return self.host.event_move(nodeStop)
    def hook_suggest(self,character,room,weapon):
        return self.host.event_suggest(character,room,weapon)
    def hook_accuse(self,character,room,weapon):
        return self.host.event_accuse(character,room,weapon)
    def hook_notifygameover(self,didIWin=None):
        self.host.gameOverResult = didIWin
    def hook_displaysuspicions(self):
        self.host.countDisplaySuggestions += 1
    def hook_displaymovediagnostics(self,statsDict):
        self.host.countDisplayMoveDiagnostics += 1
#
#
class Host(object):
    countNotifyError = 0
    countNotifyDebug = 0
    countNotifyWait = 0
    countNotifyWaitOver = 0
    countNotifyProgress = 0
    countGreet = 0
    countCollectGameSetup = 0
    countObserveMove = 0
    gameOverResult = 0
    countDisplaySuggestions = 0
    countDisplayMoveDiagnostics = 0
    #
    countRolls = 0
    countMoves = 0
    detectiveLoc = None
    countSuggestions = 0
    countAccusations = 0
    nextRoll = 7
    #
    def event_roll(self):
        self.countRolls += 1
        return self.nextRoll
    def event_move(self,nodeStop):
        self.countMoves += 1
        self.detectiveLoc = None
    def hook_suggest(self,character,room,weapon):
        self.countSuggestions += 1
        return None
    def hook_accuse(self,character,room,weapon):
        self.countAccusations += 1
        return False


################################################################################
#### TEST CLASSES ##############################################################
#
class TestSuggestionPosteriors(Host):
    """Check calculation of expected suggestion posteriors in the trivial 
    2-player case where these distributions can be produced in closed form.
    
    """
    dealer = 1
    playerCharCards = (1,4)
    DBGSCENARIO = (
        (0,1,4,8,10,11,15,18,20),(3,5,6,7,12,13,14,16,19),(2,9,17))
    myCardSet = set(DBGSCENARIO[0])
    nUnheldChars = len(game.ALLOWEDCHARS - set(DBGSCENARIO[0]))
    nUnheldRooms = len(game.ALLOWEDROOMS - set(DBGSCENARIO[0]))
    nUnheldWeaps = len(game.ALLOWEDWEAPS - set(DBGSCENARIO[0]))
    nUnheld = (nUnheldChars,nUnheldRooms,nUnheldWeaps)
    #
    # Test with suggestions containing None; One; Two; and Three of the cards in
    # Velma's hand (must be in the stated order!)
    TestSuggestions = ((3,12,17),(2,10,16),(1,11,17),(4,8,15))
    #
    def test_expposteriors(self):
        myDetective = UnhookedDetective(self)
        myDetective.initialise(
            ixDealer = self.dealer,
            playerCharCards = self.playerCharCards,
            DBGSCENARIO = self.DBGSCENARIO
            )
        assert myDetective.areHypothesesEnumerable, \
            "Hypotheses should be easily enumerable in trivial 2-player case."
        #
        # For each hypothesis in the two player game, we know every card not in
        # the scenario or the Detective's hand is in the opponent's hand. Hence,
        # the exact number of hypotheses is known:
        # There is one hypothesis for every character/room/weapon scenario.
        assert (len(myDetective.hypotheses) == 
            self.nUnheldChars * self.nUnheldRooms * self.nUnheldWeaps), \
            "Incorrect hypothesis generation (invalid count)."
        #
        # Now, find the expected entropies and room distributions for 
        # suggestions with 0 through to 3 cards featured from the Detective's
        # own hand:
        expEnts = list()
        expRoomDists = list()
        for suggestion in self.TestSuggestions:
            result = myDetective.suggestionexpposteriors(*suggestion)
            expEnts.append(result['expEntropy'])
            expRoomDists.append(np.array(result['expRoomDist']))
        #
        # The expected entropy for the three-known-card suggestion is known:
        # The only possible answer (pass) takes all hypotheses; and every 
        # hypothesis has a different murder scenario.
        # Hence E = - Nhyp * (1/Nhyp) * log(1/Nhyp) = log(Nhyp)
        startEntropy = np.log(len(myDetective.hypotheses))
        assert abs(startEntropy - myDetective.scenarioEntropy) < 1e-15, \
            "Detective scenarioEntropy variable inconsistent to within \
tolerance: Expected %g, not %g" % (startEntropy,myDetective.scenarioEntropy)
        assert abs(startEntropy - expEnts[3]) < 1e-15, \
            "Incorrect expected entropy returned for suggestion where \
Detective holds all three suggested cards: Expected %g, not %g" \
            (startEntropy,expEnts[3])
        #
        # Oh, and whilst we're at it, the entropy *can't* go up because of a
        # suggestion:
        for ix in range(2):
            assert expEnts[ix] <= startEntropy, \
                "Upper bound violated: expected entropy after a suggestion \
(%u: %g) cannot be higher than prior entropy (%g)!" % \
                (ix,expEnts[ix],startEntropy)
        #
        # We can also calculate the expected entropy of a two-known-card 
        # suggestion exactly:
        nHyps = len(myDetective.hypotheses)
        nHypsWithPass = nHyps
        for ix in range(3):
            if self.TestSuggestions[2][ix] not in self.DBGSCENARIO[0]:
                nHypsWithPass /= self.nUnheld[ix]
        expEnt2 = ((nHypsWithPass * np.log(nHypsWithPass) + 
            (nHyps-nHypsWithPass) * np.log(nHyps-nHypsWithPass)) / nHyps)
        assert abs(expEnts[2]-expEnt2) < 1e-15, \
            "Incorrect expected entropy returned for suggestion where \
Detective holds two suggested cards: Expected %g, not %g" % (expEnt2,expEnts[2])
        #
        # Regarding the expected room distributions, they must all be valid
        # probability distributions:
        for ix in range(len(self.TestSuggestions)):
            assert all(expRoomDists[ix] >= 0.), \
                "Expected probability distribution over rooms after suggestion \
%u includes negative values: %s" % (ix,expRoomDists[ix])
            assert abs(np.sum(expRoomDists[ix])-1.) < 1e-15, \
                "Expected probability distribution over rooms after suggestion \
%u fails to sum to unity (%g) within required tolerance." % \
                (ix,np.sum(expRoomDists[ix]))
    
class TestSyntheticScenario(Host):
    dealer = 0
    playerCharCards = (0,1,2)
    DBGSCENARIO = (
        (2,3,7,8,14,17),(1,6,9,12,15,16),(0,5,11,13,19,20),(4,10,18))
    specimenMovesFrom51 = [[51],[52],[68,53,39],[40,69,54],[68,70,39,41,53,55],
        [69,71,40,42,54,56],[68,70,39,72,41,43,53,55,57],
        [69,71,40,73,42,44,54,56,58],[1,68,70,39,72,41,74,43,45,79,53,55,57,59],
        [1,69,71,40,73,42,75,44,46,79,54,56,58,28,60],
        [1,61,68,70,39,72,41,74,43,76,45,79,80,18,53,55,57,59,29],
        [1,69,71,40,73,42,75,60,46,79,81,19,84,14,54,56,58,28,44,62],
        [1,3,10,15,18,29,39,41,43,45,53,55,57,59,61,63,68,70,72,74,76,79,80,85,
        89]]
    #
    def test_setup(self):
        myDetective = UnhookedDetective(self)
        myDetective.initialise(
            ixDealer = self.dealer,
            playerCharCards = self.playerCharCards,
            DBGSCENARIO = self.DBGSCENARIO
            )
    #
    def test_mapmoves(self):
        myDetective = UnhookedDetective(self)
        myDetective.initialise(
            ixDealer = self.dealer,
            playerCharCards = self.playerCharCards,
            DBGSCENARIO = self.DBGSCENARIO
            )
        movemap = myDetective.mappossiblemoves(game.CHARSTARTNODES[0])
        for ix in range(len(movemap)):
            assert set(movemap[ix]) == set(self.specimenMovesFrom51[ix]), \
                "Inconsistency in possible move mapping from Col. Mustard start"
    #
    def test_move(self):
        myDetective = UnhookedDetective(self)
        myDetective.initialise(
            ixDealer = self.dealer,
            playerCharCards = self.playerCharCards,
            DBGSCENARIO = self.DBGSCENARIO
            )
        myDetective.ixHotSeat = 0
        myDetective.move()
        
    #
    def test_initialgenerationbias(self):
        myDetective = UnhookedDetective(self)
        myDetective.HYPSAMPLECOUNT = myDetective.HYPSAMPLECOUNT * 100
        myDetective.initialise(
            ixDealer = self.dealer,
            playerCharCards = self.playerCharCards,
            DBGSCENARIO = self.DBGSCENARIO
            )
        # Check the probabilities:
        for ixChar in range(game.NCHARS):
            for ixRoom in range(game.NCHARS):
                for ixWeap in range(game.NWEAPS):
                    #TODO
                    isPossibility = game.CHARS[ixChar]
                    
        myDetective.ixHotSeat = 0
        myDetective.move()
#
#### EOF #######################################################################
################################################################################
