"""Velma default user interface.

This module defines a super-simple, console-based user interface to 
facilitate use of Velma straight out of the box. Developers are
encouraged to inherit from core.Detective and override the outbound
hook_...() methods to bypass this basic UI; allowing easy integration
of Velma into third-party Cluedo game apps.

"""


################################################################################
#### LIBRARIES #################################################################

## STANDARD LIBRARIES ##########################################################
import numpy as np
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import sys

## OTHER PARTS OF VELMA ########################################################
#import velma.core as core
import velma.game as game           # Definitions of the Cluedo game


################################################################################
#### CONSTANTS #################################################################

# Set this to a tuple of card IDs to make the UI aware of the answer to the 
# problem when no DBGSCENARIO is present
ANSWER = None

# Whether or not to automatically respond when a known debug scenario is in use
DBGAUTORESPOND = True

# Text format opener for questions
TXTFQUESTION = '\033[1m'    #ansiiescs.graphicsmode(textattrs='bold')
# ...and for errors
TXTFERROR = '\033[31;1m'    #ansiiescs.graphicsmode('red',textattrs='bold')
# ...and for important text
TXTFIMPORTANT = '\033[32;1m'#ansiiescs.graphicsmode('green',textattrs='bold')
# ...and for debug messages
TXTFDEBUG = '\033[36m'
# ...and for SUPER important text
TXTFTITLE = '\033[32;1;4m'
# Text format closer
TXTFEND = '\033[0m'         #ansiiescs.graphicsmode()
    

DICTWORDUNKNOWN = '?'
DICTVOWELPASS = 'pass'
DICTVOWELMOVEMENT = 'moves'
DICTVOWELSUGGESTION = 'suggests'
DICTVOWELACCUSATION = 'accuses'
DICTSIGSOURCELOC = 'from'
DICTSIGDESTLOC = 'to'
DICTSIGMURDERLOC = 'in'
DICTSIGMURDERWEAP = 'with'
DICTSIGOBJECT = 'the'
DICTCONNECTIVE = 'and'
DICTAFFIRMATIVE = 'yes'
DICTNEGATIVE = 'no'
DICTIONARY = {
    #### CHARACTER NAMES #######################################################
    'col. mustard':0,'prof. plum':1,'mr. green':2,'mrs. peacock':3,
    'miss scarlet':4,'mrs. white':5,
    # Full titles
    'colonel mustard':0,'professor plum':1,'mister green':2,'missus peacock':3,
    'missus white':5,
    # Surname shortcuts
    'mustard':0,'plum':1,'green':2,'peacock':3,'scarlet':4,'white':5,
    # Colour shortcuts where different from surname
    'yellow':0,'purple':1,'blue':3,'red':4,
    # Typos
    'col mustard':0,'prof plum':1,'mr green':2,'mrs peacock':3,
    'mrs white':5,
    'mustrad':0,'pulm':1,'gren':2,'paecock':3,'peacokc':3,'scralet':4,
    'wite':5,
    #### ROOM NAMES ############################################################
    'hall':6,'lounge':7,'dining room':8,'kitchen':9,'ballroom':10,
    'conservatory':11,'billiard room':12,'library':13,'study':14,
    # Shortcuts skipping 'room'
    'dining':8,'billiard':12,
    # Typos
    'ahll':6,'longue':7,'dinning room':8,'dining rom':8,'dinning':8,'kichen':9,
    'kitchne':9,'balroom':10,'ballrom':10,'conservatry':11,'cnservatory':11,
    'consevatory':11,'biliard room':12,'billiard rom':12,'biliard':12,
    'libray':13,'libary':13,
    #### WEAPON NAMES ##########################################################
    'knife':15,'candlestick':16,'revolver':17,'rope':18,'lead pipe':19,
    'wrench':20,
    # Colloquial names
    'gun':17,'handgun':17,'pipe':19,'spanner':20,
    # Typos
    'kinfe':15,'cndlestick':16,'candlstick':16,'led pipe':19,'lead pip':19,
    'rench':20,'wench':20,
    # Verbs signifying passing/non-answer:
    'pass':DICTVOWELPASS,
    # Verbs signifying movement:
    'move':DICTVOWELMOVEMENT,'moves':DICTVOWELMOVEMENT,
    'moved':DICTVOWELMOVEMENT,
    # Verbs signifying suggestion:
    'suggest':DICTVOWELSUGGESTION,'suggests':DICTVOWELSUGGESTION,
    'suggested':DICTVOWELSUGGESTION,
    # Verbs signifying accusation:
    'accuse':DICTVOWELACCUSATION,'accuses':DICTVOWELACCUSATION,
    'accused':DICTVOWELACCUSATION,
    # Signifiers of a source location:
    'from':DICTSIGSOURCELOC,
    # Signifiers of a destination location:
    'to':DICTSIGDESTLOC,
    # Signifiers of a murder location:
    'in':DICTSIGMURDERLOC,
    # Signifiers of a murder weapon:
    'with':DICTSIGMURDERWEAP,
    # Signifiers of an object:
    'a':DICTSIGOBJECT,'the':DICTSIGOBJECT,
    # Connectives between movement/suggestion/accusation phrases:
    'and':DICTCONNECTIVE,'then':DICTCONNECTIVE,
    # Affirmatives:
    'yes':DICTAFFIRMATIVE,'y':DICTAFFIRMATIVE,
    'yup':DICTAFFIRMATIVE,'always':DICTAFFIRMATIVE,
    # Negatives:
    'no':DICTNEGATIVE,'n':DICTNEGATIVE,'nope':DICTNEGATIVE,'never':DICTNEGATIVE
    }
DICTIONARYKEYS = tuple(DICTIONARY.keys())
DICTIONARYSPLITKEYS = tuple(key.split() for key in DICTIONARY.keys())


################################################################################
#### CLASSES ###################################################################

#class VELMADefaultHost(core.GameHost):
#    """Default game/host class for VELMA package
#    """
#    pass

################################################################################
#### FUNCTIONS #################################################################

#### SIMPLE NOTIFICATIONS ######################################################
#
def greet():
    """Greet the user at game start."""
    print("\n\n"+TXTFTITLE+"         VELMA Cluedo Assistant         "+TXTFEND+
        "\n      Jinkies!  Let's play Cluedo!      \n\n")
    plt.ion()
#
#
def notifyerror(msg,subsystem=None):
    """Notify the user of an error."""
    if subsystem is None:
        print(TXTFERROR+"Oops - "+msg+TXTFEND)
    else:
        print(TXTFERROR+"Oops ("+subsystem+") - "+msg+TXTFEND)
#
#
def notifydebug(msg,subsystem=None):
    """Show a debug message."""
    if subsystem is None:
        print(TXTFDEBUG+msg+TXTFEND)
    else:
        print(TXTFDEBUG+"["+subsystem+"] "+msg+TXTFEND)
#
#
def notifywait(operation,subsystem=None):
    """Notify the user of the start of a potentially long operation."""
    print(TXTFIMPORTANT+"This may take a while: "+operation+"..."+TXTFEND)
#
#
def notifywaitover(operation,subsystem=None):
    """Notify the user of the completion off a long operation."""
    print(TXTFIMPORTANT+"Operation complete"+TXTFEND)
#
#
def notifygameover(didIWin=None):
    """Notify the user that the game has ended."""
    if didIWin is None:
        print("\n\n"+TXTFTITLE+"                                        "+
            "\n                GAME OVER               \n"+TXTFEND+
            "\n   I hate goodbyes - play again soon!   \n\n")
    elif didIWin:
        print("\n\n"+TXTFTITLE+"                                        "+
            "\n          GAME OVER -> We Won!          \n"+TXTFEND+
            "\nNice work guys - another mystery solved!\n\n")
    else:
        print("\n\n"+TXTFTITLE+"                                        "+
            "\n  GAME OVER - Better luck next time...  \n"+TXTFEND+
            "\n        Darn those meddling kids!       \n\n")
#
#
def notifymove(ixTurn,ixHotSeat,nodeStart,nodeStop):
    moveprompt(ixTurn,ixHotSeat)
    nodeRoom = game.ROOMNODECARDS.get(nodeStop,None)
    
    if nodeRoom is None:
        nodeName = "space "+str(nodeStop)
    else:
        nodeName = "the "+game.CARDNAMES[nodeRoom].lower()
    
    print(TXTFQUESTION+"I move to "+nodeName+"."+TXTFEND)
    # TODO: Supposed to be a feedback system for objecting to illegal moves
    return True


#### USER INPUT REQUESTS #######################################################
#
def collectgamesetup():
    nPlayers = 0
    isItemSet = False
    errCount = 0
    while not isItemSet:
        try:
            nPlayers = np.uint8(input(TXTFQUESTION+
                "How many people are playing? -> "+TXTFEND))
            
            if nPlayers < game.MINPLAYERS or nPlayers > game.MAXPLAYERS:
                notifyerror("Cluedo is a game for 2 to 6 players",
                    "ui.collectgamesetup")
                errCount += 1
            else:
                isItemSet = True
        except:
            notifyerror("Please enter a number!","ui.collectgamesetup")
            errCount += 1
        
        if errCount >= 4:
            raise ValueError

    ixDealer = -1
    isItemSet = False
    errCount = 0
    while not isItemSet:
        try:
            ixDealer = np.uint8(input(TXTFQUESTION+
                "How many players round from me is the dealer sat, in the " +
                "direction of play? -> "+TXTFEND))
            
            if ixDealer < 0 or ixDealer >= nPlayers:
                notifyerror("""This number must be either 0 (if I am to deal), 
or the number of places round from me which the dealer is sat""",
                    "ui.collectgamesetup")
            else:
                isItemSet = True
        except:
            notifyerror("Please enter a number!","ui.collectgamesetup")
            
        if errCount >= 4:
            raise ValueError
    
    playerCharCards = [game.NULLCARD+1,]*nPlayers
    playerCharIxs = [game.NCHARS+1,]*nPlayers
    isCharSet = False
    errCount = 0
    while not isCharSet:
        try:
            parsedResponse = translatestr(input(TXTFQUESTION+
                "What character am I?"+TXTFEND+
                "\n(Recommend Peacock; Scarlet; Mustard; Plum; Green)\n"+
                TXTFQUESTION+"-> "+TXTFEND))
            if (len(parsedResponse) == 1 and 
                    parsedResponse[0] in game.ALLOWEDCHARS):
                playerCharCards[0] = parsedResponse[0]
                playerCharIxs[0] = game.CHARINDEX[parsedResponse[0]]
                isCharSet = True
            else:
                notifyerror(
                    'That card is not a character: please enter a character card',
                    "ui.collectgamesetup")
                errCount += 1
        except KeyError:
            notifyerror('Unknown Card',"ui.collectgamesetup")
            errCount += 1
        if errCount >= 3:
            raise ValueError
    
    for ixPlayer in range(1,nPlayers):
        isCharSet = False
        errCount = 0
        while not isCharSet:
            try:
                parsedResponse = translatestr(
                    input(TXTFQUESTION+"What character is "+str(ixPlayer)+
                    "? -> "+TXTFEND))
                if (len(parsedResponse) == 1 and 
                        parsedResponse[0] in game.ALLOWEDCHARS):
                    if parsedResponse[0] in playerCharCards:
                        notifyerror('That character is already taken...',
                            "ui.collectgamesetup")
                        errCount += 1
                    else:
                        charix = game.CHARINDEX[parsedResponse[0]]
                        playerCharIxs[ixPlayer] = charix
                        playerCharCards[ixPlayer] = parsedResponse[0]
                        isCharSet = True
                else:
                    notifyerror("""That card is not a character: please enter a
character card""","ui.collectgamesetup")
                    errCount += 1
            except:
                notifyerror('unknowncard',"ui.collectgamesetup")
                errCount += 1
            if errCount >= 3:
                raise ValueError
    
    # From player count and dealer location, work out the hand sizes
    playerCardHeldCounts = [(game.NCARDS-3)//nPlayers,]*nPlayers
    # Floor div gives the min card count, now add the remainder:
    for excess in range(ixDealer+1,ixDealer+1+
            ((game.NCARDS-3)%nPlayers)):
        playerCardHeldCounts[excess%nPlayers] += 1
    
    myCards = [game.NULLCARD,]*playerCardHeldCounts[0]
    print(TXTFQUESTION+'What cards am I holding after the deal?'+TXTFEND)
    for ixCard in range(playerCardHeldCounts[0]):
        cardAccepted = False
        errCount = 0
        while cardAccepted == False:
            parsedResponse = translatestr(input(TXTFQUESTION+'-> '+TXTFEND))
            if (len(parsedResponse) == 1 and 
                    parsedResponse[0] in game.ALLOWEDCARDS):
                if parsedResponse[0] in myCards:
                    notifyerror("You already mentioned that card...",
                        "ui.collectgamesetup")
                    errCount += 1
                else:
                    myCards[ixCard] = parsedResponse[0]
                    cardAccepted = True
            else:
                notifyerror('unknowncard',
                    "ui.collectgamesetup")
                errCount += 1
            if errCount >= 4:
                raise ValueError
    
    return {'nPlayers':nPlayers,'ixDealer':ixDealer,
        'playerCharCards':playerCharCards,
        'playerCardHeldCounts':playerCardHeldCounts,'myCards':myCards}
#
#
def roll(detective):
    isItemSet = False
    errCount = 0
    while not isItemSet:
        try:
            moveprompt(detective.ixTurn,detective.ixHotSeat)
            diceResult = np.int(input(TXTFQUESTION+"Roll dem bones... -> "
                +TXTFEND))
            if diceResult < game.DICEMIN or diceResult > game.DICEMAX:
                notifyerror("I'm after a number between "+str(game.DICEMIN)+
                    " and "+str(game.DICEMAX)+"...","ui.roll")
                errCount += 1
            else:
                isItemSet = True
                diceResult = np.uint8(diceResult)
        except:
            notifyerror("I'm after a number between "+str(game.DICEMIN)+" and "+
                    str(game.DICEMAX)+"...","ui.roll")
            errCount += 1
            
        if errCount >= 4:
            raise ValueError
    
    if (diceResult == game.DICEMIN) or (diceResult == game.DICEMAX):
        print("(Nice dubs)")
    return diceResult
#
#
def suggest(detective,ixTurn,ixHotSeat,character,room,weapon):
    moveprompt(ixTurn,ixHotSeat)
    print(TXTFIMPORTANT+"I suggest "+game.CARDNAMES[character]+" in the "+
        game.CARDNAMES[room]+" with\n  the "+game.CARDNAMES[weapon]+TXTFEND)
        
    sugAnswered = None
    for ixPlayer in range(1,detective.nPlayers):
        isItemSet = False
        errCount = 0
        if detective.DBGSCENARIO and DBGAUTORESPOND:
            showCard = game.NULLCARD
            if room in detective.DBGSCENARIO[ixPlayer]:
                showCard = room
            elif weapon in detective.DBGSCENARIO[ixPlayer]:
                showCard = weapon
            elif character in detective.DBGSCENARIO[ixPlayer]:
                showCard = character
            
            if showCard == game.NULLCARD:
                print(TXTFQUESTION+"Player "+str(ixPlayer)+
                    " response: -> "+TXTFEND+"Pass")
                detective.event_pass(character,room,weapon,ixPlayer)
            else:
                print(TXTFQUESTION+"Player "+str(ixPlayer)+
                    " response: -> "+TXTFEND+game.CARDNAMES[showCard])
                detective.event_seenresponse(showCard,ixPlayer,0)
                sugAnswered = ixPlayer
                
                
        else:
            while not isItemSet:
                moveprompt(ixTurn,ixHotSeat)
                response = input(TXTFQUESTION+"Player "+str(ixPlayer)+
                    " response: -> "+TXTFEND)
                parsedResponse = translatestr(response)
                if (len(parsedResponse) != 1) or not (parsedResponse[0] in 
                        (set([DICTVOWELPASS]) | game.ALLOWEDCARDS)):
                    notifyerror("""Please either name the card shown or enter 
'pass' if the player could not answer the suggestion...""","ui.suggest")
                    errCount += 1
                else:
                    if parsedResponse[0] == DICTVOWELPASS:
                        # Player passes - cannot answer suggestion
                        detective.event_pass(character,room,weapon,ixPlayer)
                        isItemSet = True
                    elif parsedResponse[0] in (character,room,weapon):
                        # Player shows card - answers suggestion
                        detective.event_seenresponse(parsedResponse[0],ixPlayer,0)
                        isItemSet = True
                        sugAnswered = ixPlayer
                    else:
                        notifyerror(
                            "That card was not mentioned in the suggestion...",
                            "ui.suggest")
                        errCount += 1
                    
                if errCount >= 3:
                    raise ValueError
            
        if sugAnswered is not None:
            # Suggestion answered - play stops going around circle
            break
            
    if sugAnswered is None:
        print("Jinkies! I think we've just about cracked this case!")
    elif sugAnswered == 1:
        print("Mmm hmm...")
    elif sugAnswered == 2:
        print("Huh...")
    else:
        print("Okay...")
        
    return sugAnswered
#
#
def accuse(detective,ixTurn,ixHotSeat,character,room,weapon):
    moveprompt(ixTurn,ixHotSeat)
    print(TXTFIMPORTANT+"I ACCUSE "+game.CARDNAMES[character]+" in the "+
        game.CARDNAMES[room]+" with\n  the "+game.CARDNAMES[weapon]+TXTFEND)
        
    if detective.DBGSCENARIO and DBGAUTORESPOND:
        if (character in detective.DBGSCENARIO[-1] and
                room in detective.DBGSCENARIO[-1] and
                weapon in detective.DBGSCENARIO[-1]):
            print(TXTFQUESTION+"So, were we right? -> "+TXTFEND+"Yes")
            print('Great! Nice work!')
            detective.event_accusationcorrect(character,room,weapon)
        else:
            print(TXTFQUESTION+"So, were we right? -> "+TXTFEND+"No")
            print("Aww, dang! That's us out of the game then... Sorry!\n"+
                "We'll get 'em next time!")
            detective.event_accusationwrong(character,room,weapon)
    else:
        if ANSWER is None:
            isItemSet = False
            errCount = 0
            while not isItemSet:
                moveprompt(detective.ixTurn,detective.ixHotSeat)
                parsedResponse = translatestr(input(TXTFQUESTION+
                    "So, were we right? -> "+TXTFEND))
                if parsedResponse[0] == DICTAFFIRMATIVE:
                    print('Great! Nice work!')
                    detective.event_accusationcorrect(character,room,weapon)
                    isItemSet = True
                    return True
                elif parsedResponse[0] == DICTNEGATIVE:
                    print("Aww, dang! That's us out of the game then... Sorry! \
\nWe'll get 'em next time!")
                    detective.event_accusationwrong(character,room,weapon)
                    isItemSet = True
                    return False
                else:
                    errCount += 1
                    notifyerror("I couldn't understand that... Come on - yes \
or no!\nThe suspense is killing me!","ui.accuse")
                        
                if errCount >= 5:
                    raise ValueError
        else:
            if character in ANSWER and room in ANSWER and weapon in ANSWER:
                moveprompt(detective.ixTurn,detective.ixHotSeat)
                print(TXTFIMPORTANT+"That's right!"+TXTFEND)
                detective.event_accusationcorrect(character,room,weapon,0)
                return True
            else:
                moveprompt(detective.ixTurn,detective.ixHotSeat)
                print(TXTFIMPORTANT+"That's not right!"+TXTFEND)
                detective.event_accusationwrong(character,room,weapon,0)
                return False
                
#
#
def observemove(detective,ixTurn,ixHotSeat):
    doneStageMove = doneStageSuggest = doneStageAccuse = doneAll = False
       
    # Possible move
    # Possible suggestion
    # Possible accusation
    #parsedResponse = translatestr(input(TXTFQUESTION+
    #    detective.playerCharIxs[detective.ixHotSeat]+"... "+TXTFEND))
    isItemSet = False
    errCount = 0
    while not isItemSet:
        moveprompt(ixTurn,ixHotSeat)
        parsedResponse = translatestr(input(TXTFQUESTION+
            "Does player "+str(detective.ixHotSeat)+
            " ("+game.CHARNAMES[detective.playerCharIxs[detective.ixHotSeat]]+
            ") move? -> "+TXTFEND))
        if len(parsedResponse) != 1:
            notifyerror("A yes or no answer is all that's needed",
                "ui.observemove")
            errCount += 1
        elif parsedResponse[0] == DICTAFFIRMATIVE:
            while not isItemSet:
                moveprompt(ixTurn,ixHotSeat)
                response = (input(TXTFQUESTION+
                    "Where do they move to? -> "+TXTFEND))
                destNode = None
                #TODO It was a mistake perhaps to translate cards directly to
                # numbers
                try:
                    destNode = int(response)
                except:
                    parsedResponse = translatestr(response)
                    if (len(parsedResponse) == 1 and 
                            parsedResponse[0] in game.ALLOWEDROOMS):
                        destNode = game.ROOMCARDNODES[parsedResponse[0] ]
                    else:
                        notifyerror("""Please give either the node number or the
name of a room""","ui.observemove")
                        errCount += 1
                
                if not destNode is None:
                    detective.event_move(destNode,detective.ixHotSeat)
                    isItemSet = True
                elif errCount >= 5:
                    raise ValueError
                    
        elif parsedResponse[0] == DICTNEGATIVE:
            isItemSet = True
            
        elif parsedResponse[0] != DICTNEGATIVE:
            notifyerror("A yes or no answer is all that's needed",
                "ui.observemove")
            errCount += 1
            
        if errCount >= 5:
            raise ValueError
        
    if (detective.charLocations[detective.playerCharIxs[detective.ixHotSeat]] in
            game.ALLOWEDROOMNODES):
        isItemSet = False
        suggestionMade = False
        errCount = 0
        while not isItemSet:
            moveprompt(ixTurn,ixHotSeat)
            parsedResponse = translatestr(input(TXTFQUESTION+
                "Does player "+str(detective.ixHotSeat)+
                " ("+game.CHARNAMES[detective.playerCharIxs[detective.ixHotSeat]]+
                ") make a suggestion? -> "+TXTFEND))
            if len(parsedResponse) != 1:
                notifyerror("A yes or no answer is all that's needed",
                    "ui.observemove")
                errCount += 1
            elif parsedResponse[0] == DICTAFFIRMATIVE:
                isCulpritSet = isWeaponSet = False
                culprit = weapon = None
                errCount = 0
                while not isCulpritSet:
                    moveprompt(ixTurn,ixHotSeat)
                    parsedResponse = translatestr(input(TXTFQUESTION+
                        "Who was suggested? -> "+TXTFEND))
                    if (len(parsedResponse) == 1 and 
                            parsedResponse[0] in game.ALLOWEDCHARS):
                        isCulpritSet = True
                        culprit = parsedResponse[0]
                    else:
                        notifyerror("I couldn't recognise that character",
                            "ui.observemove")
                        errCount += 1
                        if errCount >= 3:
                            raise ValueError
                errCount = 0
                while not isWeaponSet:
                    moveprompt(ixTurn,ixHotSeat)
                    parsedResponse = translatestr(input(TXTFQUESTION+
                        "What weapon was implicated? -> "+TXTFEND))
                    if (len(parsedResponse) == 1 and 
                            parsedResponse[0] in game.ALLOWEDWEAPS):
                        isWeaponSet = True
                        weapon = parsedResponse[0]
                    else:
                        notifyerror("I couldn't recognise that weapon",
                            "ui.observemove")
                        errCount += 1
                        if errCount >= 3:
                            raise ValueError
                #
                # Nailed down the suggestion
                room = game.ROOMNODECARDS[detective.charLocations[
                    detective.playerCharIxs[detective.ixHotSeat]]]
                detective.event_suggestion(culprit,room,weapon,
                    detective.ixHotSeat)
                #
                sugAnswered = False
                for ixPlayer in (
                        np.array(range(detective.ixHotSeat+1,
                        detective.ixHotSeat+detective.nPlayers)) 
                        % detective.nPlayers):
                        
                    if ixPlayer == 0:
                        # It's my turn to try answering the suggestion...
                        response = detective.answersuggestion(
                            culprit,room,weapon,detective.ixHotSeat)
                            
                        if response is game.NULLCARD:
                            moveprompt(ixTurn,ixHotSeat)
                            print(TXTFQUESTION+
                                "I pass - none of those cards here!"+TXTFEND)
                            isItemSet = True
                        else:
                            moveprompt(ixTurn,ixHotSeat)
                            print(TXTFQUESTION+
                                "I show the "+game.CARDNAMES[response]+
                                " card. Better luck next time, player "+
                                str(detective.ixHotSeat)+"!"+TXTFEND)
                            sugAnswered = True
                            isItemSet = True
                    else:
                        if detective.DBGSCENARIO and DBGAUTORESPOND:
                            if room in detective.DBGSCENARIO[ixPlayer]:
                                showCard = room
                            elif weapon in detective.DBGSCENARIO[ixPlayer]:
                                showCard = weapon
                            elif culprit in detective.DBGSCENARIO[ixPlayer]:
                                showCard = culprit
                            else:
                                showCard = game.NULLCARD
                                
                            if showCard == game.NULLCARD:
                                print(TXTFQUESTION+"Can player "+str(ixPlayer)+
                                    " respond with a card? -> "+TXTFEND+"No")
                                detective.event_pass(
                                    culprit,room,weapon,ixPlayer)
                                isItemSet = True
                            else:
                                print(TXTFQUESTION+"Can player "+str(ixPlayer)+
                                    " respond with a card? -> "+TXTFEND+"Yes")
                                notifydebug("AUTORESPOND","Player "+
                                    str(ixPlayer)+" secretly showed "+
                                    game.CARDNAMES[showCard]+" to player "+
                                    str(detective.ixHotSeat),"ui.observemove")
                                detective.event_unseenresponse(culprit,room,
                                    weapon,ixPlayer,detective.ixHotSeat)
                                isItemSet = True
                                sugAnswered = True       
                        else:
                            isItemSet = False
                            errCount = 0
                            while not isItemSet:
                                moveprompt(ixTurn,ixHotSeat)
                                parsedResponse = translatestr(
                                    input(TXTFQUESTION+"Can player "+str(ixPlayer)+
                                    " respond with a card? -> "+TXTFEND))
                                if len(parsedResponse) != 1:
                                    notifyerror(
                                        "A yes or no answer is all that's needed",
                                        "ui.observemove")
                                    errCount += 1
                                elif parsedResponse[0] == DICTAFFIRMATIVE:
                                    moveprompt(ixTurn,ixHotSeat)
                                    parsedResponse = translatestr(
                                        input(TXTFQUESTION+
                                        "Did you see the card? If so, what was it? -> "+
                                        TXTFEND))
                                    if len(parsedResponse) != 1:
                                        notifyerror("""Please answer either 
'no', or the name of the card you saw""","ui.observemove")
                                        errCount += 1
                                    elif parsedResponse[0] == DICTNEGATIVE:
                                        print("OK - well it was still a useful clue!")
                                        # Player responded, but we could not see the 
                                        # card
                                        detective.event_unseenresponse(culprit,room,
                                            weapon,ixPlayer,detective.ixHotSeat)
                                        isItemSet = True
                                        sugAnswered = True
                                    elif parsedResponse[0] in game.ALLOWEDCARDS:
                                        if parsedResponse[0] in (culprit,room,weapon):
                                            # We saw the card as it was shown!
                                            print("Jeepers! Nice snooping!")
                                            detective.event_seenresponse(
                                                parsedResponse[0],ixPlayer,
                                                detective.ixHotSeat)
                                            isItemSet = True
                                            sugAnswered = True
                                        else:
                                            notifyerror("""That card wasn't in 
the suggestion!""","ui.observemove")
                                            errCount += 1
                                    else:
                                        notifyerror("""Please answer either 
'no', or the name of the card you saw""","ui.observemove")
                                        errCount += 1
                                        
                                elif (parsedResponse[0] == DICTNEGATIVE or
                                        parsedResponse[0] == DICTVOWELPASS):
                                    # Player could not answer suggestion
                                    detective.event_pass(culprit,room,weapon,ixPlayer)
                                    isItemSet = True
                                else:
                                    notifyerror(
                                        "A yes or no answer is all that's needed",
                                        "ui.observemove")
                                    errCount += 1
                                    
                                if errCount >= 3:
                                    raise ValueError
                            
                    if sugAnswered:
                        # Suggestion answered - play stops going around circle
                        break
                
                suggestionMade = True
                        
            elif parsedResponse[0] == DICTNEGATIVE:
                suggestionMade = False
                isItemSet = True
            else:
                notifyerror("A yes or no answer is all that's needed",
                    "ui.observemove")
                errCount += 1
                
            if errCount >= 5:
                raise ValueError
        
        
        isItemSet = False
        accusationMade = False
        errCount = 0
        while not isItemSet:
            moveprompt(ixTurn,ixHotSeat)
            parsedResponse = translatestr(input(TXTFQUESTION+
                "Does player "+str(detective.ixHotSeat)+
                " ("+game.CHARNAMES[detective.playerCharIxs[detective.ixHotSeat]]+
                ") make an accusation? -> "+TXTFEND))
            if len(parsedResponse) != 1:
                notifyerror("A yes or no answer is all that's needed",
                    "ui.observemove")
                errCount += 1
                
            elif parsedResponse[0] == DICTAFFIRMATIVE:
                isCulpritSet = isWeaponSet = isRoomSet = False
                culprit = weapon = room = None
                errCount = 0
                while not isCulpritSet:
                    moveprompt(ixTurn,ixHotSeat)
                    parsedResponse = translatestr(input(TXTFQUESTION+
                        "Who stands accused? -> "+TXTFEND))
                    if (len(parsedResponse) == 1 and 
                            parsedResponse[0] in game.ALLOWEDCHARS):
                        isCulpritSet = True
                        culprit = parsedResponse[0]
                    else:
                        notifyerror("I couldn't recognise that character",
                            "ui.observemove")
                        errCount += 1
                        if errCount >= 3:
                            raise ValueError
                errCount = 0
                while not isWeaponSet:
                    moveprompt(ixTurn,ixHotSeat)
                    parsedResponse = translatestr(input(TXTFQUESTION+
                        "What weapon was implicated? -> "+TXTFEND))
                    if (len(parsedResponse) == 1 and
                            parsedResponse[0] in game.ALLOWEDWEAPS):
                        isWeaponSet = True
                        weapon = parsedResponse[0]
                    else:
                        notifyerror("I couldn't recognise that weapon",
                            "ui.observemove")
                        errCount += 1
                        if errCount >= 3:
                            raise ValueError
                
                room = game.ROOMNODECARDS[detective.charLocations[
                    detective.playerCharIxs[detective.ixHotSeat]]]
                detective.event_accusation(culprit,room,weapon,detective.ixHotSeat)
                
                if detective.DBGSCENARIO and DBGAUTORESPOND:
                    # Auto-respond to accusation
                    if ((culprit in detective.DBGSCENARIO[-1]) and
                            (room in detective.DBGSCENARIO[-1]) and
                            (weapon in detective.DBGSCENARIO[-1])):
                        # Accusation was correct
                        moveprompt(detective.ixTurn,detective.ixHotSeat)
                        print(TXTFIMPORTANT+"That's right!"+TXTFEND)
                        print("Oh no! Darn... Well congratulations, player "+
                            str(detective.ixHotSeat)+"!")
                        detective.event_accusationcorrect(culprit,room,weapon,
                            detective.ixHotSeat)
                        isItemSet = True
                        accusationMade = True
                    else:
                        # Accusation was wrong
                        moveprompt(detective.ixTurn,detective.ixHotSeat)
                        print(TXTFIMPORTANT+"That's not right!"+TXTFEND)
                        print("Phew, that was close! Hard luck, player "+
                            str(detective.ixHotSeat)+"!")
                        detective.event_accusationwrong(culprit,room,weapon,
                            detective.ixHotSeat)
                        isItemSet = True
                        accusationMade = True
                elif ANSWER is not None:
                    if (culprit in ANSWER and room in ANSWER and 
                            weapon in ANSWER):
                        moveprompt(detective.ixTurn,detective.ixHotSeat)
                        print(TXTFIMPORTANT+"That's right!"+TXTFEND)
                        print("Oh no! Darn... Well congratulations, player "+
                            str(detective.ixHotSeat)+"!")
                        detective.event_accusationcorrect(
                            culprit,room,weapon,detective.ixHotSeat)
                        isItemSet = True
                        accusationMade = True
                    else:
                        moveprompt(detective.ixTurn,detective.ixHotSeat)
                        print(TXTFIMPORTANT+"That's not right!"+TXTFEND)
                        print("Phew, that was close! Hard luck, player "+
                            str(detective.ixHotSeat)+"!")
                        detective.event_accusationwrong(
                            culprit,room,weapon,detective.ixHotSeat)
                        isItemSet = True
                        accusationMade = True
                else:
                    # Take response from conversant
                    while not isItemSet:
                        moveprompt(ixTurn,ixHotSeat)
                        parsedResponse = translatestr(input(TXTFQUESTION+
                            "So, are they right!? -> "+TXTFEND))
                        if parsedResponse[0] == DICTAFFIRMATIVE:
                            print("Oh no! Darn... Well congratulations, player "+
                                str(detective.ixHotSeat)+"!")
                            detective.event_accusationcorrect(culprit,room,weapon,
                                detective.ixHotSeat)
                            isItemSet = True
                            accusationMade = True
                        elif parsedResponse[0] == DICTNEGATIVE:
                            print("Phew, that was close! Hard luck, player "+
                                str(detective.ixHotSeat)+"!")
                            detective.event_accusationwrong(culprit,room,weapon,
                                detective.ixHotSeat)
                            isItemSet = True
                            accusationMade = True
                        else:
                            notifyerror("""Just tell me yes or no - the suspense
is killing me!""","ui.observemove")
                            errCount += 1
                            if errCount >= 3:
                                raise ValueError
                        
            elif parsedResponse[0] == DICTNEGATIVE:
                accusationMade = False
                isItemSet = True
                
            else:
                notifyerror("A yes or no answer is all that's needed",
                    "ui.observemove")
                errCount += 1
                
            if errCount >= 5:
                raise ValueError


#### PYPLOT-BASED PLOTTING FUNCTIONS ###########################################
#
def plotscenariomarginals(charMarginal,roomMarginal,weapMarginal):        
    figure = plt.figure(1)
    plt.clf()
    ax = figure.add_subplot(3,1,1)
    ax.bar(range(game.NCHARS),charMarginal)
    ax.set_title("Hypothesis Count by Character")
    ax.set_xlim(-0.2,game.NCHARS)
    ax.set_ylim(0.0,1.0)
    ax.set_xticks(np.array(range(game.NCHARS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.CHARNAMES)
    ax = figure.add_subplot(3,1,2)
    ax.bar(range(game.NROOMS),roomMarginal)
    ax.set_title("Hypothesis Count by Room")
    ax.set_xlim(-0.2,game.NROOMS)
    ax.set_ylim(0.0,1.0)
    ax.set_xticks(np.array(range(game.NROOMS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.ROOMNAMES)
    ax = figure.add_subplot(3,1,3)
    ax.bar(range(game.NWEAPS),weapMarginal)
    ax.set_title("Hypothesis Count by Weapon")
    ax.set_xlim(-0.2,game.NWEAPS)
    ax.set_ylim(0.0,1.0)
    ax.set_xticks(np.array(range(game.NWEAPS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.WEAPNAMES)
    plt.draw()
    plt.show()
#
#
def plotforbidden(forbiddenMx):
    nPlayers = forbiddenMx.shape[0] - 1
    figure = plt.figure(2)
    plt.clf()
    ax = figure.add_subplot(1,1,1)
    ax.scatter(tuple(range(nPlayers+1))*game.NCARDS,
        tuple(range(game.NCARDS))*(nPlayers+1),s=80,marker='s',
        facecolor=(0.,0.,0.,0.))
    pForbd = []
    cForbd = []
    for ixPlayer in range(nPlayers+1):
        for ixCard in range(forbiddenMx.shape[1]):
            if forbiddenMx[ixPlayer,ixCard]:
                pForbd.append(ixPlayer)
                cForbd.append(ixCard)
    ax.scatter(pForbd,cForbd,c='r',s=50,marker='x')
    ax.set_title("Forbidden Card Locations")
    ax.set_xticks(range(nPlayers+1))
    ax.set_yticks(range(game.NCARDS))
    ax.set_yticklabels(game.CARDNAMES)
    plt.draw()
    plt.show()
#
#
def plotmovediagnostics(statsDict):
    roomExpEntropies = statsDict.get('roomExpEntropies',None)
    presentEntropy = statsDict.get('presentEntropy',None)
    roomExpRemoteness = statsDict.get('roomExpRemoteness',None)
    presentRemoteness = statsDict.get('presentRemoteness',None)
    roomScores = statsDict.get('roomScores',None)
    stickScore = statsDict.get('stickScore',None)
    rollScore = statsDict.get('rollScore',None)
    passageScore = statsDict.get('passageScore',None)
    #
    maxScore = np.max(roomScores)
    maxScore = np.max([maxScore,rollScore,stickScore])
    if np.isfinite(passageScore) and passageScore > maxScore:
        maxScore = passageScore
    #
    figure = plt.figure(3)
    plt.clf()
    ax = figure.add_subplot(3,1,1)
    ax.bar(range(game.NROOMS),roomExpEntropies)
    ax.set_title("Expected Entropy by Room")
    ax.set_xlim(-0.2,game.NROOMS)
    ax.set_ylim(0.,maxScore * 1.2)
    ax.set_xticks(np.array(range(game.NROOMS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.ROOMNAMES)
    ax.plot([-0.2,game.NROOMS],[presentEntropy,presentEntropy],'-r')
    ax = figure.add_subplot(3,1,2)
    ax.bar(range(game.NROOMS),roomExpRemoteness)
    ax.set_title("Remoteness by Room")
    ax.set_xlim(-0.2,game.NROOMS)
    ax.set_ylim(0.,maxScore * 1.2)
    ax.set_xticks(np.array(range(game.NROOMS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.ROOMNAMES)
    ax.plot([-0.2,game.NROOMS],[presentRemoteness,presentRemoteness],'-r')
    ax = figure.add_subplot(3,1,3)
    ax.bar(range(game.NROOMS),roomScores)
    ax.set_title("Score by Room")
    ax.set_xlim(-0.2,game.NROOMS)
    ax.set_ylim(0.,maxScore * 1.2)
    ax.set_xticks(np.array(range(game.NROOMS),dtype=np.float64)+0.4)
    ax.set_xticklabels(game.ROOMNAMES)
    ax.plot([-0.2,game.NROOMS],[stickScore,stickScore],'-r')
    if np.isfinite(passageScore):
        ax.plot([-0.2,game.NROOMS],[passageScore,passageScore],'-g')
    ax.plot([-0.2,game.NROOMS],[rollScore,rollScore],'-k')
    plt.draw()
    plt.show()
#
#
def plotentropydiagnostics(mat):
    xpos,ypos = np.meshgrid(np.arange(mat.shape[0]) + 0.25,
        np.arange(mat.shape[1]) + 0.25)
    xpos = xpos.flatten()
    ypos = ypos.flatten()
    zpos = np.zeros(mat.shape[0]*mat.shape[1])
    dx = 0.5 * np.ones_like(zpos)
    dy = dx.copy()
    dz = mat.flatten() - np.min(mat)
    
    fig = plt.figure(4)
    plt.clf()
    ax = Axes3D(fig)
    ax.bar3d(xpos,ypos,zpos, dx, dy, dz, alpha=0.5)
    ticksx = np.arange(0.5, game.NWEAPS, 1)
    plt.xticks(ticksx, game.WEAPNAMES)
    ticksy = np.arange(0.5, game.NCHARS, 1)
    plt.yticks(ticksy, game.CHARNAMES)
    ax.set_xlabel('Weapon')
    ax.set_ylabel('Character')
    ax.set_zlabel('Entropy')

#### INTERNAL FUNCTIONS ########################################################
#
def moveprompt(ixTurn,ixPlayer):
    if ixPlayer:
        sys.stdout.write(TXTFQUESTION+"[Turn {:2}".format(ixTurn)+
            ", Player {:1}".format(ixPlayer)+"] "+TXTFEND)
    else:
        sys.stdout.write(TXTFQUESTION+"[Turn {:2}".format(ixTurn)+
            ", My move!] "+TXTFEND)
#
#
def translatestr(strIn):
    """Parse a user response for known words and phrases."""
    strIn = strIn.lower().split()
    strOut = []
    ixWord = 0
    while ixWord < len(strIn):
        wordIDd = False
        for dictKey in DICTIONARYKEYS:
            dictKeySplit = dictKey.split()
            correct = True
            for ixKeyWord in range(len(dictKeySplit)):
                try:
                    if strIn[ixWord + ixKeyWord] != dictKeySplit[ixKeyWord]:
                        correct = False
                except:
                    # Exception occurs if we go past the length of strIn
                    correct = False
            if correct:
                strOut.append(DICTIONARY[dictKey])
                wordIDd = True
                ixWord += len(dictKeySplit)
                break
        
        if not wordIDd:
            strOut.append(DICTWORDUNKNOWN)
            ixWord += 1
            
    return strOut
