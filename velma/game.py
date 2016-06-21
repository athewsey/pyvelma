"""Game-defining constants (and the odd function) concerning Cluedo.

This module defines the cards, dice and board used in the game; as well as
any other relevant information.

"""


################################################################################
#### LIBRARIES #################################################################
#
import numpy as np  # Numpy arrays and function vectorisation


################################################################################
#### BASE CONSTANTS ############################################################
# To tweak the game definition, modify these constants only. The "derived
# constants" are taken from them automatically, and should not need tweaking!
#
# Allowable player counts
MAXPLAYERS = 6
MINPLAYERS = 2
#
# Function of the dice. WARNING: Changing the dice definition necessitates a 
# redefinition of the ``dicerollstomove()`` function below, which MUST be an
# efficient implementation (i.e. probably use an approximation).
DICEMIN = 2
DICEMAX = 12
DICEPS = np.array((0.,0.,1./36.,1./18.,1./12.,1./9.,5./36.,1./6.,
    5./36.,1./9.,1./12.,1./18.,1./36.)) # DICEPS[x] = Pr(Dice = x)
#
# Cards in the game
CHARNAMES = ('Col. Mustard','Prof. Plum','Mr. Green','Mrs. Peacock',
    'Miss Scarlet','Mrs. White')
CHARIXSTARTORDER = (4,0,5,2,3,1) # Character game start priority in the rules
ROOMNAMES = ('Hall','Lounge','Dining Room','Kitchen','Ballroom','Conservatory',
    'Billiard Room','Library','Study')
WEAPNAMES = ('Knife','Candlestick','Revolver','Rope','Lead Pipe','Wrench')
#
# Definition of allowed moves on board from each square (no secret passages)
NULLNODE = 0
BOARDNODES = ((),       # 0: Null node
    (44,),              # 1: Lounge
    (6,),               # 2: Miss Scarlet Start Square [8*, 10, 12]
    (20,62,63),         # 3: Hall (Closed doors to 20 and 62 in new Cluedo)
    (9,),               # 4: Not-quite-a-start-square
    (22,),              # 5: Study
    (2,7,10),
    (6,11),
    (9,12),
    (4,8,13),
    (6,11,14),          # 10
    (7,10,15),
    (8,13,16),
    (9,12,17),
    (10,15,18),
    (11,14,19),
    (12,17,20),
    (13,16,21),
    (14,19,28),
    (15,18,29),
    (3,16,21,30),       # 20 (Closed door to 3 on new Cluedo)
    (17,20,22,31),
    (5,21,23,32),
    (22,24,33),
    (23,25,34),
    (24,26,35),
    (25,27,36),
    (26,37),
    (18,29,45),
    (19,28,46),
    (20,31,47),         # 30
    (21,30,32,48),
    (22,31,33,49),
    (23,32,34),
    (24,33,35),
    (25,34,36),
    (26,35,37),
    (27,36,38),
    (37,),              # 38: Prof. Plum Start Square [8*,10,11]
    (40,52),
    (39,41,53),         # 40
    (40,42,54),
    (41,43,55),
    (42,44,56),
    (1,43,44,57),
    (28,44,46,58),
    (29,45,59),
    (30,48,66),
    (31,47,49,67),
    (32,48),
    (78,96),            # 50: Library (Closed door to 96 in new Cluedo)
    (52,),              # 51: Col. Mustard Start Square [8*,8,12]
    (39,51,53,68),
    (40,52,54,69),
    (41,53,55,70),
    (42,54,56,71),
    (43,55,57,72),
    (44,56,58,73),
    (45,57,59,74),
    (46,58,60,75),
    (59,61,76),         # 60
    (60,62),
    (3,61,63),          # (Closed door to 3 on new Cluedo)
    (3,62,64),
    (63,65),
    (64,66),
    (47,65,67,77),
    (48,66,78),
    (52,69),
    (53,68,70),
    (54,69,71),         # 70
    (55,70,72),
    (56,71,73),
    (57,72,74,79),
    (58,73,75),
    (59,74,76,80),
    (60,75,81),
    (66,78,82),
    (50,67,77,83),
    (73,99),            # 79: Dining Room (Closed door to 99 in new Cluedo)
    (75,81,84),         # 80
    (76,80,85),
    (77,83,86),
    (78,82,87),
    (80,85,89),
    (81,84,90),
    (82,87,91),
    (83,86,88,92),
    (87,93),
    (84,90,99),
    (85,89,100),        # 90
    (86,92,101),
    (87,91,93,102),
    (88,92,94,103),     # 93 (connects to useless 94)
    (93,95),            # 94 
    (94,96),            # 95 
    (50,95,97),         # 96 (Closed door to 50 on new Cluedo)
    (96,98),            # 97 
    (97,104),           # 98 (Closed door to 104 on new Cluedo)
    (79,89,100,105),    # 99 (Closed door to 79 on new Cluedo)
    (90,99,106),        # 100
    (91,102,107),
    (92,101,103,108),
    (93,102,109),
    (98,127),           # 104: Billiard Room (Closed door to 98 in new Cluedo)
    (99,106,110),
    (100,105,111),
    (101,108,112),
    (102,107,109,113),
    (103,108,114),
    (105,111,118),      # 110
    (106,110,119),
    (107,113,125),
    (108,112,114,126),
    (109,113,127),
    (116,132),
    (115,117,133),
    (116,118,134),
    (110,117,119,135),
    (111,118,120,136),
    (119,121,137),      # 120
    (120,122,138),
    (121,123,139),
    (122,124,140),
    (123,125,141),
    (112,124,126,142),
    (113,125,127,143),
    (104,114,126,144),
    (129,146),
    (128,130,147),
    (129,131,148),      # 130
    (130,132,149),
    (115,131,133,150),
    (116,132,134,151),
    (117,133,135,152),
    (118,134,136),
    (119,135,137,153),
    (120,136,138),
    (121,137,139),
    (122,138,140),
    (123,139,141),      # 140
    (124,140,142,153),  # 141 (Closed door to 153 in new Cluedo)
    (125,141,143),
    (126,142,144,154),
    (127,143,155),
    (146,),             # 145: Not-quite-a-start-square
    (128,145,147),
    (129,146,148),
    (130,147,149),
    (131,148,150,161),
    (132,149,151),      # 150
    (133,150,152,162),
    (134,151,163),
    (136,141,173,174),  # 153: Ballroom (Closed doors to 141 and 173 in new)
    (143,155,164),
    (144,154,156,165),
    (155,157,166),
    (156,158,167),
    (157,159,168),
    (158,160,169),
    (159,170),          # 160
    (149,),             # 161: Kitchen
    (151,163,172),
    (152,162,173),
    (154,165,174),
    (155,164,166,175),
    (156,165,167,176),
    (157,166,168),
    (158,167,169),
    (159,168,170),
    (160,169,171),      # 170
    (170,),             # 171: Mrs. Peacock Start Square [7*,9,10]
    (162,173,178),
    (153,163,172,179),  # 173 (Closed door to 153 in new Cluedo)
    (153,164,175,180),
    (165,174,176,181),
    (166,175,177),
    (176,),             # 177: Conservatory
    (172,179,182),
    (173,178,183),
    (174,181,184),      # 180
    (175,180,185),
    (178,183,186),
    (179,182,187),
    (180,185,188),
    (181,184,189),
    (182,187),
    (183,186,190),
    (184,189,195),
    (185,188),
    (187,191),          # 190
    (190,192),
    (191,196),
    (194,197),
    (193,195),
    (188,194),
    (192,),             # 196: Mrs. White Start Square [8,13*,16]
    (193,))             # 197: Mr. Green Start Square [10*,8,13]
#
# Nodes to correspond to each of the rooms stated in ROOMNAMES
ROOMNODES = np.array((3,1,79,161,153,177,104,50,5),dtype=np.uint8)
#
# Character start nodes on the board:
CHARSTARTNODES = np.array((51,38,197,171,2,196),dtype=np.uint8)
#
# Weapon start nodes on the board:
WEAPNAMES = ('Knife','Candlestick','Revolver','Rope','Lead Pipe','Wrench')
WEAPSTARTNODES = np.array((1,79,5,153,177,161),dtype=np.uint8)
#
# Secret passages available from each node:
PASSAGES = {
    1:177,              # Lounge to Conservatory
    5:161,              # Study to Kitchen
    161:5,              # Kitchen to Study
    177:1               # Conservatory to Lounge
    }
#
# Once a room has been entered; certain nodes need never feature on shortest 
# routes bridging rooms (no matter what destination or character piece 
# configuration). Specify nodes to trim from consideration here (or an empty
# tuple if you don't want to trim any).
NODESFORTRIM = (
    2,6,7,10,11,14,15,18,19,28,29,      # Miss Scarlet start area
    4,8,9,12,13,16,17,                  # Stupid corridor
    23,24,25,26,27,33,34,35,36,37,38,   # Prof Plum start area
    39,40,51,52,53,68,69,               # Col Mustard start area
    94,95,                              # Tiny corridor
    145,146,147,148,128,129,130,        # Ridiculous corridor
    167,168,169,170,171,157,158,159,160 # Mrs Peacock start area
    )


################################################################################
#### DERIVED CONSTANTS #########################################################
#
## DICE SPECIFICATION ##########################################################
# Probability of rolling at least x:
DICEPSMINROLL = tuple(1.-np.sum(DICEPS[:ix]) for ix in range(len(DICEPS)))
#
## CARD ID SETUP ###############################################################
NCHARS = len(CHARNAMES)
NROOMS = len(ROOMNAMES)
NWEAPS = len(WEAPNAMES)
NCARDS = NCHARS + NROOMS + NWEAPS
CHARS = tuple(range(NCHARS))
ROOMS = tuple(range(NCHARS, NROOMS+NCHARS))
WEAPS = tuple(range(NROOMS+NCHARS, NCARDS))
NULLCARD = NCARDS
#
ALLOWEDCHARS = set(CHARS)
ALLOWEDROOMS = set(ROOMS)
ALLOWEDWEAPS = set(WEAPS)
ALLOWEDCARDS = ALLOWEDCHARS | ALLOWEDROOMS | ALLOWEDWEAPS
#
# CARD INDEX INFORMATION #######################################################
CHARINDEX = {}
ROOMINDEX = {}
WEAPINDEX = {}
for ix in range(NCHARS):
    CHARINDEX[CHARS[ix]] = ix
for ix in range(NROOMS):
    ROOMINDEX[ROOMS[ix]] = ix
for ix in range(NWEAPS):
    WEAPINDEX[WEAPS[ix]] = ix
#
# CARD NAMES SETUP #############################################################
CARDNAMES = CHARNAMES + ROOMNAMES + WEAPNAMES
CARDNAMEIDS = {}
for ix in range(NCARDS):
    CARDNAMEIDS[CARDNAMES[ix]] = ix
#
## GAME BOARD ##################################################################
ALLOWEDNODES = set(
    [node for node in range(len(BOARDNODES)) if node != NULLNODE])
ALLOWEDROOMNODES = set(ROOMNODES)
#
CHARCARDSTARTNODES = {}
for ix in range(NCHARS):
    CHARCARDSTARTNODES[CHARS[ix]] = CHARSTARTNODES[ix]
ROOMCARDNODES = {}
for ix in range(NROOMS):
    ROOMCARDNODES[ROOMS[ix]] = ROOMNODES[ix]
ROOMNODECARDS = {}
for ix in range(NROOMS):
    ROOMNODECARDS[ROOMNODES[ix]] = ROOMS[ix]
ROOMNODEIXS = {}
for ix in range(NROOMS):
    ROOMNODEIXS[ROOMNODES[ix]] = ix
#
## ALTERNATIVE REDUCED GAME BOARD ##############################################
TRIMMEDNODES = tuple(() if startNode in NODESFORTRIM else
    tuple(stopNode for stopNode in BOARDNODES[startNode]
    if not stopNode in NODESFORTRIM)
    for startNode in range(len(BOARDNODES)))


################################################################################
#### FUNCTIONS #################################################################
def dicerollstomove(distance):
    """Return the expected dice rolls needed to traverse a given distance.
    
    Args:
        distance (float): Number of squares to travel.
    
    Returns:
        float: Expected number of turns; or numpy.inf if ``distance`` < 0
    
    Raises:
        None (Exception-neutral)
    
    The number of turns is the (approximate) expectation of number of throws
    necessary to travel ``distance`` without requiring the movement to end on
    the specific square.
    
    To avoid the expensive (exponential-with-distance) closed-form calculation,
    this function uses a lookup table for short distances and a rather good
    heuristic for long ones. See TODO
    
    """
    if distance > 10:
        return (float(distance)+3.5)/7.
    elif distance >= 0:
        return _DICEROLLSTOMOVE[distance]
    else:
        return np.inf
_DICEROLLSTOMOVE = (0.0,1.0,1.0,
    37./36.,
    1.08333333333333,
    1.16512345679012,
    1.28163580246913,
    1.42817644032921,
    1.60988940329218,
    1.77443415637860,
    1.93233453360767)
dicerollstomove = np.vectorize(dicerollstomove,otypes=[np.float])
#
#### EOF #######################################################################
################################################################################
