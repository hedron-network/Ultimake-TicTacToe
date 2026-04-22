import engine
"""
Engine funcitons:
get_state -> gets a 406 long list of floats representing the current board state,
undo -> undo the last move,
get_legal_moves -> gets all legal moves of a position (0-80),
apply_move -> applies a move ( /!\ no safeguards),
get_winner -> gets the winner (1 for the starting player -1 for the opponent 0 if neither) /!\ do not call if the game isnt finished,
is_done -> returns true if the game is done,
"""
engine_UTTT = engine.Game() 
engine_UTTT.apply_move(55)
print(engine_UTTT.get_legal_moves())
engine_UTTT.apply_move(9)
print(engine_UTTT.get_legal_moves())
engine_UTTT.undo()
print(engine_UTTT.get_legal_moves())
print(engine_UTTT.get_state())