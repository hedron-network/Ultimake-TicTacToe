def debug_engine(game):
    """Run this at the start of a game to verify engine contracts."""
    import engine
    g = engine.Game()
    
    # 1. Check initial current player
    state = g.get_state()
    print(f"Initial current_player = {g.get_current_player()}")  # Must be 1, not -1 or 0
    
    # 2. Check eval() sign convention
    # eval() must return POSITIVE when position is good for current player
    val = g.eval()
    print(f"Eval at start (should be ~0 or slightly positive for first player): {val}")
    
    # 3. After one move, player should switch
    legal = g.get_legal_moves()
    g.apply_move(legal[0])
    state2 = g.get_state()
    print(f"current_player after move = {state2[90]}")  # Must be -1 (or 2), not still 1
    
    # 4. Check eval() flips sign for second player
    val2 = g.eval()
    print(f"Eval after first move (should flip sign if eval is relative): {val2}")
    
    # 5. Undo works
    g.undo()
    state3 = g.get_state()
    print(f"current_player after undo = {state3[90]}")  # Must be back to 1
    
    # 6. Check get_hash() changes after move
    h1 = g.get_hash()
    g.apply_move(legal[0])
    h2 = g.get_hash()
    print(f"Hash changes after move: {h1 != h2}")  # Must be True
    g.undo()
    h3 = g.get_hash()
    print(f"Hash restored after undo: {h1 == h3}")  # Must be True

debug_engine(None)