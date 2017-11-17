# Simple tetris program! v0.2

"""
#1) This program simulates the tetris game. 
#Formulation of the search problem.

#Initial State: The initial state is the 20x10 blank board configuration.

#Goal State: There is no goal state and the search may never stop. However, there is a stopping state which is when the pieces reach
#the maximum height of the board and there is no space to accommodate the current falling piece as well as the next new piece.

#State Space: The state space will contain all board configurations with the current piece placed as well as the next new piece placed.
#In some special cases where one piece overpowers others(described below) we check the third piece look ahead as well.

#Successor function: The successor function will generate all possible board configurations after placing the current piece
#and the next new piece at all possible row column positions. If the pieces can be rotated, then the board configurations after placing all possible rotations is also generated by the successor function.
#If the number of pieces on the board reach a count of 30, we calculate the piece which has
#the maximum probability and assume this piece to fall after the next piece.
#Evaluation function: The state n is evaluated by the f(n), where f(n)=h(n),where h(n) is the heuristic cost of the state.


#Heuristics used in this problem:
# Reference for initial heuristic: https://codemyroad.wordpress.com/2013/04/14/tetris-ai-the-near-perfect-player/
# We manipulated the weights and added some other ways to generate best possible heuristic by trial and error

# Holes: A hole is an empty space surrounded by 'x' in the board.
# Wedges: A wedge is an empty space which is covered by a 'x' only from the above.
# Aggregate height: The sum of heights of all the columns of the board.
# Maximum height: The maximum height of all the column heights. We use maximum height because we want our board to be as free as possible to accommodate the #falling pieces.
# Complete lines: Complete lines are the best and occur when there are 10 'x' in a row.
# Bumpiness of the board: The sum of absolute differences of heights of adjacent columns.
# If the maxheight of the board becomes greater than 11, we give more importance to bumpiness.
# We also tried many other heuristics like pits which mean the pit in top most layer,
# Blockades which mean the part which forms a hole or a wedge
# after all possible combinations we decided to stay with the upper ones and ignore the ones which dont work


#2) The search is a simple search till depth of 2 or 3(when number of pieces become greater than 30). We use a dictionary with key='set of moves', #value=heuristic value of that state.
# Initially we have a blank board, the current falling piece is placed at all possible row column 
# and a heuristic value is calculated for it and stored in the dictionary. The piece is then rotated and again placed at all possible row column. 
# This is done for all possible rotations of the piece.
# These steps are then performed for the next piece and the third piece(in some cases) as well.
# The set of moves with the maximum dictionary value is selected.

#3) This code may give a bad score if one of the pieces overpowers other pieces i.e suppose we get more number of 'z'than others.
# We are handling this by checking the piece with maximum probability and we assume that that piece will come after the next piece and then we make a third stage look ahead to get the best possible current state.   
# The major problem we faced was getting the weights for different heuristics like holes, max_height, etc. This problem can be solved if we use techniques from reinforcement learning and machine learning to lear the weights automatically after several plays.
# The choice of coefficients in the heuristic equation was made after repeatedly playing and checking which scenarios are the worst and giving weights accordingly.
# We tried checking for the number of pits in the board but there was not much improvement, so we used bumpiness instead.

"""


from AnimatedTetris import *
from SimpleTetris import *
from kbinput import *
from AdversarialTetris import *
import time, sys
import copy
import numpy as np

#The human player.
class HumanPlayer:
    def get_moves(self, tetris):
        print "Type a sequence of moves using: \n  b for move left \n  m for move right \n  n for rotation\nThen press enter. E.g.: bbbnn\n"
        moves = raw_input()
        return moves

    #Implementation of Adversarial Search for returning the next worst piece
    def getNextPiece(self, tetris):
        newTetris=copy.deepcopy(tetris)
        return advplayGame(newTetris)

    def control_game(self, tetris):
        while 1:
            if isinstance(tetris, AdversarialTetris): #check if adversarial
                tetris.next_piece=self.getNextPiece(tetris)
            c = get_char_keyboard()
            commands =  { "b": tetris.left, "n": tetris.rotate, "m": tetris.right, " ": tetris.down }
            commands[c]()

#Implementation of adversarial search
def advplayGame(newTetris):
    rank=[]
    nextRanks=[]
    nextPieces=[]
    boards=[]
    orgCol=newTetris.col
    orgRow=newTetris.row
    rotationCommands= generatePieceStates(newTetris.piece)[0]
    for rotcom in rotationCommands:
        rotCommands=""
        newTetris.piece=newTetris.rotate_piece(newTetris.piece,(0 if rotcom==0 else 90))
        rotCommands=({0:'',90:'n',180:'nn',270:'nnn'}.get(rotcom))
        offset=getOffsetOfLeft(orgCol)
        lengthOfPiece=getLengthOfPiece(newTetris.piece)
        for i in range(0,10-lengthOfPiece+1):
            newTetris.move(offset,newTetris.piece)
            tempboard=keepPiece(newTetris.state[0],newTetris.state[1],newTetris.piece,newTetris.row,newTetris.col)
            rank.append(heuristic(tempboard))
            boards.append(tempboard)
            offset +=1
            i +=1
            newTetris.col=orgCol
            newTetris.row=orgRow
    tempboard=boards[np.argmax(np.asarray(rank))]  #assume player plays the best possible current move so take the max of current state
    for piece in [['xxxx'],['xx ', ' xx'],['x  ','xxx'],['xxx',' x '],['xx', 'xx']]:
        newTetris.next_piece=piece
        nextRanks.append(placeNextPiece(tempboard,newTetris,None))
        nextPieces.append(piece)
    return(nextPieces[np.argmin(np.asarray(nextRanks))])  #return min of max ranks 

# This method calculates the heuristic value for a state.
# Reference for initial heuristic: https://codemyroad.wordpress.com/2013/04/14/tetris-ai-the-near-perfect-player/
def heuristic(boardPassed):
    from collections import defaultdict
    heuristic_value=0
    aggregate_height=0
    board=list(boardPassed)
    board.reverse()
    holes=0
    wedges=0
    col_height=defaultdict(lambda:0)
    for row in range(20):
        for col in range(10):
            try:
                if board[row][col]=='x':
                    col_height[col]=row+1
                elif board[row+1][col]=='x' and board[row][col]==' ':  
                    if board[row][col-1]=='x' and board[row][col+1]=='x':
                        holes+=1
                    elif col==0 and board[row][col+1]=='x': #left corner case
                        holes+=1
                    else:
                        wedges+=1
                elif col==9 and board[row][col]==' ' and board[row-1][col]=='x': #right corner case
                        holes+=1
            except IndexError:
                continue
    maxheight=max(col_height.values())
    aggregate_height=sum(col_height[val] for val in col_height)
    complete_lines=complete_lines=sum(1 for row in board if row.count('x')==10)
    bumpiness=sum(map(lambda i: abs(col_height[i]-col_height[i+1]),range(9)))
    if maxheight<=11: 
        return (-0.4566)*holes+(-0.2)*wedges+(-0.51)*aggregate_height+(-0.2)*maxheight+complete_lines*(0.76)+(-0.1844)*bumpiness
    else: #if height is greater than 11 give more weightage to bumpiness than before
        return (-0.4566)*holes+(-0.2)*wedges+(-0.51)*aggregate_height+(-0.2)*maxheight+complete_lines*(0.76)+(-0.4)*bumpiness
# Check the possible rotations for the piece.
def generatePieceStates(piece):
    if piece in [['xxxx'],['x', 'x', 'x', 'x']]:  #if shape is i 2 rotations possible
        return [0,90],'i'
    elif piece in [['xx ', ' xx'],[' x', 'xx', 'x ']]: ##if shape is z 2 rotations possible
        return [0,90],'z'
    elif piece in [['x  ','xxx'],['xx','x ','x '],['xxx','  x'],[' x',' x','xx']]: #if shape is inverted l 4 rotations possible
        return [0,90,180,270],'l'
    elif piece in [['xxx',' x '],['x ','xx','x '],[' x', 'xx', ' x'],[' x ','xxx']]: ##if shape is t 4 rotataions possible
        return [0,90,180,270],'t'
    elif piece in [['xx', 'xx']]:       #if o no need to rotate
        return [0],'o'

# Returns the length of the piece.
def getLengthOfPiece(piece):
    return max(len(s) for s in piece)

#get number of steps to go left 
def getOffsetOfLeft(col):
    return (0-col)
    
# Returns the {letter:shape} dictionary.
def getShape(shape):
    return {'i':['xxxx'], 'z':['xx ', ' xx'], 't':['x  ','xxx'], 'l':[' x',' x','xx'], 'o':['xx', 'xx']}[shape]

#Third step look ahead called when the number of piece on board reaches 30.
def probabilisticLookAhead(board,newTetris,shape):
    ranks=[]
    shape=getShape(shape)
    rotationCommands=generatePieceStates(shape)[0]
    for rotcom in rotationCommands:
        shape=newTetris.rotate_piece(shape,(0 if rotcom==0 else 90))
        lengthOfPiece=getLengthOfPiece(shape)
        for i in range(0,9-lengthOfPiece):
            tempboard=board
            row=0
            tempboard=keepPiece(tempboard,0,shape,row,i)
            r=heuristic(tempboard)
            ranks.append(r)
    return max(ranks)

# return max of rank after placing next piece
def placeNextPiece(board,newTetris,countDict):
    ranks=[]
    rotationCommands=generatePieceStates(newTetris.next_piece)[0]
    for rotcom in rotationCommands:
        newTetris.next_piece=newTetris.rotate_piece(newTetris.next_piece,(0 if rotcom==0 else 90))
        lengthOfPiece=getLengthOfPiece(newTetris.next_piece)
        for i in range(0,10-lengthOfPiece+1):
            tempboard=board
            row=0
            tempboard=keepPiece(tempboard,0,newTetris.next_piece,row,i)
            if countDict!=None:
                shape,prob=getMaxProb(countDict)
                if sum(countDict.itervalues())>30 and prob>=0.65:
                    r=probabilisticLookAhead(tempboard,newTetris,shape)
                else:
                    r=heuristic(tempboard)
            else:
                r=heuristic(tempboard)
            ranks.append(r)
    return max(ranks)

# Return the piece with maximum probability.
def getMaxProb(countDict):
    probDict=copy.deepcopy(countDict)
    total=sum(probDict.itervalues())
    for key in probDict.keys():
        probDict[key]=probDict[key]/float(total)
    return (max(probDict,key=probDict.get),max(probDict.values()))
 
# Check for collisions. 
def keepPiece(board,score,piece,row,col):
    while not TetrisGame.check_collision((board,score),piece,row+1,col):
        row += 1
    return TetrisGame.place_piece((board,score),piece,row,col)[0]

# Return the best move.
def playGame(newTetris):
    commands={}
    orgCol=newTetris.col
    orgRow=newTetris.row
    countDict[generatePieceStates(newTetris.next_piece)[1]]+=1   #get count of pieces  
    rotationCommands= generatePieceStates(newTetris.piece)[0]
    for rotcom in rotationCommands:
        rotCommands=""
        newTetris.piece=newTetris.rotate_piece(newTetris.piece,(0 if rotcom==0 else 90))
        rotCommands=({0:'',90:'n',180:'nn',270:'nnn'}.get(rotcom))
        offset=getOffsetOfLeft(orgCol)
        lengthOfPiece=getLengthOfPiece(newTetris.piece)
        for i in range(0,10-lengthOfPiece+1):
            newTetris.move(offset,newTetris.piece)
            tempboard=keepPiece(newTetris.state[0],newTetris.state[1],newTetris.piece,newTetris.row+1,newTetris.col)
            commandList=rotCommands+('b'*abs(offset) if offset<0 else 'm'*offset)
            rank=placeNextPiece(tempboard,newTetris,countDict) #
            commands[commandList]=rank
            offset +=1
            i +=1
            newTetris.col=orgCol
            newTetris.row=orgRow
    return max(commands,key=commands.get) #return the commands for max rank


countDict={'i':0,'z':0,'t':0,'l':0,'o':0}
#The computer player.
class ComputerPlayer:
    # This function generates a series of commands to move the piece into the "optimal"
    # position. The commands are a string of letters, where b and m represent left and right, respectively,
    # and n rotates. tetris is an object that lets you inspect the board, e.g.:
    #   - tetris.col, tetris.row have the current column and row of the upper-left corner of the 
    #     falling piece
    #   - tetris.get_piece() is the current piece, tetris.get_next_piece() is the next piece after that
    #   - tetris.left(), tetris.right(), tetris.down(), and tetris.rotate() can be called to actually
    #     issue game commands
    #   - tetris.get_board() returns the current state of the board, as a list of strings.
    #
    def get_moves(self, tetris):
        newTetris=copy.deepcopy(tetris)
        return playGame(newTetris)

    # This is the version that's used by the animted version. This is really similar to get_moves,
    # except that it runs as a separate thread and you should access various methods and data in
    # the "tetris" object to control the movement. In particular:
    #   - tetris.col, tetris.row have the current column and row of the upper-left corner of the 
    #     falling piece
    #   - tetris.get_piece() is the current piece, tetris.get_next_piece() is the next piece after that
    #   - tetris.left(), tetris.right(), tetris.down(), and tetris.rotate() can be called to actually
    #     issue game commands
    #   - tetris.get_board() returns the current state of the board, as a list of strings.
    #
    def control_game(self, tetris):
        time.sleep(0.1)
        COMMANDS = { "b": tetris.left, "n": tetris.rotate, "m": tetris.right }
        while 1:
            moves = self.get_moves(tetris)
            for c in moves:
                if c in COMMANDS:
                    COMMANDS[c]()
            tetris.down()    

(player_opt, interface_opt) = sys.argv[1:3]
try:
    advrs=sys.argv[3]    
except IndexError:
    advrs=None
  

try:
    if player_opt == "human":
        player = HumanPlayer()
    elif player_opt == "computer":
        player = ComputerPlayer()
    else:
        print "unknown player!"
        exit(1)
    if advrs=="adversarial":  #added new option
        tetris=AdversarialTetris()
    elif interface_opt == "simple" and advrs==None:
        tetris = SimpleTetris()
    elif interface_opt == "animated" and advrs==None:
        tetris = AnimatedTetris()
    else:
        print "unknown interface!"
        exit(1)
    if (player_opt=="computer" and advrs=="adversarial") or(advrs=="adversarial" and interface_opt=="simple") :
        print "Adversarial option is only for human player and animated option"
        exit(1)
    else:
        tetris.start_game(player)
except EndOfGame as s:
    print "\n\n\n", s
