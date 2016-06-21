#!/usr/bin/python3
"""A script to demonstrate the Velma Cluedo AI in a synthetic scenario."""

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
#### CONSTANTS #################################################################
#
# Respond to suggestions/etc automatically, or prompt for user input?
autorespond = True
#
# Characters played by each player (starting with Velma, must be full names
# from velma.game.CARDNAMES):
characters = ('Mrs. White','Prof. Plum','Mrs. Peacock','Col. Mustard')
#
# Number of places around from Velma the dealer is sat:
dealer = 1
#
# Cards held by each player and then murder envelope (must be full names from
# velma.game.CARDNAMES):
scenario = (
        ('Col. Mustard','Dining Room','Billiard Room','Lead Pipe'),
        ('Mrs. Peacock','Prof. Plum','Hall','Library'),
        ('Conservatory','Lounge','Study','Knife','Candlestick'),
        ('Mrs. White','Mr. Green','Ballroom','Revolver','Rope'),
        ('Miss Scarlet','Kitchen','Wrench'))


################################################################################
#### MAIN FUNCTION #############################################################
#
def main():
    """Demonstrate Velma's Cluedo AI in a synthetic scenario.
    
    This is the main function; executed when the file is invoked as a script.
    
    """
    velma.ui.greet()
    Velma = velma.Detective()
    # Set the UI to autorespond, or not:
    velma.ui.DBGAUTORESPOND = autorespond
    # Set the scenario up:
    playerCharCards = tuple(
        velma.game.CARDNAMEIDS[card] for card in characters)
    DBGSCENARIO = tuple(
        tuple(velma.game.CARDNAMEIDS[card] for card in hand) 
        for hand in scenario)
    # Initialise the detective with the scenario
    Velma.initialise(
        ixDealer = dealer,
        playerCharCards = playerCharCards,
        DBGSCENARIO = DBGSCENARIO
        )
        
    print(Velma.mappossiblemoves(51))    
        
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
