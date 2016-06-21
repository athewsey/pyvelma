#!/usr/bin/python2
"""A script to demonstrate the Velma Cluedo AI as an opponent.

A random 2-player game is initialised; and then hosted by a velma.Detective
object. No reminders of your hand are issued by the UI in play, so make a note
at the start!

"""

################################################################################
#### IMPORT MODULES/PACKAGES ###################################################
#
#### STANDARD PACKAGES #########################################################
import random
#
#### VELMA #####################################################################
try:
    # For when velma has been installed:
    import velma
except:
    # Development environment: We're in the bin directory of the velma package:
    import sys
    sys.path.append('..')
    import velma
    del sys


################################################################################
#### MAIN FUNCTION #############################################################
#
def main():
    """Demonstrate Velma's capacity as a Cluedo opponent using the default UI.
    
    This is the main function; executed when the file is invoked as a script.
    
    """
    velma.ui.greet()
    Velma = velma.Detective()
    #
    # Random card deal:
    deck = set(range(velma.game.NCARDS))
    murderer = velma.game.CHARS[random.sample(range(velma.game.NCHARS),1)[0]]
    deck.remove(murderer)
    murderRoom = velma.game.ROOMS[random.sample(range(velma.game.NROOMS),1)[0]]
    deck.remove(murderRoom)
    murderWeap = velma.game.WEAPS[random.sample(range(velma.game.NWEAPS),1)[0]]
    deck.remove(murderWeap)
    ixDealer = random.randint(0,1)
    playerHand = random.sample(deck,9)  # Random.sample is without replacement
    for card in playerHand:
        deck.remove(card)
    velmaHand = deck
    playerCharCards = random.sample(velma.game.ALLOWEDCHARS,2)
    #
    # Tell the user who they're playing and what cards they hold:
    print(velma.ui.TXTFIMPORTANT +
        "You are playing as " + str(velma.game.CARDNAMES[playerCharCards[1]]) +
        velma.ui.TXTFEND)
    print(velma.ui.TXTFIMPORTANT +
        "You hold:\n" + str([velma.game.CARDNAMES[card] for card in playerHand])
        + "\n" + velma.ui.TXTFEND)
    raw_input("Make a note of these cards - you won't be reminded again!\n\
Press Enter to continue...")
    #
    # Tell the UI what the answer is
    velma.ui.ANSWER = (murderer,murderRoom,murderWeap)
    #
    # Initialise the detective with its hand and make it secretive
    Velma.SECRETIVE = True
    Velma.initialise(
        nPlayers=2,
        playerCharCards=playerCharCards,
        ixDealer=ixDealer,
        playerCardHeldCounts=(9,9),
        myCards=velmaHand
        )
    # Have the detective host a game of Cluedo:
    Velma.run()
    raw_input("Velma exited. Press enter to continue...")


################################################################################
#### EXECUTE ###################################################################
#
if __name__ == '__main__':
    main()
#
#### EOF #######################################################################
################################################################################
