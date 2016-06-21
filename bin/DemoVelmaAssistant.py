#!/usr/bin/python3
"""A script to demonstrate the Velma Cluedo assistant."""

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
    """Demonstrate Velma's capacity as a Cluedo assistant using the default UI.
    
    This is the main function; executed when the file is invoked as a script.
    
    """
    velma.ui.greet()
    Velma = velma.Detective()
    # Initialise with default UI:
    Velma.initialise()
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
