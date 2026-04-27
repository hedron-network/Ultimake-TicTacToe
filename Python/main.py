import engine
"""
Engine funcitons:
get_state -> gets a 406 long list of floats representing the current board state,
undo -> undo the last move,
get_legal_moves -> gets all legal moves of a position (0-80),
apply_move -> applies a move ( /!\ no safeguards),
get_winner -> gets the winner (1 for the starting player -1 for the opponent 0 if neither) /!\ do not call if the game isnt finished,
is_done -> returns true if the game is done,
eval -> return a float [-1;1] depending on the position
print_board -> prints the board
"""
engine_UTTT = engine.Game() 

print(engine_UTTT.eval())
engine_UTTT.apply_move(0)
engine_UTTT.apply_move(20)
engine_UTTT.apply_move(1)
engine_UTTT.apply_move(40)
engine_UTTT.apply_move(2)
engine_UTTT.apply_move(50)
engine_UTTT.print_board()
print(engine_UTTT.get_legal_moves())
engine_UTTT.apply_move(9)
print(engine_UTTT.eval())
print(engine_UTTT.get_legal_moves())
engine_UTTT.undo()
print(engine_UTTT.get_legal_moves())