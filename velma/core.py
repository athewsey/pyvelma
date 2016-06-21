"""Velma core tools.

This module defines the Detective class implementing the AI; as well as
some basic supporting classes.

"""


################################################################################
#### LIBRARIES #################################################################
#
## STANDARD PACKAGES ###########################################################
import numpy as np                  # Lots of NumPy matrix/array stuff
from scipy.misc import comb as nCr  # Combinations function
# TODO: Find an N-D sparse array implementation (scipy.sparse is 2D only)
import random                       # Random sample and shuffle for sets/vectors
import time                         # For timing (for debugging) only
import sys # temp
import multiprocessing as mproc     # For parallel calculations
from collections import namedtuple  # Lightweight structures
#
## OTHER PARTS OF VELMA ########################################################
import velma.game as game           # Definitions of the Cluedo game
import velma.ui as ui               # Default user interface for Velma
import velma.parcore as parcore     # Parallelised core functions


################################################################################
#### WARNING FILTERS FOR NON-FINITE ARITHMETIC #################################
#
import warnings as _warnings
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^divide by zero encountered in log',module='velma.core')
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^invalid value encountered in multiply',module='velma.core')
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^invalid value encountered in divide',module='velma.core')
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^divide by zero encountered in log',module='velma.parcore')
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^invalid value encountered in multiply',module='velma.parcore')
_warnings.filterwarnings("ignore",category=RuntimeWarning,
    message='^invalid value encountered in divide',module='velma.parcore')
del _warnings


################################################################################
#### PACKET DEFINITIONS ########################################################
#

EventPacket = namedtuple("EventPacket","type turn actor consumer nodeStart nodeStop card character room weapon")
EVENTTYPE_GENERIC = 0
EVENTTYPE_MOVE = 1
EVENTTYPE_SUGGESTION = 2
EVENTTYPE_PASS = 3
EVENTTYPE_ACCUSATION = 4
EVENTTYPE_ANSWERUNSEEN = 5
EVENTTYPE_ANSWERSEEN = 6

MessagePacket = namedtuple("MessagePacket","type msg subsystem progress progressLim")
MESSAGETYPE_GENERIC = 0
MESSAGETYPE_ERROR = 1
MESSAGETYPE_WAIT = 2
MESSAGETYPE_WAITOVER = 3
MESSAGETYPE_PROGRESS = 4
MESSAGETYPE_DEBUG = 5

ResultPacket = namedtuple("ResultPacket","type number")
RESULTTYPE_SUCCESS = 0
RESULTTYPE_ILLEGAL = 1

STATUS_GAMEINIT = 0
STATUS_GAMEACTIVE = 1
STATUS_GAMEOVER = 2


################################################################################
#### DATA STRUCTURES ###########################################################
#

EventMove = namedtuple("EventMove", "turn actor nodeStart nodeStop")
EventMove.__doc__ = \
"""A structure for recording one movement of a character piece.

Attributes:
    turn (int): The turn on which the piece was moved.
    actor (int): The relative ID of the player whose piece was moved.
    nodeStart (int): The ID of the node from which the piece was moved.
    nodeStop (int): The ID of the node to which the piece was moved.

"""


EventSuggestion = namedtuple("EventSuggestion",
    "turn actor character room weapon")
EventSuggestion.__doc__ = \
"""A structure for recording one suggestion made by a player.

Attributes:
    turn (int): The turn on which the suggestion was made.
    actor (int): The relative ID of the player making the suggestion.
    character (int): The card ID of the character suggested.
    room (int): The card ID of the room suggested.
    weapon (int): The card ID of the weapon suggested.

"""


EventPass = namedtuple("EventPass", "turn actor character room weapon")
EventPass.__doc__ = \
"""A structure for recording a player's inability to answer a suggestion.

Attributes:
    turn (int): The turn on which the event happened.
    actor (int): The relative ID of the player unable to answer.
    character (int): The card ID of the character suggested.
    room (int): The card ID of the room suggested.
    weapon (int): The card ID of the weapon suggested.

"""


EventAccusation = namedtuple("EventAccusation",
    "turn actor character room weapon")
EventAccusation.__doc__ = \
"""A structure for recording one accusation made.

Attributes:
    turn (int): The turn on which the accusation was made.
    actor (int): The relative ID of the accusing player.
    character (int): The card ID of the character accused.
    room (int): The card ID of the room accused.
    weapon (int): The card ID of the weapon accused.

"""


EventUnseenAnswer = namedtuple("EventUnseenAnswer",
    "turn actor consumer character room weapon")
EventUnseenAnswer.__doc__ = \
"""A structure for recording a suggestion answer whose card we did not see.

Attributes:
    turn (int): The turn on which the event happened.
    actor (int): The relative ID of the player answering the suggestion.
    consumer (int): The relative ID of the player making the suggestion.
    character (int): The card ID of the character suggested.
    room (int): The card ID of the room suggested.
    weapon (int): The card ID of the weapon suggested.

"""

EventSeenAnswer = namedtuple("EventSeenAnswer",
    "turn actor consumer card")
EventSeenAnswer.__doc__ = \
"""A structure for recording one suggestion answer whose card Velma saw.

Attributes:
    turn (int): The turn on which the event happened.
    actor (int): The relative ID of the player answering the suggestion.
    consumer (int): The relative ID of the player making the suggestion.
    card (int): The ID of the card shown in answer to the suggestion.

"""


################################################################################
#### CLASS DEFINITIONS #########################################################
#

class GameHost(object):
    """The minimal host class required to operate the Velma AI
    """
    def processmessage(self,pktMessage):
        """Process (display and distribute if necessary) a message packet
        
        Args:
            pktMessage (MessagePacket): Message packet.
        
        Returns:
            None
            
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def processevent(self,pktEvent):
        """Process an event packet
        
        Args:
            pktEvent (EventPacket): Event packet.
        
        Returns:
            ResultPacket
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        """
        raise NotImplementedError()
    #
    #
    def rolldice(self):
        """Return the result of one dice roll.
        
        Args:
            None
        
        Returns:
            ResultPacket: Status and the number rolled if applicable.
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def move(self,nodeStop):
        """Request a move.
        
        Args:
            nodeStop (int): ID of the node to be moved to.
        
        Returns:
            bool: True if successful, or False if the move is queried as 
                illegal.
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def suggest(self,character,room,weapon):
        """Make a suggestion.
        
        Args:
            character (int): ID of character card suggested.
            room (int): ID of room card suggested.
            weapon (int): ID of weapon card suggested.
        
        Returns:
            int: The number of players asked before receiving an answer, or none
                if play returned to the Detective with no answers to the 
                suggestion.
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def accuse(self,character,room,weapon):
        """Make an accusation.
        
        Args:
            character (int): ID of character card accused.
            room (int): ID of room card accused.
            weapon (int): ID of weapon card accused.
        
        Returns:
            bool: True if the accusation is proven correct; or False otherwise.
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def displaysuspicions(self):
        """Graph our suspicions given the current evidence.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            NotImplementedError (Derived classes should override this function)
        
        """
        raise NotImplementedError()
    #
    #
    def displaymovediagnostics(self,statsDict):
        """Graph intermediate statistics from move calculation."""
        raise NotImplementedError()

class GameServer(GameHost):
    """Game server class
    """
    #### VARIABLES #############################################################
    # Status of the game (initialising, active, over)
    statusGame = STATUS_GAMEINIT
    # Number of players in the game
    nPlayers = np.uint8(0)
    # Position of the dealer
    ixDealer = np.uint8(0)
    # Position of the active/moving player
    ixHotSeat = np.uint8(0)
    # Boolean np array: whether each player is still active in the game:
    playersActive = None
    # Character avatar index for each player (tuple)
    playerCharIxs = None
    # Character avatar locations (incl. unplayed)
    charLocations = game.CHARSTARTNODES
    # Weapon locations
    weapLocations = game.WEAPSTARTNODES
    # Client interfaces (message target objects) for each player
    playerClients = None
    # Game event log
    logEvents = None
    
    def reset(self):
        self.statusGame = STAT_GAMEINIT
        self.nPlayers = np.uint8(0)
        self.ixDealer = np.uint8(0)
        self.playersActive = None
        self.playerCharIxs = None
        self.charLocations = game.CHARSTARTNODES
        self.weapLocations = game.WEAPSTARTNODES
        self.playerClients = None
        self.logEvents = None
    
    


class GameLog(object):
    """Data architecture for a complete game log.
    
    Logging games creates opportunities for later, offline data analysis and
    correlation to uncover different playing strategies.
    """
    #### PLAYER INFORMATION ####################################################
    playerNames = ()
    
    #### GAME EVENTS ###########################################################
    moveLog = ()
    suggestionLog = ()
    passLog = ()
    accusationLog = ()
    unseenAnswerLog = ()
    seenAnswerLog = ()
    solution = ()
    
    #### FILE LOAD/SAVE FUNCTIONS ##############################################
    def load(logFile):
        """Load a game log from a given log file."""
        pass #TODO
    
    def save(forcedFileName=""):
        """Save a game log to storage (optional file name force)."""
        if (forcedFileName == ""):
            pass #TODO
        else:
            pass #TODO


class Detective(object):
    """A Class implementing an A.I. for the game of Cluedo.
    
    Detective objects may run a game in a stand-alone fashion using the run() 
    method; for dealing with minimal/stateless UIs such as velma.ui.
    
    Alternatively, Detective objects may participate in a game controlled by
    external software by use of the event_...() functions only.
    
    Integration with novel UIs or game control systems is by inheritance from
    this class with overrides to the outbound hook_...() functions. For further
    information, see the documentation.
    
    """
    #### SETTINGS "CONSTANTS" ##################################################
    # These CAPS-named members affect the performance (first section) or 
    # functional behaviour (second section) of the detective: Alter with care,
    # and certainly not during a game.
    #
    # When infering from stochastically generated hypotheses sets, maintain
    # HYPSAMPLECOUNT hypotheses.
    HYPSAMPLECOUNT = 100000
    # When the estimated number of remaining feasible scenarios falls below 
    # THRESHAPPROXHYPCOUNT, stop stochastically generating hypotheses and 
    # switch to enumerating all possible scenarios. (Note that the estimation
    # algorithm is currently a bit pants)
    THRESHAPPROXHYPCOUNT = 500000
    # When the largest of the murder scenario probabilities rises above 
    # PACCUSATIONTHRESH, the accusation is made when we are able (i.e. in the
    # correct room with the ability to suggest)
    PACCUSATIONTHRESH = 0.79
    #
    #
    # When SECRETIVE evaluates true, the Detective inhibits hook_...() function
    # calls such as diagnostics and plots which would display on-screen 
    # information providing an unfair advantage to competitors.
    #plots and diagnostics are inhibited to 
    # allow sensible competition against Velma (subject to somebody initially
    # telling her what cards she holds...)
    SECRETIVE = False
    # DBGSCENARIO is controlled by initialise(); but may be relied upon to 
    # evaluate to logical True when the detective is using a synthetic game
    # scenario and False otherwise
    DBGSCENARIO = None
    # Private: Controlled by initialise(): Contains a string representation of 
    # the synthetic game scenario when one is used.
    DBGSCENARIOREMINDER = True
    
    #### VARIABLES #############################################################
    # Host object for the game
    gameHost = None
    # Whether the game is over (i.e. drop turn loop and exit if using run())
    isGameOver = False
    # Whether the detective has been initialised with game information:
    isInitialised = False
    # Boolean np array: whether each player has been knocked out of the game:
    playersOusted = None
    # Number of players in the game (including the AI - range 2-6)
    nPlayers = np.uint8(0)
    # Dealer index (around from AI in direction of play - range 0-(nPlayers-1))
    ixDealer = np.uint8(0)
    # Number of cards held by each player (set by nPlayers and ixDealer)
    nCardsHeld = None
    # Character avatar index for each player (tuple)
    playerCharIxs = None
    # Set of card IDs held by the AI after the deal
    myCardSet = None
    # List of card IDS held by the AI after the deal
    myCards = None
    # Boolean np array: whether I've shown each player each card in my hand
    myCardsShownTo = None
    # List: total number of times I've shown each card in my hand
    myCardsShownCounts = None
    
    # Character avatar locations (incl. unplayed)
    charLocations = game.CHARSTARTNODES
    # Matrix of forbidden card locations on the basis of received evidence:
    # nPlayers+1 by NCARDS (the plus 1 is for the murder hand)
    forbidden = None
    # List of sets of cards forbidden for each player - updated alongside
    # forbidden matrix and queried as a faster alternative when generating or
    # manipulating hypotheses (since sets are hashed)
    forbiddenSets = []
    # Deal hypotheses (list [hypotheses] of lists [players] of sets [cards 
    # held])
    hypotheses = []
    # Have we yet reduced the possibilities far enough for precise inference?
    areHypothesesEnumerable = False
    # When we've entered our first room, we can reduce the scope of the board
    hasEnteredRoomYet = False
    # We can only make one suggestion in a room without leaving it and returning
    # later
    canSuggestInCurrentRoom = True
    # Move counter (from 0)
    ixTurn = 0
    # "Hot seat" - next player to move
    ixHotSeat = 0
    # Log of moves made by avatars/players
    logMoves = []
    # Log of suggestions made by players
    logSuggestions = []
    # Log of pass events: player unable to show card to answer suggestion
    logPasses = []
    # Log of suggestion answers shown to other people (i.e. we didn't see the 
    # card)
    logUnseenAnswers = []
    # Log of suggestion answers shown to us (pinpoints a card's location)
    logSeenAnswers = []
    # Log of incorrect accusations (surely never a long list!)
    logIncorrectAccusations = []
    
    # Marginal counts of each murder scenario appearing in hypotheses 
    # (maintained on the fly)
    hypCountByCharacter = np.zeros(game.NCHARS)
    hypCountByRoom = np.zeros(game.NROOMS)
    hypCountByWeapon = np.zeros(game.NWEAPS)
    hypCountByScenario = np.zeros((game.NCHARS,game.NROOMS,game.NWEAPS))
    pScenario = np.zeros((game.NCHARS,game.NROOMS,game.NWEAPS))
    scenarioEntropy = 0.
    
    
    #### CONSTRUCTOR ###########################################################
    #
    def __init__(self):
        """Constructor (empty)"""
        pass
    
    
    #### HOOK FUNCTIONS ########################################################
    # The following 'hook' functions are provided as minimal outbound interfaces
    # to allow easy integration of the detective class into other software.
    #
    # Simply inherit from this class and override these methods to override the 
    # default Velma UI.
    def hook_notifyerror(self,msg,subsystem=None):
        """Notify the user of an error.
        
        Args:
            msg (str): Message to display to the user.
            subsystem: Identifier for the source subsystem/function.
        
        Returns:
            None
            
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifyerror(msg,subsystem)
    #
    #
    def hook_notifydebug(self,msg,subsystem=None):
        """Notify the user of a debug message.
        
        Args:
            msg (str): Message to display to the user.
            subsystem: Identifier for the source subsystem/function.
        
        Returns:
            None
            
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifydebug(msg,subsystem)
    #
    #
    def hook_notifywait(self,operation,subsystem=None):
        """Notify the user of the start of a potentially long operation.
        
        Args:
            operation (str): Short, human-readable description of the operation
                in progress.
            subsystem: Identifier for the source subsystem/function.
        
        Returns:
            None
            
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifywait(operation,subsystem)
    #
    #
    def hook_notifywaitover(self,operation,subsystem=None):
        """Notify the user of the completion off a long operation.
        
        Args:
            operation (str): Short, human-readable description of the operation
                completed.
            subsystem: Identifier for the source subsystem/function.
        
        Returns:
            None
            
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifywaitover(operation,subsystem)
    #
    #
    def hook_notifyprogress(self,operation,progress,progressLim=1.,
            subsystem=None):
        """Notify the user of the extent of progress of an operation.
        
        Args:
            operation (str): Short, human-readable description of the operation
                in progress.
            progress (numeric): Amount of progress made so far.
            progressLim (numeric): Value of progress that will represent 
                completion of the operation.
            subsystem: Identifier for the source subsystem/function.
        
        Returns:
            None
            
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifydebug(operation+"... ("+str(progress)+"/"+str(progressLim)+")",
            subsystem)
    #
    #
    def hook_greet(self):
        """Notify the user when the detective starts a game.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        ui.greet()
    #
    #
    def hook_collectgamesetup(self):
        """Collect the game setup information.
        
        Args:
            None
        
        Returns:
            dict with keys:
            'nPlayers' (int): Number of players in the game.
            'ixDealer' (int): Number of players around from this Detective (in
                the direction of play) the dealer is sat.
            'playerCharCards' (iterable of int): Card IDs of the avatars to be
                played by each player.
            'playerCardHeldCounts' (iterable of int): Number of cards held by 
                each player after the deal.
            'myCards' (iterable of int): Card IDs held by this detective after
                the deal.
        
        Raises:
            None (Exception-neutral)
        
        This method is called when initialise() is invoked without the 
        information - allowing the thread of execution to be diverted from here
        to the actual task of collecting it.
        
        """
        result = ui.collectgamesetup()
        # The following unpacking/repacking is just to force the interface:
        return {'nPlayers':result['nPlayers'],'ixDealer':result['ixDealer'],
            'playerCharCards':result['playerCharCards'],
            'playerCardHeldCounts':result['playerCardHeldCounts'],
            'myCards':result['myCards']}
    #
    #
    def hook_observemove(self):
        """Observe a move and trigger the relevant event_...() callbacks.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        Invokes the UI to collect information on the current player's move:
        triggering the event_...() callbacks relevant to what we see.
        
        """
        ui.observemove(self,self.ixTurn,self.ixHotSeat)
    #
    #
    def hook_rolldice(self):
        """Return the result of one dice roll.
        
        Args:
            None
        
        Returns:
            int: The number rolled.
        
        Raises:
            None (Exception-neutral)
        
        """
        return ui.roll(self)
    #
    #
    def hook_notifymove(self,nodeStop):
        """Notify the user that Velma moves her character.
        
        Args:
            nodeStop (int): ID of the node to be moved to.
        
        Returns:
            bool: True if successful, or False if the move is queried as 
                illegal.
        
        Raises:
            None (Exception-neutral)
        
        """
        return ui.notifymove(self.ixTurn,self.ixHotSeat,
            self.charLocations[self.playerCharIxs[0]],nodeStop)
    #
    #
    def hook_suggest(self,character,room,weapon):
        """Make a suggestion.
        
        Args:
            character (int): ID of character card suggested.
            room (int): ID of room card suggested.
            weapon (int): ID of weapon card suggested.
        
        Returns:
            int: The number of players asked before receiving an answer, or none
                if play returned to the Detective with no answers to the 
                suggestion.
        
        Raises:
            None (Exception-neutral)
        
        Trigger the appropriate event_...() callbacks for each pass/show
        response.
        
        """
        return ui.suggest(self,self.ixTurn,self.ixHotSeat,character,room,weapon)
    #
    #
    def hook_accuse(self,character,room,weapon):
        """Make an accusation.
        
        Args:
            character (int): ID of character card accused.
            room (int): ID of room card accused.
            weapon (int): ID of weapon card accused.
        
        Returns:
            bool: True if the accusation is proven correct; or False otherwise.
        
        Raises:
            None (Exception-neutral)
        
        Trigger the appropriate event_...() callbacks for the response.
        
        """
        return ui.accuse(self,self.ixTurn,self.ixHotSeat,character,room,weapon)
    #
    #
    def hook_notifygameover(self,didIWin=None):
        """Notify the user of the termination of the game.
        
        Args:
            didIWin (optional Bool): Whether the Detective won the game.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        ui.notifygameover(didIWin)
    #
    #
    def hook_displaysuspicions(self):
        """Graph our suspicions given the current evidence.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        charMarginal = (np.array(self.hypCountByCharacter,dtype=np.float64)
            / np.sum(self.hypCountByCharacter))
        roomMarginal = (np.array(self.hypCountByRoom,dtype=np.float64)
            / np.sum(self.hypCountByRoom))
        weapMarginal = (np.array(self.hypCountByWeapon,dtype=np.float64)
            / np.sum(self.hypCountByWeapon))
        ui.plotscenariomarginals(charMarginal,roomMarginal,weapMarginal)
        ui.plotforbidden(self.forbidden)
    #
    #
    def hook_displaymovediagnostics(self,statsDict):
        """Graph intermediate statistics from move calculation."""
        ui.plotmovediagnostics(statsDict)
    
    
    #### EVENT FUNCTIONS #######################################################
    #
    def event_move(self,destNode=None,player=None):
        """Update detective state: A player has moved their piece.
        
        Args:
            destNode (int): ID of the node moved to.
            player (int): Relative ID of the player whose piece was moved.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        This event does *not* need to be invoked when a piece moves incidentally
        (e.g. it is transferred to a room after being suggested there) or when
        the move has been requested by this Detective object.
        
        """
        if destNode is None:
            # The call relates to the most recent move log entry
            event = self.logMoves[-1]
        else:
            if player is None:
                player = 0
            event = EventMove(self.ixTurn,player,
                self.charLocations[self.playerCharIxs[player]],destNode)
            self.logMoves.append(event)
        #
        # If we're the one moving, we can make suggestions in new rooms now
        if event.actor == 0:
            self.canSuggestInCurrentRoom = True
            if destNode in game.ROOMNODEIXS:
                self.hasEnteredRoomYet = True
        #
        # Move the character piece to the destination node
        self.charLocations[self.playerCharIxs[event.actor]] = event.nodeStop
    #
    #
    def event_suggestion(self,character=None,room=None,weapon=None,player=None):
        """Update detective state: A suggestion has been made.
        
        Args:
            character (int): ID of the character card suggested.
            room (int): ID of the room card suggested.
            weapon (int): ID of the weapon card suggested.
            player (int): Relative ID of the player making the suggestion.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        This event does *not* need to be invoked separately on a Detective 
        object when it makes the suggestion itself.
        
        """
        if character is None or room is None or weapon is None:
            # Call refers to the most recent log entry
            event = self.logSuggestions[-1]
        else:
            if player is None:
                player = 0
            event = EventSuggestion(self.ixTurn,player,character,room,weapon)
            self.logSuggestions.append(event)
        #
        ixChar = game.CHARINDEX[event.character]
        if event.actor == 0:
            # Our suggestion prohibits future suggestions without moving first
            self.canSuggestInCurrentRoom = False
        elif (ixChar == self.playerCharIxs[0] and
                (self.charLocations[self.playerCharIxs[0]] != event.actor)):
            # The suggestion moves our avatar to a new room and hence allows us
            # to make a suggestion without moving on the next turn
            self.canSuggestInCurrentRoom = True
        #
        # Move the character piece referenced to the room referenced
        self.charLocations[ixChar] = game.ROOMCARDNODES[event.room]
    #
    #
    def event_pass(self,character=None,room=None,weapon=None,player=None):
        """Update detective state: A player held no cards from a suggestion.
        
        Args:
            character (int): ID of the character card suggested.
            room (int): ID of the room card suggested.
            weapon (int): ID of the weapon card suggested.
            player (int): Relative ID of the player unable to answer.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        if character is None or room is None or weapon is None:
            event = self.logPasses[-1]
        else:
            if player is None:
                player = 0
            event = EventPass(self.ixTurn,player,character,room,weapon)
            self.logPasses.append(event)
        #
        # Forbidden card locations update
        self.forbidden[event.actor,event.character] = True
        self.forbiddenSets[event.actor].add(event.character)
        if all(self.forbidden[0:self.nPlayers,event.character]):
            charsForbidden = game.ALLOWEDCHARS.copy()
            charsForbidden.remove(event.character)
            for char in charsForbidden:
                self.forbidden[self.nPlayers,char] = True
                self.forbiddenSets[self.nPlayers].add(char)
        self.forbidden[event.actor,event.room] = True
        self.forbiddenSets[event.actor].add(event.room)
        if all(self.forbidden[0:self.nPlayers,event.room]):
            roomsForbidden = game.ALLOWEDROOMS.copy()
            roomsForbidden.remove(event.room)
            for room in roomsForbidden:
                self.forbidden[self.nPlayers,room] = True
                self.forbiddenSets[self.nPlayers].add(room)
        self.forbidden[event.actor,event.weapon] = True
        self.forbiddenSets[event.actor].add(event.weapon)
        if all(self.forbidden[0:self.nPlayers,event.weapon]):
            weapsForbidden = game.ALLOWEDWEAPS.copy()
            weapsForbidden.remove(event.weapon)
            for weapon in weapsForbidden:
                self.forbidden[self.nPlayers,weapon] = True
                self.forbiddenSets[self.nPlayers].add(weapon)
        #
        # Remove invalidated hypotheses (this can't be done by simple list 
        # comprehension because incremental updates of counts are required too)
        disallowed = set([event.character,event.room,event.weapon])
        hypsNew = []
        for ixHyp in range(len(self.hypotheses)):
            if len(disallowed & self.hypotheses[ixHyp][event.actor]):
                self.removehypfromcounts(ixHyp)
            else:
                hypsNew.append(self.hypotheses[ixHyp])
        #        
        # Replace removed hypotheses and update statistics
        self.hook_notifydebug(str(len(self.hypotheses)-len(hypsNew))+
            ' hypotheses invalidated',"Velma.event_pass")
        self.hypotheses = hypsNew
        self.rebuildhypotheses()
        self.updatestats()
    #
    #
    def event_seenresponse(self,card=None,shower=None,viewer=None):
        """Update detective state: the detective saw a suggestion response.
        
        Args:
            card (int): The ID of the card shown in response.
            shower (int): The relative ID of the answerer of the suggestion.
            viewer (int): The relative ID of the suggesting player.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        This event does *not* need to be invoked separately on a Detective 
        object when it showed the card itself.
        
        """
        if card is None or (shower is None and viewer is None):
            event = self.logSeenAnswers[-1]
        else:
            if shower is None:
                shower = 0
            elif viewer is None:
                viewer = 0
            event = EventSeenAnswer(self.ixTurn,shower,viewer,card)
            self.logSeenAnswers.append(event)
        #
        # Forbidden card locations update
        for ixPlayer in range(self.nPlayers+1):
            if ixPlayer != event.actor:
                self.forbidden[ixPlayer,event.card] = True
                self.forbiddenSets[ixPlayer].add(event.card)
            else:
                # This is the one place this card actually is.
                # This phrase is not absolutely necessary - but think of it as
                # double-entry helpfulness
                self.forbidden[ixPlayer,event.card] = False
                try:
                    self.forbiddenSets[ixPlayer].remove(event.card)
                except:
                    pass
        #
        # Remove invalidated hypotheses (this can't be done by simple list 
        # comprehension because incremental updates of counts are required too)
        hypsNew = []
        for ixHyp in range(len(self.hypotheses)):
            if event.card in self.hypotheses[ixHyp][event.actor]:
                hypsNew.append(self.hypotheses[ixHyp])
            else:
                self.removehypfromcounts(ixHyp)
        self.hook_notifydebug(str(len(self.hypotheses)-len(hypsNew))+
            ' hypotheses invalidated',"Velma.event_seenresponse")
        self.hypotheses = hypsNew
        self.rebuildhypotheses()
        self.updatestats()
    #
    #
    def event_unseenresponse(self,character=None,room=None,weapon=None,
            shower=None,viewer=None):
        """Update detective state: A player secretly answered a suggestion.
        
        Args:
            character (int): The ID of the character card suggested.
            room (int): The ID of the room card suggested.
            weapon (int): The ID of the weapon card suggested.
            shower (int): The relative ID of the answerer of the suggestion.
            viewer (int): The relative ID of the suggesting player.
        
        Returns:
            None
        
        Raises:
            None
        
        """
        if (character is None or room is None or weapon is None or 
                (shower is None and viewer is None)):
            event = self.logPasses[-1]
        else:
            if shower is None:
                shower = 0
            elif viewer is None:
                viewer = 0
            event = EventUnseenAnswer(self.ixTurn,shower,viewer,character,room,
                weapon)
            self.logUnseenAnswers.append(event)
        #
        # No information added to forbidden matrix
        #
        # Remove invalidated hypotheses (this can't be done by simple list 
        # comprehension because incremental updates of counts are required too)
        present = set([event.character,event.room,event.weapon])
        hypsNew = []
        for ixHyp in range(len(self.hypotheses)):
            if len(present & self.hypotheses[ixHyp][event.actor]):
                hypsNew.append(self.hypotheses[ixHyp])
            else:
                self.removehypfromcounts(ixHyp)
        self.hook_notifydebug(str(len(self.hypotheses)-len(hypsNew))+
            ' hypotheses invalidated',"Velma.event_unseenresponse")
        self.hypotheses = hypsNew
        self.rebuildhypotheses()
        self.updatestats()
    #
    #
    def event_accusation(self,character=None,room=None,weapon=None,player=None):
        """Update detective state: An accusation has been made.
        
        Args:
            character (int): The ID of the character card accused.
            room (int): The ID of the room card accused.
            weapon (int): The ID of the weapon card accused.
            player (int): The relative ID of the accusing player.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        This event does *not* need to be invoked separately on a Detective 
        object when it makes the accusation itself.
        
        """
        pass
    #
    #
    def event_accusationcorrect(self,
            character=None,room=None,weapon=None,player=None):
        """Update detective state: An accusation has been proven correct.
        
        Args:
            character (int): The ID of the character card accused.
            room (int): The ID of the room card accused.
            weapon (int): The ID of the weapon card accused.
            player (int): The relative ID of the accusing player.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        if player is None:
            player = 0
        #
        self.isGameOver = True
        if player == 0:
            self.hook_notifygameover(didIWin=True)
        else:
            self.hook_notifygameover(didIWin=False)
    #
    #
    def event_accusationwrong(self,
            character=None,room=None,weapon=None,player=None):
        """Update detective state: An accusation has been proven wrong.
        
        Args:
            character (int): The ID of the character card accused.
            room (int): The ID of the room card accused.
            weapon (int): The ID of the weapon card accused.
            player (int): The relative ID of the accusing player.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        if character is None or room is None or weapon is None:
            event = self.logIncorrectAccusations[-1]
        else:
            if player is None:
                player = 0
            event = AccusationRecord(self.ixTurn,
                character,room,weapon,player)
            self.logIncorrectAccusations.append(event)
        #
        # Remove player from game
        self.playersOusted[player] = True
        #
        # Remove invalidated hypotheses
        accusation = (game.CHARINDEX[character],game.ROOMINDEX[room],
            game.WEAPINDEX[weapon])
        hypsNew = []
        for ixHyp in range(len(self.hypotheses)):
            thisHyp = self.hypotheses[ixHyp]
            # Debug: Check type of hyp[-1] is tuple and not list or set.
            assert thisHyp[-1] == tuple(thisHyp[-1])
            #
            if thisHyp[-1] == accusation:
                self.removehypfromcounts(ixHyp)
            else:
                hypsNew.append(self.hypotheses[ixHyp])
        #        
        # Replace removed hypotheses and update statistics
        self.hook_notifydebug(str(len(self.hypotheses)-len(hypsNew))+
            ' hypotheses invalidated',"Velma.event_accusationwrong")
        self.hypotheses = hypsNew
        self.rebuildhypotheses()
        self.updatestats()
    
    
    #### INTERNAL FUNCTIONS ####################################################
    #
    def removehypfromcounts(self,ixHyp):
        """Revise hypothesis count states to reflect an imminent removal.
        
        Args:
            ixHyp (int): The index (in self.hypotheses) of the hypothesis to be
                removed.
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        """
        # hypothesis[-1] is tuple of (ixChar,ixRoom,ixWeap)
        # Use numpy tuple indexing for the scenario mx:
        self.hypCountByScenario[self.hypotheses[ixHyp][-1]] -= 1
        # For 1D numpy arrays, use scalar indexing:
        self.hypCountByCharacter[self.hypotheses[ixHyp][-1][0]] -= 1
        self.hypCountByRoom[self.hypotheses[ixHyp][-1][1]] -= 1
        self.hypCountByWeapon[self.hypotheses[ixHyp][-1][2]] -= 1
    #
    #
    def genfeasiblehypothesis(self):
        """Generate a random hypothesis satisfying all current constraints.
        
        Args:
            None
        
        Returns:
            dict with keys:
            'hypothesis': A randomly generated hypothesis satisfying all 
                recorded constraints.
            'genAttempts': Number of attempts taken to generate hypothesis.
        
        Raises:
            None (Exception-neutral)
        
        For this task, simple rejection sampling (generating totally random 
        deals and rejecting samples that violate constraints) would be very 
        inefficient.
        
        Conversely, a highly complex algorithm would be required to account for 
        all constraints whilst sampling fairly.
        
        Therefore, this method uses a hybrid approach by explicitly satisfying 
        many of the constraints, and rejecting against the few that remain.
        
        """
        hypValid = False
        genAttempts = 0
        hypothesis = []
        while hypValid == False:
            genAttempts += 1.
            # Generate a hypothesis:
            #
            # 1. Deal myself the hand I know I have
            hypothesis = [set() for ix in range(self.nPlayers+1)]
            hypValid = True
            hypothesis[0] = self.myCardSet.copy()
            dealt = self.myCardSet.copy()
            #
            # 2. Loop through all the seen answer constraints dealing cards to 
            #   known locations
            for constraint in self.logSeenAnswers:
                if not constraint.card in hypothesis[constraint.actor]:
                    hypothesis[constraint.actor].add(constraint.card)
                    dealt.add(constraint.card)
            #
            # 3. Loop through the unseen answer constraints, 
            #   satisfying each in turn by random allocation of one
            #   of the three cards they reference, in such a way
            #   that the other (pass, seen-answer) constraints are 
            #   observed.
            for constraint in self.logUnseenAnswers:
                constraintset = set(
                    [constraint.character,constraint.room,constraint.weapon])
                #
                if not len(constraintset & 
                        hypothesis[constraint.actor]):
                    # This constraint is not already satisfied.
                    #
                    # Attempt to deal the mentioned player another
                    # card: Can they fit it in their hand?
                    if (len(hypothesis[constraint.actor]) <
                            self.nCardsHeld[constraint.actor]):
                        #
                        # Check which cards we could allowably give
                        # the player to satisfy the constraint
                        allowedCards = (constraintset - dealt 
                            - self.forbiddenSets[constraint.actor])
                        if len(allowedCards):
                            # Constraint satisfied
                            chosenCard = random.sample(allowedCards,1)[0]
                            hypothesis[constraint.actor].add(chosenCard)
                            dealt.add(chosenCard)
                        else:
                            # Constraint unsatisfiable due to 
                            # earlier stochastic allocations -
                            # abort hypothesis generation
                            hypValid = False
                            break
                    else:
                        # Constraint unsatisfiable due to earlier
                        # stochastic allocations - abort hypothesis
                        # generation
                        hypValid = False
                        break
            #
            # 4. Select a murder scenario from what's left or abort
            #   if the previous process didn't work out well
            if hypValid:
                try:
                    murderer = random.sample((game.ALLOWEDCHARS
                        - dealt) - self.forbiddenSets[-1],1)[0]
                    dealt.add(murderer)
                    ixChar = game.CHARINDEX[murderer]
                    murderRoom = random.sample((game.ALLOWEDROOMS
                        - dealt) - self.forbiddenSets[-1],1)[0]
                    dealt.add(murderRoom)
                    ixRoom = game.ROOMINDEX[murderRoom]
                    murderWeap = random.sample((game.ALLOWEDWEAPS
                        - dealt) - self.forbiddenSets[-1],1)[0]
                    dealt.add(murderWeap)
                    ixWeap = game.WEAPINDEX[murderWeap]
                    #
                    hypothesis[-1] = (ixChar,ixRoom,ixWeap)
                except ValueError:
                    # If we land here, the unseen-answer constraint
                    # satisfaction process left us with no cards
                    # from one or more of the three necessary 
                    # categories - so the hypothesis is void!
                    hypValid = False
                    continue
            else:
                # Hypothesis invalid = try again from the start
                continue
            #
            # 5. If we get here, we can randomly allocate the 
            # remaining undealt cards subject to the forbidden locations - all 
            # unseen and seen answer constraints have been satisfied
            shuffledDeck = list(game.ALLOWEDCARDS - dealt)
            random.shuffle(shuffledDeck)
            for card in shuffledDeck:
                # Deal card to first player who is not forbidden from 
                # receiving it
                recipient = next((ix for ix in range(self.nPlayers) 
                    if (not self.forbidden[ix,card]) and 
                    (len(hypothesis[ix]) < self.nCardsHeld[ix])
                    ),None)
                #    
                if recipient is None:
                    # We ended up with nobody to allocate this card to: the
                    # hypothesis is invalidated (by pass constraints) due
                    # to earlier random dealings
                    hypValid = False
                    break
                else:
                    hypothesis[recipient].add(card)
                    dealt.add(card)
            #
            # 6. Finally, just check the hypothesis isn't invalidated by any 
            # incorrect accusations we've seen. This is by rejection sampling
            # because it should very rarely happen!
            for wrongAcc in self.logIncorrectAccusations:
                if ((murderer,murderRoom,murderWeap) == 
                        (wrongAcc.character,wrongAcc.room,wrongAcc.weapon)):
                    hypValid = False
            #
            # Either hypValid = False (and loop will run again), or a valid 
            # hypothesis is generated.
        #
        # Debug check: All cards must have been dealt for the hypothesis
        assert dealt == game.ALLOWEDCARDS, \
            "'Valid' hypothesis generated without dealing full pack!"
        #
        return {'hypothesis':hypothesis,'genAttempts':genAttempts}
    #
    #
    def rebuildhypotheses(self):
        """Regenerate the hypothesis list after logical reduction.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        When information is gained, old hypotheses are rejected. If inexact/
        statistical inference is being used, we must therefore sample some new
        possible hypotheses from time to time to keep our sample suitably large
        and representative.
        
        This function estimates the number of feasible deals left under the
        current constraints. If this count is above THRESHAPPROXHYPCOUNT, 
        the hypothesis list is regenerated to the target length. If below,
        the full set of possible deals is enumerated and future rebuilds are
        no-ops.
        
        """
        if not (len(self.hypotheses) or self.areHypothesesEnumerable):
            # We are building hypothesis database for the first time (a 
            # potentially slow process)
            self.hook_notifywait("Building initial hypothesis database")
        # This function only has anything to do if we're starting out still in 
        # the inexact inference stage
        if not self.areHypothesesEnumerable:
            # Check whether inexact inference is still appropriate at this time
            #
            # Number of possibilities is approx equal to (maybe leq?)
            # # feasible murderers * # feasible rooms * # feasible weapons *
            #   (for each player in turn from deal) nCr where r is nCardsHeld
            #   and n is min(feasiblecards,remainingcardsindeck)
            # Spaces to deal into after eliminating known card positions
            dealSpaces = list(self.nCardsHeld)
            # Recognise the fixedness of all cards narrowed down to one possible
            # location
            knownCards = set(())
            # Cards left for dealing to players
            cardsLeft = game.NCARDS - 3 # -3 due to murder set
            for card in game.ALLOWEDCARDS:
                if np.sum(self.forbidden[:,card]) == self.nPlayers:
                    ixAllowed = next((ix for ix in range(self.nPlayers+1) 
                        if not self.forbidden[ix,card]))
                    knownCards.add(card)
                    
                    if ixAllowed != self.nPlayers:
                        # Card is isolated to a location not in the murder set:
                        # subtract another card from those dealable to players
                        cardsLeft -= 1
                        dealSpaces[ixAllowed] -= 1
            #
            nHypsApprox = (
                (game.NCHARS - 
                np.sum(self.forbidden[self.nPlayers,list(game.ALLOWEDCHARS)]))*
                (game.NROOMS -
                np.sum(self.forbidden[self.nPlayers,list(game.ALLOWEDROOMS)]))*
                (game.NWEAPS -
                np.sum(self.forbidden[self.nPlayers,list(game.ALLOWEDWEAPS)]))
                )
            #
            for ixPlayer in np.array(range(self.ixDealer,
                    self.ixDealer+self.nPlayers)) % self.nPlayers:
                nHypsApprox *= nCr(
                    np.min((cardsLeft,
                    game.NCARDS-np.sum(self.forbidden[ixPlayer,:])))
                    ,dealSpaces[ixPlayer],exact=True)
                cardsLeft -= dealSpaces[ixPlayer]
            #
            if nHypsApprox < self.THRESHAPPROXHYPCOUNT:
                self.hook_notifydebug('Approx scenario count ' + 
                    str(nHypsApprox) +
                    ' under threshold',"Velma.rebuildhypotheses")
            else:
                self.hook_notifydebug('High scenario count '+ str(nHypsApprox) +
                    ' - Building ' + 
                    str(self.HYPSAMPLECOUNT-len(self.hypotheses)) + 
                    ' hypotheses',"Velma.rebuildhypotheses")
            #
            if nHypsApprox < self.THRESHAPPROXHYPCOUNT:
                # Replace the hypotheses with the full, enumerated set of 
                # possible deals under the known conditions. (Might be a long
                # process!)
                self.hook_notifywait("Switching from stochastic to enumerated \
inference: Rebuilding hypothesis database")
                tStart = time.time()
                #
                # NOTE that the last element starts out as a list but is re-
                # cast to a tuple (necessary) in stage 3 murder scenario 
                # selection
                self.hypotheses = [
                    ([set() for ix in range(self.nPlayers)]+[[-1,-1,-1]])]
                dealt = [set()]
                #
                # 1. Deal all cards whose location is known exactly
                for card in game.ALLOWEDCARDS:
                    if np.sum(self.forbidden[:,card]) == self.nPlayers:
                        ixHolder = [ix for ix in range(self.nPlayers+1)
                            if not self.forbidden[ix,card]][0]
                        if ixHolder < self.nPlayers:
                            self.hypotheses[0][ixHolder].add(card)
                        else:
                            ixChar = game.CHARINDEX.get(card,None)
                            if ixChar is None:
                                ixRoom = game.ROOMINDEX.get(card,None)
                                if ixRoom is None:
                                    ixWeap = game.WEAPINDEX.get(card,None)
                                    # ixWeap can't be none - otherwise card 
                                    # would be invalid!
                                    self.hypotheses[0][ixHolder][2] = ixWeap
                                else:
                                    self.hypotheses[0][ixHolder][1] = ixRoom
                            else:
                                self.hypotheses[0][ixHolder][0] = ixChar
                        dealt[0].add(card)
                #
                # 2. Loop through unseen answer constraints, satisfying each in
                # turn by allocating one card but exploring ALL POSSIBLE ways - 
                # cloning the working variables
                for constraint in self.logUnseenAnswers:
                    constraintset = set([
                        constraint.character,constraint.room,constraint.weapon])
                    
                    newHyps = []
                    newDealt = []
                    
                    for ixHyp in range(len(self.hypotheses)):
                        if len(constraintset & 
                                self.hypotheses[ixHyp][constraint.shower]):
                            # Constraint already satisfied
                            newHyps.append(self.hypotheses[ixHyp])
                            newDealt.append(dealt[ixHyp])
                        else:
                            # Need to satisfy this constraint - can the 
                            # mentioned player take any further cards in their 
                            # hand? (if not, no action is taken and the 
                            # hypothesis does not make it to the next stage)
                            if (len(self.hypotheses[ixHyp][constraint.shower])
                                        < self.nCardsHeld[constraint.shower]):
                                # Yes they can: Check which cards could be given
                                # to the player in this scenario to satisfy the
                                # constraint
                                allowedCards = (constraintset - dealt[ixHyp]
                                    - self.forbiddenSets[constraint.shower])
                                #
                                for chosenCard in allowedCards:
                                    # Constraint satisfied
                                    # Remember to deep copy!
                                    thisHyp = [set(cardSet) for cardSet in
                                        self.hypotheses[ixHyp]]
                                    thisHyp[-1] = list(
                                        self.hypotheses[ixHyp][-1])
                                    thisDealt = dealt[ixHyp].copy()
                                    #
                                    thisHyp[constraint.shower].add(chosenCard)
                                    thisDealt.add(chosenCard)
                                    newHyps.append(thisHyp)
                                    newDealt.append(thisDealt)
                    #
                    self.hypotheses = newHyps
                    dealt = newDealt
                    
                # 3. Select murder scenarios from the remaining cards for each
                # hypothesis
                newHyps = []
                newDealt = []
                for ixHyp in range(len(self.hypotheses)):                    
                    if self.hypotheses[ixHyp][-1][0] >= 0:
                        # Hypothesis already has a murderer: There is only one
                        # possibility
                        charSet = set([game.CHARS[
                            self.hypotheses[ixHyp][-1][0]]]) #
                    else:
                        # Hypothesis may have murderers from the following set:
                        charSet = (game.ALLOWEDCHARS-dealt[ixHyp] - 
                            self.forbiddenSets[-1])
                    # If the length of charSet is still zero, the hypothesis is
                    # impossible and the loop below will ensure it's dropped 
                    # from the list
                    #
                    # Repeat the above for room and weapon:
                    if self.hypotheses[ixHyp][-1][1] >= 0:
                        roomSet = set([game.ROOMS[
                            self.hypotheses[ixHyp][-1][1]]])
                    else:
                        roomSet = (game.ALLOWEDROOMS-dealt[ixHyp] - 
                            self.forbiddenSets[-1])
                    if self.hypotheses[ixHyp][-1][2] >= 0:
                        weapSet = set([game.WEAPS[
                            self.hypotheses[ixHyp][-1][2]]])
                    else:
                        weapSet = (game.ALLOWEDWEAPS - 
                            dealt[ixHyp]-self.forbiddenSets[-1])
                    #
                    # Loop through characters, rooms and weapons to add all 
                    # possible hypotheses to the list
                    for murderer in charSet:
                        for murderRoom in roomSet:
                            for murderWeap in weapSet:
                                # Copy the hypothesis (casting the last element
                                # to a set is no problem because we'll overwrite
                                # it as tuple in a mo and it's already in the
                                # wrong type anyway)
                                thisHyp = [set(cardSet) for cardSet in
                                    self.hypotheses[ixHyp]]
                                thisDealt = dealt[ixHyp].copy()
                                #
                                # Assign as tuple (was previously list!):
                                thisHyp[-1] = (
                                    game.CHARINDEX[murderer],
                                    game.ROOMINDEX[murderRoom],
                                    game.WEAPINDEX[murderWeap])
                                thisDealt.update(
                                    [murderer,murderRoom,murderWeap])
                                newHyps.append(thisHyp)
                                newDealt.append(thisDealt)
                self.hypotheses = newHyps
                dealt = newDealt
                #
                # 4. Distribute the remaining cards in all possible ways (all
                # constraints are satisfied)
                hypsComplete = 0
                while hypsComplete < len(self.hypotheses):
                    newHyps = []
                    newDealt = []
                    hypsComplete = 0
                    for ixHyp in range(len(self.hypotheses)):
                        if dealt[ixHyp] == game.ALLOWEDCARDS:
                            # All cards are dealt in this hypothesis
                            newHyps.append(self.hypotheses[ixHyp])
                            newDealt.append(dealt[ixHyp].copy())
                            hypsComplete += 1
                        else:
                            # One or more cards are left to deal.
                            dealtCard = (game.ALLOWEDCARDS-dealt[ixHyp]).pop()
                            thisNewDealt = dealt[ixHyp].copy()
                            thisNewDealt.add(dealtCard)
                            # Which people can receive it?
                            destinations = []
                            for ixPlayer in range(1,self.nPlayers):
                                if (len(self.hypotheses[ixHyp][ixPlayer]) <
                                        self.nCardsHeld[ixPlayer] and
                                        not dealtCard in 
                                        self.forbiddenSets[ixPlayer]):
                                    destinations.append(ixPlayer)
                            #
                            # Create a new hypothesis in the new list for each 
                            # possible destination of the card
                            for ixPlayer in destinations:
                                #thisHyp = copy.deepcopy(self.hypotheses[ixHyp])
                                thisHyp = [set(cardSet) for cardSet in
                                    self.hypotheses[ixHyp]]
                                thisHyp[-1] = tuple(self.hypotheses[ixHyp][-1])
                                ##thisHyp = [set(cardSet) for cardSet in 
                                ##        self.hypotheses[ixHyp]]
                                thisHyp[ixPlayer].add(dealtCard)
                                newHyps.append(thisHyp)
                                newDealt.append(thisNewDealt.copy())
                    #    
                    self.hypotheses = newHyps
                    dealt = newDealt
                #    
                # Finally, trim off any hypotheses we've generated that are 
                # invalidated by incorrect accusations. (This is a tacked-on
                # kinda check because we expect invalid hypotheses very rarely!)
                for wrongAcc in self.logIncorrectAccusations:
                    self.hypotheses = filter(
                        lambda x: x[-1] != (murderer,murderRoom,murderWeap),
                        self.hypotheses)
                #                
                # All hypotheses in self.hypotheses are complete (dealt all 
                # cards), and self.hypotheses contains all possible hypotheses
                # satisfying the given conditions.  
                tStop = time.time()
                self.hook_notifywaitover("Switching from stochastic to \
enumerated inference: Rebuilding hypothesis database")
                self.hook_notifydebug('Enumerated ' + 
                    str(len(self.hypotheses)) + ' possible outcomes in ' + 
                    str(tStop-tStart) + ' seconds', "Velma.rebuildhypotheses")
                #    
                # Update scenario counts to new hypothesis list
                self.hypCountByScenario = np.zeros(
                    self.hypCountByScenario.shape)
                self.hypCountByCharacter = np.zeros(
                    self.hypCountByCharacter.shape)
                self.hypCountByRoom = np.zeros(self.hypCountByRoom.shape)
                self.hypCountByWeapon = np.zeros(self.hypCountByWeapon.shape)
                for ixHyp in range(len(self.hypotheses)):
                    self.hypCountByScenario[self.hypotheses[ixHyp][-1]] += 1
                    self.hypCountByCharacter[self.hypotheses[ixHyp][-1][0]] += 1
                    self.hypCountByRoom[self.hypotheses[ixHyp][-1][1]] += 1
                    self.hypCountByWeapon[self.hypotheses[ixHyp][-1][2]] += 1
                #
                # Hypotheses successfully enumerated: From now on it's all
                # about reduction!
                self.areHypothesesEnumerable = True
            else:
                # Still too many possibilities to enumerate - regenerate some
                # more samples to compensate for losses due to hypothesis 
                # rejection.
                #
                # Some but not all of the constraints can be applied in the
                # generating algorithm - so some degree of rejection sampling
                # is required to produce the corect number.
                genAttempts = np.zeros(
                    (self.HYPSAMPLECOUNT-len(self.hypotheses),))
                tStart = time.time()
                # Loop through generating samples
                for ixGen in range(self.HYPSAMPLECOUNT-len(self.hypotheses)):
                    result = self.genfeasiblehypothesis()
                    hypothesis = result['hypothesis']
                    genAttempts[ixGen] = result['genAttempts']
                    #
                    self.hypotheses.append(hypothesis)
                    # Update scenario counts
                    # Since hypothesis[-1] is a tuple of char, room, weap 
                    # indices, we can index directly!
                    self.hypCountByScenario[hypothesis[-1]] += 1
                    self.hypCountByCharacter[hypothesis[-1][0]] += 1
                    self.hypCountByRoom[hypothesis[-1][1]] += 1
                    self.hypCountByWeapon[hypothesis[-1][2]] += 1
                
                # Successfully generated enough feasible hypotheses to bring
                # total hypothesis count back to nominal
                self.hook_notifydebug('Done in ' + str(time.time()-tStart) + 
                    's with ' + str(np.mean(genAttempts)) + ' avg gen attempts',
                    "Velma.rebuildhypotheses")
            #
            self.updatestats()
        else:
            self.hook_notifydebug('Precise inference: ' + 
                str(len(self.hypotheses)) + ' hypotheses remaining',
                "Velma.rebuildhypotheses")  
    
    
    def calculateroomhops(self,nodeStart):
        """Return the minimum "hop" distances from nodeStart to all rooms.
        
        Args:
            nodeStart (int): The board node ID from which to start the search.
        
        Returns:
            np.array: (game.NROOMS x 1) array of distances from nodeStart to 
                each room on the board, in terms of numbers of squares.
        
        Raises:
            None (Exception-neutral)
        
        This algorithm ignores routes passing through other rooms en route.
        
        If nodeStart is a room, secret passages leading out of nodeStart are
        examined.
        
        """
        roomDists = np.tile(-1,(game.NROOMS,))
        locs = [nodeStart]
        nodesVisited = set((nodeStart,))
        #
        # If we have already entered a room, there are some squares we can 
        # eliminate with certainty: even for any possible configuration of
        # player pieces on the board.
        #if self.hasEnteredRoomYet:
        #    GAMEBOARD = game.TRIMMEDNODES
        #else:
        GAMEBOARD = game.BOARDNODES
        #
        ixRoomStart = game.ROOMNODEIXS.get(nodeStart,None)
        if not ixRoomStart is None:
            # If we start in a room, set the distance to this room to zero and
            # set the distances to any rooms connected by secret passages to one
            roomDists[ixRoomStart] = 0
            passageNode = game.PASSAGES.get(nodeStart,None)
            if not passageNode is None:
                ixRoomPassage = game.ROOMNODEIXS.get(passageNode,None)
                if not ixRoomPassage is None:
                    roomDists[ixRoomPassage] = 1
                    nodesVisited.add(passageNode)
        #
        # For remaining rooms, go hunting for the fastest route!
        moveDist = 0
        while any(roomDists < 0) and len(locs):
            moveDist += 1
            newLocs = []
            for ixLoc in range(len(locs)):
                loc = locs[ixLoc]
                for newLoc in GAMEBOARD[loc]:
                    # Nodes are only visited if they've not been reached before
                    # (this algorithm finds fastest routes, not all possible 
                    # routes)
                    if not newLoc in nodesVisited:
                        # If the new location is a room, we enter it and 
                        # terminate whether or not someone else is present
                        if newLoc in game.ALLOWEDROOMNODES:
                            roomDists[game.ROOMNODEIXS[newLoc]] = moveDist
                            nodesVisited.add(newLoc)
                        else:
                            # Given that the new location is not a room, we may
                            # only enter if nobody else is stood on this square
                            if not newLoc in self.charLocations:
                                newLocs.append(newLoc)
                                nodesVisited.add(newLoc)
            locs = newLocs
        #
        return roomDists
    #
    #
    def calculateinterroomspans(self):
        """Return the matrix of "span" distances between all rooms.
        
        The "span" [i,j] is the expected number of dice throws necessary to move
        from room index i to room index j: Minimised over the possible routes 
        including consideration for routes via any sequence of other rooms.
        
        """
        # Calculate the matrix of distances between rooms without entering other
        # rooms en route; and convert to "span" - expected throws:
        interRoomHopSpans = game.dicerollstomove(np.array(
            [self.calculateroomhops(room) for room in game.ROOMNODES]))
        #
        # For routes travelling via rooms, we sum the expected turns for each
        # element of the journey.
        #
        # The true distance (in expected turns) between rooms is that of the
        # shortest possible route, which may go through other rooms on the way.
        # For each room, explore all possible compound routes to other rooms.
        # Use the usual trick of propagating particles which branch at every 
        # possible junction.
        interRoomSpans = interRoomHopSpans.copy()
        #
        # Route (list of nodes) taken by each particle: Initialised to one 
        # particle starting in each room
        routes = [[ix,] for ix in range(len(game.ROOMS))]
        # Set of nodes already visited by each particle
        visited = [set((ix,)) for ix in range(len(game.ROOMS))]
        # Route length travelled by each particle (which could be evaluated from
        # 'routes' at each iteration, but is calculated cumulatively for speed)
        routeSpans = [0. for ix in range(len(game.ROOMS))]
        #
        # Set of all room indices just used for generation of next destinations
        ALLROOMIXS = set(range(len(game.ROOMS)))
        #
        # Whilst there are unfinished particles left to propagate
        while len(routes):
            newRoutes = []
            newVisited = []
            newRouteSpans = []
            # For each particle:
            for ix in range(len(routes)):
                # For each possible next move (all nodes that haven't been
                # visited by this particle before):
                for newLoc in (ALLROOMIXS - visited[ix]):
                    # Calculate the total route length of making this move
                    newRouteSpan = routeSpans[ix]+interRoomHopSpans[
                        routes[ix][-1],newLoc]
                    # If the new route is still shorter than the longest inter-
                    # -room distance from this starting node, then it's worth
                    # propagating as it may shortcut one of these distances.
                    if any(newRouteSpan < interRoomSpans[routes[ix][0],:]):
                        # Branch the particle to take this route (as well as all 
                        # others)
                        newRoute = [node for node in routes[ix]] # List copy
                        newRoute.append(newLoc)
                        newVisit = visited[ix].copy() # Set copy
                        newVisit.add(newLoc)
                        newRoutes.append(newRoute)
                        newVisited.append(newVisit)
                        newRouteSpans.append(newRouteSpan)
                        # Check whether this route between start and finish
                        # constitutes a shortcut
                        if newRouteSpan < interRoomSpans[routes[ix][0],newLoc]:
                            interRoomSpans[routes[ix][0],newLoc] = newRouteSpan
            #
            routes = newRoutes
            visited = newVisited
            routeSpans = newRouteSpans
        #
        # Finished: interRoomSpans matrix represents the minimum span (distance 
        # in dice-throws) from room i to room j
        return interRoomSpans
    #
    #
    def mappossiblemoves(self,nodeStart):
        """Return the list of possible destinations for every dice roll.
        
        Args:
            nodeStart (int): The board node ID from which to start the search.
        
        Returns:
            list of lists of ints: All reachable node IDs for each possible 
                roll from 0 to ``game.DICEMAX``.
        
        Raises:
            None (Exception-neutral)
        
        Permitted routes are included even if they are not the fastest possible
        to given destinations, since it may be desirable to land on a square 
        with a roll higher than the lowest possible.
        
        Room nodes are restated for all rolls above the minimum; since entry to
        a room stops all rolls.
        
        """
        destinations = [set() for ix in range(game.DICEMAX+1)]
        destinations[0] = set([nodeStart])
        routes = [[nodeStart]]
        #
        # TODO: Not convinced this adds anything more than it harms in this fn.
        #if self.hasEnteredRoomYet:
        #    GAMEBOARD = game.TRIMMEDNODES
        #else:
        GAMEBOARD = game.BOARDNODES
        #
        for diceRoll in range(1,game.DICEMAX+1):
            newRoutes = []
            for route in routes:
                for nextLoc in GAMEBOARD[route[-1]]:
                    if not nextLoc in route:
                        # This location has not yet been visited by this route
                        if nextLoc in game.ALLOWEDROOMNODES:
                            # Location is a room - can move into it regardless
                            # of population, but not move further. We can also
                            # use any longer roll to move here by this route
                            for thisRoll in range(diceRoll,game.DICEMAX+1):
                                destinations[thisRoll].add(nextLoc)
                        else:
                            # Location is a square - can only move into it if
                            # unoccupied, but can move further once there.
                            if not nextLoc in self.charLocations:
                                # Unoccupied (could check against 
                                # charLocations[1:] since we're the piece moving
                                # but a nextLoc = charLocations[0] would be
                                # rejected by being already in the route anyway)
                                newRoute = list(route)
                                newRoute.append(nextLoc)
                                newRoutes.append(newRoute)
                                destinations[diceRoll].add(nextLoc)
            routes = newRoutes
        #
        return [list(destSet) for destSet in destinations]
    #
    #
    def statsfromcounts(self,countMatrix):
        """Calculate statistics from a matrix/vector of hypothesis counts.
        
        Args:
            countMatrix (np.array): (NCHARS x NROOMS x NWEAPS) array of uints
                counting the number of hypotheses nominating each scenario.
           
        Returns:
            A dict with keys:
            'p' (np.array): countMatrix converted to probabilities
                after the suggestion has been answered.
            'entropy' (float): The total entropy of distribution p.
            
        Raises:
            None (Exception-neutral)
        
        The sum of countMatrix is calculated; and so need not be equal to 
        ``len(self.hypotheses)``.
        
        """
        countSum = np.sum(countMatrix,dtype=np.float64)
        if countSum > 0.:
            p = countMatrix/countSum
            entropies = (-p)*np.log(p)
            # p=0 yields infinite log and hence nan entropy. We define
            # 0log(0) as 0 though:
            entropies[np.isnan(entropies)] = 0.
            entropy = np.sum(entropies)
        else:
            p = np.zeros(countMatrix.shape)
            entropy = 0.
        #
        return {'p':p,'entropy':entropy}     
    #
    #
    def updatestats(self):
        """Update the record of statistics for the currently held hypotheses."""
        result = self.statsfromcounts(self.hypCountByScenario)
        self.pScenario = result["p"]
        self.scenarioEntropy = result["entropy"]   
    #
    #
    def suggestionexpposteriors(self,character,room,weapon):
        """Return expected entropy and room distribution following a suggestion.
        
        Args:
            character (int): ID of character card nominated in suggestion.
            room (int): ID of room card nominated in suggestion.
            weapon (int): ID of weapon card nominated in suggestion.
           
        Returns:
            A dict with keys:
            'expEntropy' (float): Expected entropy of scenario distribution
                after the suggestion has been answered.
            'expRoomDist' (list of float): Expected probability distribution
                over rooms after the suggestion has been answered.
        
        Raises:
            None (Exception-neutral)
        
        This function takes the expectation over possible answers to a
        suggestion: Finding the turn-end entropy and room probability 
        distribution associated with each candidate answer, and combining them
        weighted by the likelihood of each answer being received.
        
        Players holding multiple cards in the triad are assumed to give the 
        response leaving us with highest entropy.
        
        Only hypothesis reduction is performed: Even when using probabilistic
        inference, the entropy and room distribution associated for an answer 
        are calculated from the depleted hypothesis list before rebuilding.
        
        """
        # Some helpful phrasings of the suggestion:
        triadList = [character,room,weapon]
        triadSet = set(triadList)
        #
        #### PHASE 1
        # Sort the hypotheses by their murder scenario, and by the answer(s) 
        # they provoke to this suggestion. A player may hold multiple of the
        # cards suggested and hence have a choice regarding which to show us.
        #
        # Therefore, we sort into 7 bins:
        # Bins 1,3,5,7 (binary 1 bit set) => Player holds character card
        # Bins 2,3,6,7 (binary 2 bit set) => Player holds room card
        # Bins 4,5,6,7 (binary 4 bit set) => Player holds weapon card
        # Note for zero based indexing, we must subtract one from these sort 
        # indices.
        hypCountsSorted = np.zeros(
            (self.nPlayers-1,   # Players that could answer
            7,                  # Cards this player could hold
            game.NCHARS,game.NROOMS,game.NWEAPS # Suggestion murder scenario
            ))
        # Lastly, we could have no answer from anyone
        hypCountsNoAnswer = np.zeros((game.NCHARS,game.NROOMS,game.NWEAPS))
        #
        # Sort the hypotheses:
        for hypothesis in self.hypotheses:
            for ixPlayer in range(1,self.nPlayers):
                ixAnswer = 0
                if character in hypothesis[ixPlayer]:
                    ixAnswer = 1
                if room in hypothesis[ixPlayer]:
                    ixAnswer |= 2
                if weapon in hypothesis[ixPlayer]:
                    ixAnswer |= 4
                if ixAnswer > 0:
                    hypCountsSorted[ixPlayer-1,ixAnswer-1,
                        hypothesis[-1][0],hypothesis[-1][1],
                        hypothesis[-1][2]] += 1
                    break
            else:
                # Else executed when for loop terminates without break => none
                # of the players held any of the cards suggested:
                hypCountsNoAnswer[hypothesis[-1][0],hypothesis[-1][1],
                    hypothesis[-1][2]] += 1
        #
        #### PHASE 2
        # Calculate the scenario entropy we're left with after receiving each
        # possible answer from each possible player (or no answers).
        #
        # Receiving an answer from a player invalidates all hypotheses in which
        # that player does NOT hold that card. For example, if player X shows us
        # the character, we will be left with the matrix of hypothesis counts
        # by scenario as follows:
        #   self.hypCountsByScenario[:,:,:] = 
        #       hypCountsSorted[X-1,{ix & 1},:,:,:]
        #
        # let HypCountsAfterAnswer be the hypothesis counts after reduction (but
        # before any rebuilding) following each possible answer:
        #   nPlayersAsked * 3 (Possible Answers) * NCHARS * NROOMS * NWEAPS
        #
        # Showing the character card keeps bins (1,3,5,7)-1 = (0,2,4,6)
        # Showing the room card keeps bins (2,3,6,7)-1 = (1,2,5,6)
        # Showing the weapon card keeps bins (4,5,6,7)-1 = (3,4,5,6)
        #
        # This matrix represents the distribution over scenarios after each 
        # answer is received - where deals allowing multiple answers are counted
        # multiple times
        hypCountsAfterAnswer = (
            hypCountsSorted[:,(0,1,3),:,:,:] + # One card only
            hypCountsSorted[:,(2,2,4),:,:,:] + 
            hypCountsSorted[:,(4,5,5),:,:,:] +
            hypCountsSorted[:,(6,6,6),:,:,:])  # All three cards
        #
        # This matrix represents the marginal distribution over murder rooms 
        # after each answer is received.
        hypCountsByRoomAfterAnswer = np.sum(np.sum(
            hypCountsAfterAnswer,4),2)
        #
        # To calculate probabilities (and so entropies) from our hypothesis 
        # counts, we need to divide by the total hypotheses remaining after each
        # answer. Only the room axis must be summed over, since we already
        # produced the marginal over rooms above. Append three singleton 
        # dimensions to allow direct division of the scenario count matrices by
        # (slices of) this matrix:
        hypCountSumsAfterAnswer = np.sum(
            hypCountsByRoomAfterAnswer,2)[:,:,None,None,None]
        pAfterAnswer = hypCountsAfterAnswer/hypCountSumsAfterAnswer
        #
        # pAfterAnswer will have np.infs in it where certain player,answer 
        # combinations are completely impossible 
        # (hypCountSumAfterAnswer[p,ans] = 0). These will appear as np.nans in
        # the entropy calculation below and must be dealt with. Note we don't 
        # bother dealing with the infs in p separately because:
        #   a) 0log(0) would still map to non-finite entropy so need correction
        #   b) We don't use pAfterAnswer after entropy calculation so may as 
        #       well save our time.
        entsAfterAnswer = -pAfterAnswer*np.log(pAfterAnswer)
        entsAfterAnswer[np.isnan(entsAfterAnswer)] = 0.
        # Distribution entropy is sum of entropies over distribution axes:
        # (NCHARS, NROOMS, NWEAPS)
        entAfterAnswer = np.sum(np.sum(np.sum(entsAfterAnswer,4),3),2)
        #
        # With all that out of the way, dealing with no-answer case is easier:
        hypCountsByRoomNoAnswer = np.sum(np.sum(hypCountsNoAnswer,2),0)
        hypCountSumNoAnswer = np.sum(hypCountsByRoomNoAnswer)
        if hypCountSumNoAnswer > 0.:
            # pNoAnswer will contain no infs...
            pNoAnswer = hypCountsNoAnswer/hypCountSumNoAnswer
            # ...But it will still have zeros so we must remove nan entropies.
            entsNoAnswer = -pNoAnswer*np.log(pNoAnswer)
            entsNoAnswer[np.isnan(entsNoAnswer)] = 0.
            entNoAnswer = np.sum(entsNoAnswer)
        else:
            entNoAnswer = 0.
        #
        #### PHASE 3
        # Calculate the probability of receiving each answer; given opponents'
        # expected strategy for choosing cards to show us where multiple 
        # possibilities exist.
        #
        # We assume players maximise the Detective's turn-end entropy when 
        # choosing cards to show; and hence provide the minimum amount of 
        # information to our distribution.
        #
        # let playerDecisions[ply,:] be player ply's order of preference for
        # each response (2=weap, 1=room, 0=character) starting with favourite:
        playerDecisions = np.argsort(entAfterAnswer)[:,::-1]
        #
        # Hence, the most preferred response will be given for all hypotheses 
        # where ply holds that card. The least preferred response will be given
        # for hypotheses where ply holds the least preferred card only.
        # Example: 0,1,2 => Character-holding bins 1,3,5,7 count to response 0
        #   Bin 4 only counts towards response 2 (weapon)
        #   Bins 2,6 count towards response 1 (room)
        #
        # For starters, allocate bins corresponding to holding only one card:
        # (don't worry - this creates a new copy not a view)
        receivedHypCounts = hypCountsSorted[:,(0,1,3),:,:,:]
        #
        # Because each player will have a different preference order, we must
        # loop through the player slices assigning the bins separately for each.
        # Note we refrain from use of 'ixPlayer' since we're off by one, not 
        # having the usual ixPlayer=0=Detective.
        for ixOPlayer in range(self.nPlayers-1):
            # The three-card case (bin 7) is fairly easily allocated - to the 
            # most preferred response:
            receivedHypCounts[ixOPlayer,playerDecisions[ixOPlayer,0]] += (
                hypCountsSorted[ixOPlayer,6,:,:,:])
            #
            # The three two-card bins require a little more negotiating:
            binsForAllocation = [3,5,6] # indexes 2,4 and 5
            mostPreferredBit = 2 ** playerDecisions[ixOPlayer,0]
            for thisBin in binsForAllocation:
                if thisBin & mostPreferredBit:
                    # Goes to most preferred answer
                    receivedHypCounts[ixOPlayer,playerDecisions[ixOPlayer,0]] \
                        += hypCountsSorted[ixOPlayer,thisBin-1,:,:,:]
                else:
                    # Goes to second preferred answer
                    receivedHypCounts[ixOPlayer,playerDecisions[ixOPlayer,1]] \
                        += hypCountsSorted[ixOPlayer,thisBin-1,:,:,:]
        #
        # We don't actually care about these distributions; only the total 
        # number of hypotheses in each for weighting our earlier entropies:
        totalReceivedCounts = np.sum(np.sum(np.sum(receivedHypCounts,4),3),2)
        # The sum over all given answers plus the no-answer case will, of course
        # be the total number of hypotheses we have:
        totalHypCount = len(self.hypotheses)
        # TODO: Remove debug check
        assert totalHypCount == \
            np.sum(totalReceivedCounts) + hypCountSumNoAnswer
        #
        # Hence the expected entropy after this suggestion is the sum of 
        # scenario entropies after each possible answer (and no answer); 
        # weighted by the number of hypotheses for which each answer is received
        expEntropy = ((entNoAnswer * hypCountSumNoAnswer) + 
            np.sum(entAfterAnswer * totalReceivedCounts)) / totalHypCount
        #
        # The expected room distribution works similarly, but needs to be
        # normalised by whatever constant necessary to represent a valid 
        # probability distribution. (totalHypCount^2 does not work)
        expRoomDist = ((hypCountsByRoomNoAnswer * hypCountSumNoAnswer) +
            np.sum(np.sum(
            (hypCountsByRoomAfterAnswer * totalReceivedCounts[:,:,None]),1),0))
        expRoomDist = expRoomDist / np.sum(expRoomDist)
        #
        return {'expEntropy':expEntropy,'expRoomDist':expRoomDist}    
    
    
    #### EXTERNAL FUNCTIONS ####################################################
    #
    def answersuggestion(self,character,room,weapon,suggester):
        """Return a card ID in answer to a suggestion.
        
        Args:
            character (int): ID of suggested character card.
            room (int): ID of suggested room card.
            weapon (int): ID of suggested weapon card.
            suggester (int): Relative ID of the suggesting player.
        
        Returns:
            int: ID of the card this Detective shows in answer to the suggestion
                if possible; or else game.NULLCARD.
        
        Raises:
            None (Exception-neutral)
        
        """
        # TODO: suggester is always self.ixHotSeat? Could do away with param
        #
        # Set of showable card IDs
        setShowables = self.myCardSet & set((character,room,weapon))
        # List of showable card IDs
        showables = list(setShowables)
        # List of indices in myCards of showable card IDs
        ixShowables = [self.myCards.index(card) for card in showables]
        # List of indices in myCards of showable and already shown (to this 
        # suggester) card IDs
        ixShownShowables = np.array([ixShowables[ix] for ix in 
            range(len(ixShowables)) 
            if self.myCardsShownTo[suggester-1,ixShowables[ix]]])
        # ixShowables is to be a numpy array too - but has to be transformed 
        # after the list comprehension lest an error be thrown on empty list
        ixShowables = np.array(ixShowables)
        if len(ixShowables):
            # We have one or more of the suggested cards and need a strategy to
            # show the least useful one to our opponent!
            if len(ixShownShowables):
                # If we have cards we have shown this player before; select the
                # one of these we have shown the most times previously.
                ixCard = ixShownShowables[
                    np.argmax(self.myCardsShownCounts[ixShownShowables])]
                self.myCardsShownCounts[ixCard] += 1
                self.event_seenresponse(self.myCards[ixCard],0,suggester)
                return self.myCards[ixCard]
            else:
                # Otherwise, select the card included in the suggestion we have
                # shown the most times previously
                ixCard = ixShowables[
                    np.argmax(self.myCardsShownCounts[ixShowables])]
                self.myCardsShownTo[suggester-1,ixCard] = True
                self.myCardsShownCounts[ixCard] += 1
                self.event_seenresponse(self.myCards[ixCard],0,suggester)
                return self.myCards[ixCard]
        else:
            # We have none of the suggested cards - must pass
            self.event_pass(character,room,weapon,0)
            return game.NULLCARD
    #
    #
    def move(self):
        """Take a turn.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            None (Exception-neutral)
        
        This is somewhat the core of the AI... Invokes hook_...() methods to 
        execute movements, suggestions and accusations as appropriate.
        """
        # Calculate the current inter-room distances in terms of expected rolls
        # of the dice
        interRoomSpans = self.calculateinterroomspans()
        #
        # For each room on the board, calculate the expected posterior scenario
        # entropy and the expected posterior murder location distribution:
        # Array of posterior entropies
        roomExpEntropies = np.tile(np.inf,(game.NROOMS,))
        # Array of character suggestions (charindexs) to attain these entropies
        roomSugCharIxs = np.zeros((game.NROOMS,),dtype=np.int)
        # ...and weapons
        roomSugWeapIxs = np.zeros((game.NROOMS,),dtype=np.int)
        # Matrix of posterior distributions over rooms after suggestion such
        # that roomPosteriorDists[ix,:] is the dist over rooms after suggesting
        # in room ix.
        roomPosteriorDists = np.zeros((game.NROOMS,game.NROOMS))
        #
        # Collect the index of the room we're currently in, or None if we are
        # in a corridor
        presentRoomIx = game.ROOMNODEIXS.get(
            self.charLocations[self.playerCharIxs[0]], None)
        #
        # Now, loop through rooms to analyse their merits as initialised above:
        self.hook_notifywait("Analysing room scores","Velma.move")
        tStart = time.time()
        for ixRoom in range(game.NROOMS):
            self.hook_notifyprogress("Analysing room scores",ixRoom,
                game.NROOMS,"Velma.move")
            if ixRoom == presentRoomIx and not self.canSuggestInCurrentRoom:
                # No suggestion can currently be made in this room: its 
                # expected posterior entropy is the prior entropy
                roomExpEntropies[ixRoom] = self.scenarioEntropy
                # ...and its expected posterior room distribution is the prior
                # too
                roomPosteriorDists[ixRoom,:] = (
                    self.hypCountByRoom/np.sum(self.hypCountByRoom))
            else:
                # A suggestion could be made in this room (if we can reach it)
                # and we must calculate the expected posterior entropy. This is
                # the minimum expected entropy over all suggestions, since we
                # choose to name the most productive character and weapon 
                # possible in our suggestion.
                tStartProc = time.time()    #TODO
                expEnts = np.zeros((game.NCHARS,game.NWEAPS))
                expRoomDists = np.zeros((game.NCHARS,game.NWEAPS,game.NROOMS))
                for ixChar in range(game.NCHARS):
                    for ixWeap in range(game.NWEAPS):
                        result = self.suggestionexpposteriors(
                            game.CHARS[ixChar],game.ROOMS[ixRoom],
                            game.WEAPS[ixWeap])
                        expEnts[ixChar,ixWeap] = result['expEntropy']
                        expRoomDists[ixChar,ixWeap,:] = result['expRoomDist']
                
                self.hook_notifydebug("Single thread analysis done in "+
                    str(time.time()-tStartProc)+"s","Velma.parcore")
                #TODO: Parallel solution *************************************************************************************************
                #import velma.CPUCount as CPUCount
                #cpuCount = CPUCount.available_cpu_count()
                #del CPUCount
                
                #procPool = mproc.Pool(cpuCount)
                #tStartProc = time.time()
                #thisRoom = game.ROOMS[ixRoom]
                #poolChars = tuple(i % game.NCHARS for i in range(game.NCHARS*game.NWEAPS))
                #poolWeaps = tuple(i // game.NWEAPS for i in range(game.NCHARS*game.NWEAPS))
                #poolArgs = tuple((self.hypotheses,game.CHARS[poolChars[i]],
                #    thisRoom,game.WEAPS[poolWeaps[i]]) for i in range(game.NCHARS*game.NWEAPS))
                #
                #results = procPool.starmap(parcore.suggestionexpposteriors,
                #    poolArgs,6)
                #self.hook_notifydebug("Multiproc work done in "+
                #    str(time.time()-tStartProc)+"s","Velma.parcore")
                #    
                #for i in range(len(results)):
                #    self.hook_notifyerror(str(results[i]),"Velma.parcore")
                #    expEnts[poolChars[i],poolWeaps[i]] = results[i]['expEntropy']
                #    expRoomDists[poolChars[i],poolWeaps[i],:] = results[i]['expRoomDist']
                #
                #self.hook_notifydebug("Multiproc analysis done in "+
                #    str(time.time()-tStartProc)+"s","Velma.parcore")
                #procPool.close()
                
                #************************************************************************************************************************
                #
                # TODO: Multiple suggestions may have same entropy, and we
                # should probably pick randomly rather than just taking the 
                # first option.
                roomExpEntropies[ixRoom] = np.min(expEnts)
                #
                # Find the indices achieving the minimum (multiple suggestions
                # may yield the same expected entropy)
                sugCharIxs,sugWeapIxs = np.where(expEnts == expEnts.min())
                # Choose one at random:
                ixChosen = random.sample(range(len(sugCharIxs)),1)[0]
                sugCharIx = sugCharIxs[ixChosen]
                sugWeapIx = sugWeapIxs[ixChosen]
                #(sugCharIx,sugWeapIx) = np.unravel_index(
                #    expEnts.argmin(),expEnts.shape)
                roomSugCharIxs[ixRoom] = sugCharIx
                roomSugWeapIxs[ixRoom] = sugWeapIx
                roomPosteriorDists[ixRoom,:] = \
                    expRoomDists[sugCharIx,sugWeapIx,:]
                #
                charInHand = bool(game.CHARS[sugCharIx] in self.myCardSet)
                roomInHand = bool(game.ROOMS[ixRoom] in self.myCardSet)
                weapInHand = bool(game.WEAPS[sugWeapIx] in self.myCardSet)
                totalInHand = charInHand + roomInHand + weapInHand
                #ui.plotentropydiagnostics(expEnts)
                #raw_input("Pause...")
        #
        tStop = time.time()
        self.hook_notifywaitover("Analysing room scores","Velma.move")
        self.hook_notifydebug('Analysed ' + str(game.NROOMS) + ' rooms in ' +
            str(tStop-tStart) + ' seconds',"Velma.move")
        #
        # roomPosteriorDists[ixRoom,:] is (our prior expectation of) the 
        # marginal probability distribution of each murder location after the 
        # entropy-minimising suggestion is made in room ixRoom.
        #
        # Hence we calculate the expected number of dice rolls to get from 
        # ixRoom to the murder location using this distribution. e.g. When the
        # room is known with certainty at the start of the turn, this quantity 
        # collapses to the number of dice rolls from ixRoom to the known murder
        # room. When our impressions of murder location are very weak, we 
        # approach a uniform average distance from rooms.
        #
        # TODO: Remedy this hack: takes 2 turns to get a suggestion in the room
        # you're in
        if (not presentRoomIx is None) and (not self.canSuggestInCurrentRoom):
            interRoomSpans[presentRoomIx,presentRoomIx] = 2.
        #
        roomExpRemoteness = np.array(
            [np.sum(roomPosteriorDists[ix,:]*interRoomSpans[ix,:])
            for ix in range(game.NROOMS)])
        #
        # Hence each room offers us a (scalar) expected scenario entropy on the
        # one hand, and a (scalar) metric indicating how far we would have to
        # travel from it to make our accusation on the other. 
        #
        # Conversely, landing on a plain (non-room) square would leave us with:
        # expected entropy = prior entropy
        # remoteness = expectation over interRoomSpans with prior over rooms
        if not self.SECRETIVE:
            np.set_printoptions(precision=3)
            self.hook_notifydebug("Present entropy = " +
                str(self.scenarioEntropy), "Velma.move")
            self.hook_notifydebug("Expected entropies:\n" +
                str(roomExpEntropies), "Velma.move")
            self.hook_notifydebug("Expected remoteness:\n" +
                str(roomExpRemoteness), "Velma.move")
            self.hook_notifydebug("Analysing available moves... ", "Velma.move")
            np.set_printoptions(precision=8)
        #
        roomScores = roomExpEntropies + roomExpRemoteness
        feasibleMoves = self.mappossiblemoves(
            self.charLocations[self.playerCharIxs[0]])
        bestScores = np.tile(np.inf,(len(feasibleMoves),))
        bestMoves = np.tile(game.NULLNODE,(len(feasibleMoves),))
        #
        scoreDict = {}
        remotenessDict = {}
        for diceRoll in range(len(feasibleMoves)):
            scores = np.tile(np.inf,(len(feasibleMoves[diceRoll]),))
            for ixDest in range(len(feasibleMoves[diceRoll])):
                destNode = feasibleMoves[diceRoll][ixDest]
                if destNode in game.ALLOWEDROOMNODES:
                    ixRoom = game.ROOMNODEIXS[destNode]
                    scores[ixDest] = roomScores[ixRoom]
                    scoreDict[destNode] = roomScores[ixRoom]
                    remotenessDict[destNode] = roomExpRemoteness[ixRoom]
                else:
                    # Span from a node to a room = min {
                    #   hop from node to room,
                    #   hop to any other room + span from room to destination}
                    roomHopSpans = game.dicerollstomove(
                        self.calculateroomhops(destNode))
                    # Distance from a room to itself = 0, so this computation
                    # is rather nice and quick with our interRoomSpans tensor
                    roomSpans = [np.min(roomHopSpans+interRoomSpans[ix,:])
                        for ix in range(game.NROOMS)]
                    # Hence compute remoteness of node with current prob dist
                    # over murder rooms
                    nodeRemoteness = (np.sum(self.hypCountByRoom * roomSpans) / 
                        np.sum(self.hypCountByRoom))
                    # Score = entropy + remoteness as before
                    scores[ixDest] = self.scenarioEntropy + nodeRemoteness
                    scoreDict[destNode] = scores[ixDest]
                    remotenessDict[destNode] = nodeRemoteness
                #
                #TODO Debug only... integrate this better:
                scoreTest = scoreDict.get(destNode,None)
                if scoreTest is None:
                    scoreDict[destNode] = scores[ixDest]
            #
            # Given dice roll, choose move to minimise the destination score:
            ixBestDest = np.argmin(scores)
            bestMoves[diceRoll] = feasibleMoves[diceRoll][ixBestDest]
            bestScores[diceRoll] = scores[ixBestDest]
        #
        # Having isolated our preferred destinations for every possible roll of
        # the dice, we can calculate the expected score of rolling the dice:
        rollScore = np.sum(game.DICEPS*bestScores)
        # ...and, rather trivially, the expected score of staying put:
        stickScore = bestScores[0]
        #
        # We have calculated optimal destinations and scores for every possible
        # rule of the dice including zero (staying put). To make an appropriate
        # decision about what to do with our turn, the only thing missing is the
        # score of taking the secret passage if one exists:
        passageDest = game.PASSAGES.get(self.charLocations[self.playerCharIxs[0]],
            None)
        passageScore = np.inf
        if not passageDest is None:
            if passageDest in game.ALLOWEDROOMNODES:
                passageRoomIx = game.ROOMNODEIXS[passageDest]
                passageScore = (roomExpRemoteness[passageRoomIx] + 
                    roomExpEntropies[passageRoomIx])
            else:
                # (The following would only ever get called for a custom board
                # layout with passages that terminate outside of rooms)
                roomHopSpans = game.dicerollstomove(
                    calculateroomhops(self,passageDest))
                roomSpans = [np.min(roomHopSpans+interRoomSpans[ix,:])
                    for ix in range(game.NROOMS)]
                nodeRemoteness = ((self.hypCountByRoom * roomSpans) / 
                        np.sum(self.hypCountByRoom))
                passageScore = self.scenarioEntropy + nodeRemoteness
        #
        if not self.SECRETIVE:
            self.hook_notifydebug("Expected roll score = "+str(rollScore),
                "Velma.move")
            self.hook_notifydebug("Expected stick score = "+str(stickScore),
                "Velma.move")
            self.hook_notifydebug("Expected passage score = "+str(passageScore),
                "Velma.move")
        #
        # All the leg-work is done: plot diagnostics
        if not self.SECRETIVE:
            self.hook_displaymovediagnostics({
                "roomExpEntropies":roomExpEntropies,
                "presentEntropy":self.scenarioEntropy,
                "roomExpRemoteness":roomExpRemoteness,
                "presentRemoteness":remotenessDict[
                self.charLocations[self.playerCharIxs[0]]],
                "roomScores":roomScores,
                "stickScore":stickScore,
                "rollScore":rollScore,
                "passageScore":passageScore})
        #
        # Action stations at last!
        if (passageScore <= stickScore) and (passageScore <= rollScore):
            # Take the secret passage
            self.hook_notifymove(passageDest)
            self.event_move(passageDest)
        elif (rollScore <= stickScore) and (rollScore <= passageScore):
            # Roll the dice
            moveLength = self.hook_rolldice()
            # Make the best move we can
            self.hook_notifymove(bestMoves[moveLength])
            self.event_move(bestMoves[moveLength])
        elif (self.charLocations[self.playerCharIxs[0]] not in 
                game.ALLOWEDROOMNODES):
            self.hook_notifyerror("Why on Earth have I decided to stay still \
when I can't make a suggestion?","Velma.move")
        #
        # If we can make a suggestion, do so!
        ixRoom = game.ROOMNODEIXS.get(self.charLocations[self.playerCharIxs[0]],
            None)
        if self.canSuggestInCurrentRoom and not ixRoom is None:
            self.event_suggestion(game.CHARS[roomSugCharIxs[ixRoom]],
                game.ROOMS[ixRoom],game.WEAPS[roomSugWeapIxs[ixRoom]])
            sugAnswerer = self.hook_suggest(game.CHARS[roomSugCharIxs[ixRoom]],
                game.ROOMS[ixRoom],game.WEAPS[roomSugWeapIxs[ixRoom]])
            #
            # If we've exceeded the certainty threshold, go for the accusation!
            self.hook_notifydebug('Most likely scenario has p=' + 
                str(np.max(self.pScenario)),"Velma.move")
            if np.max(self.pScenario) > self.PACCUSATIONTHRESH:
                (ixAccChar,ixAccRoom,ixAccWeap) = np.unravel_index(
                    np.argmax(self.pScenario),self.pScenario.shape)
                if ixRoom == ixAccRoom:
                    if not self.SECRETIVE:
                        self.hook_displaysuspicions()
                    self.hook_accuse(game.CHARS[ixAccChar],
                        game.ROOMS[ixAccRoom],game.WEAPS[ixAccWeap])
        #
        # All done - turn complete!
    #
    #
    def initialise(self,nPlayers=None,playerCharCards=None,ixDealer=None,
            playerCardHeldCounts=None,myCards=None,DBGSCENARIO=None):
        """Initialise the detective in one of three ways:
        
        Args:
            nPlayers (int, optional): Number of players in the game.
            playerCharCards (list of int, optional): Character card IDs of the
                avatars of each player.
            ixDealer (int, optional): Number of seats around from the Detective
                (in the direction of play) the dealer is sat. i.e. the relative
                ID of the dealer.
            playerCardHeldCounts (list of int, optional): Number of cards held
                by each player.
            myCards (iterable of int, optional): Card IDs held by the Detective.
            DBGSCENARIO (iterable of iterable of int, optional): A synthetic
                scenario deal.
        
        Returns:
            None
        
        Raises:
            TypeError, ValueError for invalid argument inputs.
        
        Call ``initialise()`` with no arguments to invoke the default UI to
        ask the user for game setup information (i.e. play as assistant).
        
        Call ``initialise()`` with playerCharCards, ixDealer and DBGSCENARIO set
        to begin a synthetic game with a known scenario - for debugging Velma's
        turn algorithm.
        
        Call ``initialise()`` with nPlayers, playerCharCards, ixDealer,
        playerCardHeldCounts and myCards set to initialise Velma with an already
        known game setup (i.e. play as an opponent or with a game-hosting UI).
        
        DBGSCENARIO objects are lists of hands: for all players plus the murder
        envelope. Each hand is a list of card IDs representing the cards held
        by the given player. Hands are in order of the relative player ID; i.e.
        starting (0) with the Detective object and continuing until (nPlayers+1)
        for the cards in the murder envelope.
        
        To speed up debugging, the default UI can be configured to examine 
        DBGSCENARIOS in Detective objects and automatically respond to 
        suggestions and accusations.
        
        """
        # The following articles are set differently depending whether a debug
        # scenario is provided
        if DBGSCENARIO is not None:
            # DBGSCENARIO is not None:
            # Try to parse the debug scenario and raise ValueError if not 
            # suitable
            try:
                self.DBGSCENARIO = tuple(
                    set(int(card) for card in hand) for hand in DBGSCENARIO)
                self.DBGSCENARIOREMINDER = str(tuple(
                    set(game.CARDNAMES[card] for card in hand)
                    for hand in DBGSCENARIO))
            except:
                raise ValueError("To supply a DBGSCENARIO, provide an iterable \
such that each element refers to a player's hand except for the last - which \
refers to the murder set. Each hand must in turn be an iterable of card IDs or \
names.")
            # Check uniqueness of cards
            dealt = set()
            for ixHand in range(len(DBGSCENARIO)):
                for card in DBGSCENARIO[ixHand]:
                    dealt.add(card)
            if dealt != game.ALLOWEDCARDS:
                raise ValueError("The supplied DBGSCENARIO does not deal the \
full set of cards.")
            # Check integrity of murder hand
            if len(self.DBGSCENARIO[-1]) != 3:
                raise TypeError("The last entry of DBGSCENARIO must be an \
iterable containing the card IDs of the culprit, murder weapon and location - \
and must therefore have length 3.")
            murderChars = murderRooms = murderWeaps = 0
            for card in DBGSCENARIO[-1]:
                if card in game.ALLOWEDCHARS:
                    murderChars += 1
                elif card in game.ALLOWEDROOMS:
                    murderRooms += 1
                elif card in game.ALLOWEDWEAPS:
                    murderWeaps += 1
            if murderChars != 1 or murderRooms != 1 or murderWeaps != 1:
                raise ValueError("The last entry of DBGSCENARIO must be an \
iterable containing the card ID of one character, one room and one weapon - \
describing the murder.")
            #
            # Checks complete - set other articles from DBGSCENARIO
            self.nPlayers = len(self.DBGSCENARIO)-1
            if self.nPlayers < 2 or self.nPlayers > 6:
                raise ValueError("If a DBGSCENARIO is not provided, nPlayers \
must be a positive integer between 2 and 6 - the number of players in the \
game.")
            self.nCardsHeld = tuple(
                len(hand) for hand in DBGSCENARIO[:-1])
            self.myCards = tuple(
                int(entry) for entry in DBGSCENARIO[0])
            self.myCardSet = set(
                int(entry) for entry in DBGSCENARIO[0])
            #
            try:
                self.playerCharIxs = tuple(
                    game.CHARINDEX[card] for card in playerCharCards)
                if len(self.playerCharIxs) != self.nPlayers:
                    raise TypeError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, \
playerCharCards must be an iterable of card IDs - the character card for each \
player in turn.")
            except KeyError:
                raise KeyError("If a DBGSCENARIO is not provided, \
playerCharCards must be an iterable of card IDs - the character card for each \
player in turn.")
            try:
                self.ixDealer = int(ixDealer)
                if self.ixDealer < 0 or self.ixDealer >= self.nPlayers:
                    raise ValueError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, ixDealer \
must be an integer between 0 and (nPlayers-1) - the number of places around \
the table the dealer is sat from the detective, in the direction of play.")
            except ValueError:
                raise ValueError("If a DBGSCENARIO is not provided, ixDealer \
must be an integer between 0 and (nPlayers-1) - the number of places around \
the table the dealer is sat from the detective, in the direction of play.")
                
        elif nPlayers is not None and playerCharCards is not None:
            self.DBGSCENARIO = None
            self.DBGSCENARIOREMINDER = False
            try:
                self.nPlayers = int(nPlayers)
                if self.nPlayers < 2 or self.nPlayers > 6:
                    raise ValueError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, nPlayers \
must be a positive integer between 2 and 6 - the number of players in the \
game.")
            except ValueError:
                raise ValueError("If a DBGSCENARIO is not provided, nPlayers \
must be a positive integer between 2 and 6 - the number of players in the \
game.")
            try:
                self.nCardsHeld = tuple(
                    int(entry) for entry in playerCardHeldCounts)
                if len(self.nCardsHeld) != self.nPlayers:
                    raise TypeError
                for entry in self.nCardsHeld:
                    if entry <= 0:
                        raise ValueError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, \
playerCardHeldCounts must be in iterable of positive integers - the number of \
cards held by each player after the deal, starting with me.")
            except ValueError:
                raise ValueError("If a DBGSCENARIO is not provided, \
playerCardHeldCounts must be in iterable of positive integers - the number of \
cards held by each player after the deal, starting with me.")
            try:
                self.myCards = tuple(
                    int(entry) for entry in myCards)
                self.myCardSet = set(
                    int(entry) for entry in myCards)
                if len(self.myCardSet) != self.nCardsHeld[0]:
                    raise TypeError
                for card in self.myCardSet:
                    if card not in game.ALLOWEDCARDS:
                        raise ValueError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, myCards \
must be an iterable of cards (ID or name) - the cards held by me after the \
deal.")
            except ValueError:
                raise ValueError("If a DBGSCENARIO is not provided, myCards \
must be an iterable of cards (ID or name) - the cards held by me after the \
deal.")
            try:
                self.playerCharIxs = tuple(
                    game.CHARINDEX[card] for card in playerCharCards)
                if len(self.playerCharIxs) != self.nPlayers:
                    raise TypeError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, \
playerCharCards must be an iterable of card IDs - the character card for each \
player in turn.")
            except KeyError:
                raise KeyError("If a DBGSCENARIO is not provided, \
playerCharCards must be an iterable of card IDs - the character card for each \
player in turn.")
            try:
                self.ixDealer = int(ixDealer)
                if self.ixDealer < 0 or self.ixDealer >= self.nPlayers:
                    raise ValueError
            except TypeError:
                raise TypeError("If a DBGSCENARIO is not provided, ixDealer \
must be an integer between 0 and (nPlayers-1) - the number of places around \
the table the dealer is sat from the detective, in the direction of play.")
            except ValueError:
                raise ValueError("If a DBGSCENARIO is not provided, ixDealer \
must be an integer between 0 and (nPlayers-1) - the number of places around \
the table the dealer is sat from the detective, in the direction of play.")
        
        else:
            # Called without arguments -> we should fetch the situation 
            # ourselves from the UI
            self.DBGSCENARIO = None
            self.DBGSCENARIOREMINDER = False
            result = self.hook_collectgamesetup()
            self.nPlayers = result['nPlayers']
            self.ixDealer = result['ixDealer']
            self.playerCharIxs = tuple(
                game.CHARINDEX[card] for card in result['playerCharCards'])
            self.nCardsHeld = tuple(result['playerCardHeldCounts'])
            self.myCards = tuple(result['myCards'])
            self.myCardSet = set(result['myCards'])
        #
        ## (Re)Initialise internal variables for new game ######################
        self.charLocations = game.CHARSTARTNODES
        self.hypotheses = []
        self.areHypothesesEnumerable = False
        self.hasEnteredRoomYet = False
        self.canSuggestInCurrentRoom = True
        self.ixTurn = 0
        self.logMoves = []
        self.logSuggestions = []
        self.logPasses = []
        self.logUnseenAnswers = []
        self.logSeenAnswers = []
        self.logIncorrectAccusations = []
        self.hypCountByCharacter = np.zeros(game.NCHARS)
        self.hypCountByRoom = np.zeros(game.NROOMS)
        self.hypCountByWeapon = np.zeros(game.NWEAPS)
        self.hypCountByScenario= np.zeros((game.NCHARS,game.NROOMS,game.NWEAPS))
        #
        ## Setup collected - initialise internal state for play ################
        self.isGameOver = False
        self.playersOusted = np.tile(False,(self.nPlayers,))
        self.charLocations = [node for node in game.CHARSTARTNODES]
        self.myCardsShownTo = np.tile(False,(self.nPlayers-1,len(self.myCards)))
        self.myCardsShownCounts = np.zeros(len(self.myCards))
        # Find the first mover by going around the characters clockwise, 
        # starting with scarlet:
        for ixChar in game.CHARIXSTARTORDER:
            try:
                self.ixHotSeat = self.playerCharIxs.index(ixChar)
                break
            except ValueError:
                pass
        # Forbidden card locations:
        self.forbidden = np.tile(False,(self.nPlayers+1,game.NCARDS))
        self.forbiddenSets = [set() for ix in range(self.nPlayers+1)]
        for cardid in self.myCardSet:
            self.forbidden[1:self.nPlayers+1,cardid] = True
            for ixPlayer in range(1,self.nPlayers+1):
                self.forbiddenSets[ixPlayer].add(cardid)
        for cardid in game.ALLOWEDCARDS:
            if cardid in self.myCardSet:
                self.forbidden[0,cardid] = False
            else:
                self.forbidden[0,cardid] = True
                self.forbiddenSets[0].add(cardid)
        #
        ## Build hypothesis database ###########################################
        self.rebuildhypotheses()
        #
        # Mark initialisation complete #########################################
        self.isInitialised = True
    #
    #
    def run(self):
        """Host a game of Cluedo.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            AssertionError if not ``initialise()``d first.
        
        Call this function to make the Detective host a game of Cluedo: calling
        move() or hook_observemove() and updating displays until the game
        terminates.
        
        This mode of operation is ideal for games against a single Detective - 
        especially as in the assistant use-case or with very lightweight UIs.
        
        Meanwhile, more complex apps (capable of hosting multiple Detectives in
        a game or with more sophisticated user interfaces) should be developed
        to drive the games themselves and employ a Detective by way solely of
        the hook_...() and event_...() methods.
        
        """
        # TODO: Clean this up to better facilitate running as client: There's 
        # still too much being done in this function.
        #
        # Only start if we've been appropriately initialised
        # TODO: Are assertion checks stripped out in optimised builds? Is this
        # the wrong method for an important check?
        assert self.isInitialised, "Detective must be initialise()d before \
running."
        #
        ## If not secretive, announce our cards ################################
        if not self.SECRETIVE:
            announcestr = "Preparing for battle. I hold cards: "
            for card in self.myCards:
                announcestr += game.CARDNAMES[card]+", "
            self.hook_notifydebug(announcestr[:-2],"Velma.run")
        #
        #
        # TODO: Move the following commented code stack to a test routine.
        # Miss Scarlet known to be culprit
        #ui.dbgstatus('tweak','Miss Scarlet known culprit')
        #for ixPlayer in range(1,self.nPlayers):
        #    self.event_pass(character=4,room=8,weapon=19,player=ixPlayer)
        # Kitchen known to be scene
        #ui.dbgstatus('tweak','Kitchen known scene')
        #for ixPlayer in range(1,self.nPlayers):
        #    self.event_pass(character=0,room=9,weapon=19,player=ixPlayer)
        # Unseen answer 1 Plum/Billiard/Wrench
        #ui.dbgstatus('tweak','Unseen answer from 1')
        #self.event_unseenresponse(character=1,room=12,weapon=20,shower=1,viewer=3)
        # 1 known to have Peacock
        #ui.dbgstatus('tweak','1 known has Peacock')
        #self.event_seenresponse(card=3,shower=1,viewer=0)
        # 1 known not to have candlestick
        #ui.dbgstatus('tweak','1 known without candlestick')
        #self.event_pass(character=0,room=8,weapon=16,player=1)
        # 2 known to have knife
        #ui.dbgstatus('tweak','2 known has knife')
        #self.event_seenresponse(card=15,shower=2,viewer=0)
        # 2 known to have either White or Lounge or Candlestick
        #ui.dbgstatus('tweak','Unseen answer from 2')
        #self.event_unseenresponse(character=5,room=7,weapon=16,shower=2,viewer=1)
        # 3 known has ballroom
        #ui.dbgstatus('tweak','3 known has ballroom')
        #self.event_seenresponse(card=10,shower=3,viewer=0)
        #
        #
        while not self.isGameOver:
            # Output everybody's identity and position on the board. This 
            # information is not privileged, and should be helpful in ensuring
            # consistency between what Velma thinks is going on and the state
            # of the real-world board
            for ixPlayer in range(self.nPlayers):
                self.hook_notifydebug("Player "+str(ixPlayer)+" is "+
                    game.CARDNAMES[game.CHARS[self.playerCharIxs[ixPlayer]]]+
                    " at "+
                    str(self.charLocations[self.playerCharIxs[ixPlayer]]),
                    "Velma.run")
            #
            # Remind our conversant of any pre-set scenario
            if self.DBGSCENARIOREMINDER:
                self.hook_notifydebug('Reminder: \n' + self.DBGSCENARIOREMINDER,
                    "Velma.run")
            #
            # If we're not competing with our conversant, plot our knowledge
            if not self.SECRETIVE:
                self.hook_displaysuspicions()
            #
            if self.ixHotSeat == 0:
                self.move()
            else:
                self.hook_observemove()
            #
            # The hot seat increments, and skips over any players previously
            # knocked out
            self.ixTurn += 1
            self.ixHotSeat = (self.ixHotSeat + 1) % self.nPlayers
            while self.playersOusted[self.ixHotSeat]:
                self.ixHotSeat = (self.ixHotSeat + 1) % self.nPlayers
#
#### EOF #######################################################################
################################################################################
