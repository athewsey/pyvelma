"""Parallelised Velma core functions."""

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
#
## OTHER PARTS OF VELMA ########################################################
import velma.game as game           # Definitions of the Cluedo game
import velma.ui as ui               # Default user interface for Velma

def suggestionexpposteriors(hypotheses,character,room,weapon):
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
    # Calculate the number of players in the game
    nPlayers = len(hypotheses)-1
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
        (nPlayers-1,   # Players that could answer
        7,                  # Cards this player could hold
        game.NCHARS,game.NROOMS,game.NWEAPS # Suggestion murder scenario
        ))
    # Lastly, we could have no answer from anyone
    hypCountsNoAnswer = np.zeros((game.NCHARS,game.NROOMS,game.NWEAPS))
    #
    # Sort the hypotheses:
    for hypothesis in hypotheses:
        for ixPlayer in range(1,nPlayers):
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
    #   Velma.hypCountsByScenario[:,:,:] = 
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
    for ixOPlayer in range(nPlayers-1):
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
    totalHypCount = len(hypotheses)
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
