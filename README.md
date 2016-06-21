# "Velma" - An assistant & AI for 'Cluedo'

## Introduction

Velma was conceived on holiday in the summer of 2013 in the gap between university and work. It was an opportunity for
the author to apply machine learning techniques on a practical problem, and a nice way to pick up Python.

Python was nice to write, but rather slow for this application as you'll see if you try out the code. The 
computationally-intensive nature of the solution sat poorly with the sluggish interpreter and lack of multithreading
support - leading to tediously long waits for move selection.

As such, development of this incarnation has been largely abandoned. The author is working on a private project to 
improve the algorithm and package it in a mobile app with a decent GUI.

If you're interested in improving or forking Velma, do get in touch - I might be able to offer some further improvements
from the mobile journey!


## Licensing

'Cluedo' and 'Clue' (by which name the game is known in North America) are registered trademarks of Hasbro Ltd. at the
time of writing this notice.

The names of characters and other elements of the game; the board layout; certain game mechanics; and any graphics
produced for publications of the game, may also be protected in various jurisdictions.

The author of Velma has no affiliation with and claims no rights regarding the game itself. Although Velma necessarily
contains logic relating to the game, this assistant/adversary software does not constitute a playable instance of the 
game in itself.

Under these restrictions and to the extent permitted by local law, Alex Thewsey as author of this software has waived 
all copyright and relating or neighbouring rights according to the terms of the Creative Commons CC0 1.0 Public Domain
Dedication.


## Using / Demonstrating the Code

Run the /bin/ scripts to demonstrate the code in action. Velma refers to non-room board squares by number, so you will
probably need /doc/boardmap.jpg open as a reference. If you struggle to get Velma to understand a card, check out the 
dictionary in ui.py.


## How It Works

### Deduction by Constraints and Hypotheses

At the start of the game Velma is initialised knowing what cards it holds; the number of cards held by each player, and
the character avatar (hence location, by the position of the start squares) of each player.

A user keeps Velma informed of movements, suggestions, responses, and accusations through the game.

Events in the game represent constraints on the solution (i.e. which character, weapon and room are in the 'murder' 
hand), which Velma tracks:

    - A player showing Velma a card in response to the user's suggestion confirms they have that particular card.
    - A player responding to another player's suggestion indicates they have at least one of the character, room, or 
      weapon suggested. (Assistant Velma is sneaky, and will let you enter which card it was if you catch a glimpse).
    - A player unable to answer a suggestion indicates they have none of the suggested cards.
    - An incorrect accusation (though very rare) invalidates a particular murder character/room/weapon set.
      Traditionally, ousted players should remain in the game to answer suggestions so no immediate additional 
      information about their cards is gained.

Bad human players keep a list of who has which card. Better human players keep a matrix of possible & forbidden card 
locations (e.g. proved card X is not with player A, but it might still be with player B or in the murder solution).

Velma maintains a matrix of forbidden locations (which is determined by passes and seen responses) but also the list of
unseen responses whose constraints are too complex for humans to systematically track.

Towards the end of the game, Velma enumerates all possible location combinations of every card. This allows exact 
calculation of the probability of each solution (i.e. proportion of the feasible hypotheses that have that given 
character/room/weapon combination in the murder solution hand).

In earlier stages, there are way too many to enumerate so instead Velma generates `HYPSAMPLECOUNT` feasible hypotheses 
satisfying observed constraints. After every observed event:

    - The new constraint is added to the appropriate list (e.g. narrowing down the forbidden locations matrix).
    - Invalidated hypotheses not satisfying the new constraint are removed.
    - If the estimated number of feasible hypotheses falls below a threshold, Velma replaces the hypotheses list with 
      a fully enumerated, duplicate-free list of possibilities.
    - Otherwise, replacement hypotheses are generated satisfying the new constraint to get back to `HYPSAMPLECOUNT`.


### Statistics on the Hypothesis Set

By the mechanism outlined above, Velma maintains a list of hypotheses regarding where every card in the deck might be.
Towards the end of the game, that list is the actual list of possibilities. Earlier on, assuming our hypothesis
generating algorithm is fair, it's a representative sample.

One of the simplest metrics that gives us (which Velma graphs as it runs in assistant mode) is the probability 
distribution over murder suspects: Count up the number of hypotheses identifying each character as the murderer, and
divide by the total number of hypotheses. In the beginning, it will be uniform except for any characters whose cards
Velma holds (zero probability). As turns go by and new information emerges, some characters will be invalidated 
completely and others will become more or less probable.

Beyond this 1D distribution of probability by character, Velma can track the 3D distribution of solution probability by
character, weapon and room. As before, just count the number of hypotheses with that particular solution character, 
weapon, and room; then divide by the total number of hypotheses. When a particular combination reaches a probability of 
`PACCUSATIONTHRESH`, Velma will make the accusation at the next available turn.

Although Velma uses the probability of the most likely member to decide when to make accusations, it's not the best 
measure of how much information/uncertainty is contained in a distribution. For that, we use *entropy*.

By choosing actions that minimise the entropy of the solution probability distribution each turn, Velma will gather
information that will help solve the mystery.


### Using Entropy and Expectation to Choose Actions

The game rules compel a player answering a suggestion to show a suggested card if they are able, and we can reasonably 
expect players to show the least helpful (i.e. least entropy-reducing) card if they have a choice. These facts allow us
to map any card locations hypothesis to the expected response if we were to make a given suggestion.

A suggestion response yields (possibly) new constraints and a revised set of feasible hypotheses. A revised hypothesis
set allows us to calculate the posterior solution probability distribution and hence entropy. Iterating over the 
original hypotheses, we can calculate the expected distribution of responses to a suggestion; the consequences of each
response; and hence the expected posterior solution entropy after making that suggestion.

Performing this calculation for each suggestion in turn (possibly excluding those where we already know the location of
all 3 cards so could not gain any information), we can score every possible suggestion character/room/weapon combination
by how much it is expected to reduce the entropy of the solution probability distribution. Velma should therefore choose
the suggestion predicted to provide the most new information.

Unfortunately by the standard rules, suggestions can only name the room the suggester's character is currently in. We've
actually calculated a list of optimal suggestions for each room, and a metric by which to rank which rooms we'd rather
be in (expected entropy of the entropy-minimising/"best" suggestion for each room).

To fully select moves though, Velma must also consider the concept of remoteness: Moving is by dice-roll and there's no
point making a perfect suggestion if it lands you so far away from the murder room you get beaten to the accusation. 
It's also fairly common to end up unable to reach a room to make a suggestion in a turn - meaning Velma must choose the
best direction to move in to get closer to the goal.

The probability distribution of rolling 2 fair dice may be converted to a function mapping a distance to the expected
number of dice-rolls required to travel it. Velma scores the 'remoteness' of a square on the board as the expected 
number of dice-rolls required to travel from it to the murder location (the distance to every room is calculated, then
the distances are combined by average weighted by the marginal probabilities that each room is the murder location).

Velma very crudely combines these scores by adding them up: expected posterior entropy in nats + expected turns
required to move to the murder location. For non-room squares and the room the turn starts in (because you can't sit in
the same room making suggestions), posterior entropy is equal to current entropy.

At long last, we've scored every possible move and calculated the optimal suggestion for each room we might end up in.
As a final caveat, if we're in a room with a secret Passage, Velma will compare the score of the room at the other end
with the expected score we can achieve if we roll the dice.

By this process, Velma has ranked every decision involved in a turn:

    - Whether to take a secret passage or roll the dice
    - Where to move after rolling the dice
    - What character and weapon to suggest if landing in a room
    - What accusation to follow the suggestion with, if any

When asked to respond to a suggestion for which Velma holds multiple cards; the card already shown to the suggesting
player (if any); or else the card most often shown previously will be chosen.


## Successes and Limitations

In our few tests Velma proved extremely successful in games with 3 players or more, and distinctly average one-on-one.
Any human can play with a forbidden locations matrix. Velma's real advantage is in applying unseen suggestion responses
demonstrating the responding player has one of 3 possible cards - and this information source is not available in 2
player games.

In 2-player situations, human players are also more likely to search for patterns in suggestions or movements that might
indicate the intentions of the opponent. Arguably there is as much potential to be misled as helped by this, but when
humans know they're playing against an algorithm, they're more likely to correctly interpret patterns in Velma's 
choices and use them to infer extra information.

Although hard to say without further investigation, it's also likely improving the following issues would improve 
Velma's results.


### Greedy Behaviour and Scoring Heuristics

Room remoteness is Velma's only consideration beyond the current turn. It's possible a coordinated suggestion strategy
over several turns could yield more information than choosing the best suggestion for each turn individually. However,
computational intensity would be very high.

Scoring squares by adding entropy nats to expected turn counts is very poor too, being dimensionally inconsistent... It 
may be possible and preferable to rephrase scores in terms of a predicted entropy reduction from the current state per 
turn - to be maximised rather than minimised.

In retrospect, I also have no idea why Velma uses a probability threshold for accusation rather than an entropy 
threshold - given our stated premise that entropy is the best available measure of uncertainty in the distribution!


### Performance

As mentioned in the introduction, this solution struggles with computational performance to keep pace with humans
playing the game. In its current form, it's not an assistant you could subtly use under the table... ;-)

An attempt to use `parcore` to parallelise the heavy lifting of the hypothesis regeneration and expected posterior
entropy calculations was found to make things worse rather than better.

This was a while ago, and Python may well have newer and better or improved tools to achieve these aims now. Porting to
Java, although probably beneficial in the long run, introduces its own challenges due to the lack of any good ND array 
maths platform on a par with `numpy`. Although more for debugging purposes than as a final product UI, the graphing 
abilities of `matplotlib` were also extremely handy.

To easily adapt this software to another environment, you will likely want (in descending order of importance):

    1. A fast `Set` implementation with O(1) `includes`, and fast `union`/`difference` methods.
    2. Easy support for parallelism and related optimisations.
    3. A fast and easy facility to do maths on N-dimensional matrices.
    4. An easy graphing library to debug and improve the algorithm.

Since Velma's current code was written as an idle, exploratory project in such an environment without parallelism, 
there's probably plenty of opportunities already to refactor for speed too.


### Mindgames

It's possible that an achievably basic theory of mind tracking other players might be sufficient to allow Velma to 
mislead the competition. Anecdotal evidence suggests this is a common strategy, and particularly relevant to one-on-one
games.

As a first step, some facility should be implemented to identify players/users at the start of each game and log the
procedures of all games to build a data set. 

Game logging implemented in Velma itself would:

    - Contain a lot of uncertainty (as each player sees only a fraction of the total information in 3+ player games); 
      **but**
    - May form the basis of a mechanism for the detective to learn and adapt to new players without special access to 
      usually unavailable information (e.g. when used as an assistant in real-life games).

By contrast, logging implemented in a game server and subsequently post-processed by the detective would provide a more
complete data set for testing theories of mind, but would not be available for 'live' running.

    - Is it fair practice to examine everybody's hand at the end of the game? Maybe the answer is different if you have
      a perfect memory of every suggestion made throughout.
    - But "You had Miss Scarlett all along!" is a conceivable human conversation at the end of a game...


### The core-ui Interface and Code Structure (An Apology)

Hook and event methods!? It's not like Python isn't object-oriented - I was just new to the language and more interested
in the mathematical problem than the architecture of the solution, so all sensible design considerations went out the 
window.

The code is also littered with disabled experiments into game logging, alternative interfaces, and parallelism.

Velma is being released as-is now because I've already spent years pretending I'll find the time to tidy it up.
Hopefully it will still be of use and the clutter will illustrate thought processes on where development could go next.
Sorry!
