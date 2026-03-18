import random
import time
from typing import Dict, List, Tuple, Optional
from chess_engine import ChessGame, ChessPiece

class AIPlayer:
    def __init__(self, difficulty: str = 'medium'):
        self.difficulty = difficulty
        self.depth_map = {
            'easy': 2,
            'medium': 3,
            'hard': 3,  # Reduced from 4 for better performance
            'expert': 4  # Reduced from 5 for better performance
        }
        self.depth = self.depth_map.get(difficulty, 3)

        # Move caching for performance
        self.move_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Piece values
        self.piece_values = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
        
        # Position evaluation tables
        self.pawn_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ]
        
        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]
        
        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]
        
        self.rook_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ]
        
        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]
        
        self.king_middle_game = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
        
        self.king_end_game = [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]
    
    def get_move(self, game: ChessGame) -> Optional[Dict]:
        """Get the best move for the AI"""
        if self.difficulty == 'easy':
            return self.get_random_move(game)
        
        best_move = self.minimax_root(game)
        return best_move
    
    def get_random_move(self, game: ChessGame) -> Optional[Dict]:
        """Get a random legal move (easy difficulty)"""
        all_moves = []
        
        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece and piece.color == game.current_player:
                    moves = game.get_possible_moves(row, col)
                    for to_row, to_col in moves:
                        from_pos = chr(col + ord('a')) + str(8 - row)
                        to_pos = chr(to_col + ord('a')) + str(8 - to_row)
                        all_moves.append({
                            'from': from_pos,
                            'to': to_pos,
                            'from_row': row,
                            'from_col': col,
                            'to_row': to_row,
                            'to_col': to_col
                        })
        
        if all_moves:
            return random.choice(all_moves)
        return None
    
    def minimax_root(self, game: ChessGame) -> Optional[Dict]:
        """Minimax algorithm entry point"""
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        all_moves = self.get_all_moves(game)
        
        # Sort moves for better alpha-beta pruning
        all_moves = self.order_moves(game, all_moves)
        
        for move in all_moves:
            # Make move
            game_copy = self.copy_game(game)
            if game_copy.make_move(move['from'], move['to']):
                value = self.minimax(game_copy, self.depth - 1, alpha, beta, False)
                
                if value > best_value:
                    best_value = value
                    best_move = move
                
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
        
        return best_move
    
    def minimax(self, game: ChessGame, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0 or game.is_game_over():
            return self.evaluate_position(game)
        
        if maximizing:
            max_eval = float('-inf')
            moves = self.get_all_moves(game)
            moves = self.order_moves(game, moves)
            
            for move in moves:
                game_copy = self.copy_game(game)
                if game_copy.make_move(move['from'], move['to']):
                    eval_score = self.minimax(game_copy, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            
            return max_eval
        else:
            min_eval = float('inf')
            moves = self.get_all_moves(game)
            moves = self.order_moves(game, moves)
            
            for move in moves:
                game_copy = self.copy_game(game)
                if game_copy.make_move(move['from'], move['to']):
                    eval_score = self.minimax(game_copy, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            
            return min_eval
    
    def get_all_moves(self, game: ChessGame) -> List[Dict]:
        """Get all possible moves for current player (with caching)"""
        # Create cache key based on current player and board state
        cache_key = (game.current_player, str(game.board))

        # Check cache first
        if cache_key in self.move_cache:
            self.cache_hits += 1
            return self.move_cache[cache_key]

        self.cache_misses += 1
        all_moves = []

        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece and piece.color == game.current_player:
                    moves = game.get_possible_moves(row, col)
                    for to_row, to_col in moves:
                        from_pos = chr(col + ord('a')) + str(8 - row)
                        to_pos = chr(to_col + ord('a')) + str(8 - to_row)
                        all_moves.append({
                            'from': from_pos,
                            'to': to_pos,
                            'from_row': row,
                            'from_col': col,
                            'to_row': to_row,
                            'to_col': to_col
                        })

        # Cache the result (limit cache size to prevent memory issues)
        if len(self.move_cache) < 1000:
            self.move_cache[cache_key] = all_moves

        return all_moves
    
    def order_moves(self, game: ChessGame, moves: List[Dict]) -> List[Dict]:
        """Order moves for better alpha-beta pruning"""
        def move_priority(move):
            score = 0
            
            # Prioritize captures
            target = game.get_piece_at(move['to_row'], move['to_col'])
            if target:
                # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                piece = game.get_piece_at(move['from_row'], move['from_col'])
                score += self.piece_values[target.piece_type] - self.piece_values[piece.piece_type] // 10
            
            # Prioritize center control
            center_distance = abs(move['to_row'] - 3.5) + abs(move['to_col'] - 3.5)
            score += (7 - center_distance) * 10
            
            return score
        
        return sorted(moves, key=move_priority, reverse=True)
    
    def evaluate_position(self, game: ChessGame) -> float:
        """Evaluate the current position"""
        if game.is_game_over():
            result = game.get_result()
            if result == 'black_wins':  # AI wins
                return 10000
            elif result == 'white_wins':  # AI loses
                return -10000
            else:  # Draw
                return 0
        
        score = 0
        
        # Material count and position evaluation
        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece:
                    piece_value = self.get_piece_value(piece, row, col, game)
                    if piece.color == 'black':  # AI color
                        score += piece_value
                    else:
                        score -= piece_value
        
        # Additional positional factors
        score += self.evaluate_king_safety(game, 'black') - self.evaluate_king_safety(game, 'white')
        score += self.evaluate_pawn_structure(game, 'black') - self.evaluate_pawn_structure(game, 'white')
        score += self.evaluate_piece_mobility(game, 'black') - self.evaluate_piece_mobility(game, 'white')
        
        # Check and checkmate threats
        if game.check_status['white']:
            score += 50
        if game.check_status['black']:
            score -= 50
        
        return score
    
    def get_piece_value(self, piece: ChessPiece, row: int, col: int, game: ChessGame) -> float:
        """Get piece value including positional bonus"""
        base_value = self.piece_values[piece.piece_type]
        
        # Position tables (flip for black pieces)
        if piece.color == 'black':
            position_row = 7 - row
        else:
            position_row = row
        
        position_bonus = 0
        
        if piece.piece_type == 'pawn':
            position_bonus = self.pawn_table[position_row][col]
        elif piece.piece_type == 'knight':
            position_bonus = self.knight_table[position_row][col]
        elif piece.piece_type == 'bishop':
            position_bonus = self.bishop_table[position_row][col]
        elif piece.piece_type == 'rook':
            position_bonus = self.rook_table[position_row][col]
        elif piece.piece_type == 'queen':
            position_bonus = self.queen_table[position_row][col]
        elif piece.piece_type == 'king':
            # Use different table for endgame
            if self.is_endgame(game):
                position_bonus = self.king_end_game[position_row][col]
            else:
                position_bonus = self.king_middle_game[position_row][col]
        
        return base_value + position_bonus
    
    def is_endgame(self, game: ChessGame) -> bool:
        """Check if position is in endgame"""
        piece_count = 0
        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece and piece.piece_type not in ['king', 'pawn']:
                    piece_count += 1
        
        return piece_count <= 6
    
    def evaluate_king_safety(self, game: ChessGame, color: str) -> float:
        """Evaluate king safety"""
        king_pos = game.king_positions[color]
        safety_score = 0
        
        # Check squares around king
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                check_row, check_col = king_pos[0] + dr, king_pos[1] + dc
                if game.is_valid_position(check_row, check_col):
                    piece = game.get_piece_at(check_row, check_col)
                    if piece and piece.color == color:
                        safety_score += 10  # Friendly piece protection
        
        return safety_score
    
    def evaluate_pawn_structure(self, game: ChessGame, color: str) -> float:
        """Evaluate pawn structure"""
        structure_score = 0
        pawn_files = [False] * 8
        
        # Find pawns
        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece and piece.piece_type == 'pawn' and piece.color == color:
                    pawn_files[col] = True
                    
                    # Passed pawn bonus
                    if self.is_passed_pawn(game, row, col, color):
                        structure_score += 20
                    
                    # Doubled pawn penalty
                    for check_row in range(8):
                        if check_row != row:
                            check_piece = game.get_piece_at(check_row, col)
                            if (check_piece and check_piece.piece_type == 'pawn' 
                                and check_piece.color == color):
                                structure_score -= 10
                                break
        
        # Isolated pawn penalty
        for col in range(8):
            if pawn_files[col]:
                isolated = True
                if col > 0 and pawn_files[col - 1]:
                    isolated = False
                if col < 7 and pawn_files[col + 1]:
                    isolated = False
                
                if isolated:
                    structure_score -= 15
        
        return structure_score
    
    def is_passed_pawn(self, game: ChessGame, row: int, col: int, color: str) -> bool:
        """Check if pawn is passed"""
        direction = -1 if color == 'white' else 1
        opponent_color = 'black' if color == 'white' else 'white'
        
        # Check if any opponent pawns can stop this pawn
        for check_row in range(row + direction, 8 if direction > 0 else -1, direction):
            for check_col in [col - 1, col, col + 1]:
                if game.is_valid_position(check_row, check_col):
                    piece = game.get_piece_at(check_row, check_col)
                    if (piece and piece.piece_type == 'pawn' 
                        and piece.color == opponent_color):
                        return False
        
        return True
    
    def evaluate_piece_mobility(self, game: ChessGame, color: str) -> float:
        """Evaluate piece mobility"""
        mobility_score = 0
        
        for row in range(8):
            for col in range(8):
                piece = game.get_piece_at(row, col)
                if piece and piece.color == color and piece.piece_type != 'king':
                    moves = len(game.get_possible_moves(row, col))
                    mobility_score += moves * 2
        
        return mobility_score
    
    def copy_game(self, game: ChessGame) -> ChessGame:
        """Create a deep copy of the game state (optimized version)"""
        # Create new game instance
        new_game = ChessGame()

        # Copy board state more efficiently
        new_game.board = [[piece for piece in row] for row in game.board]

        # Copy other attributes
        new_game.current_player = game.current_player
        new_game.move_history = game.move_history.copy()
        new_game.captured_pieces = {
            color: pieces.copy() for color, pieces in game.captured_pieces.items()
        }
        new_game.king_positions = game.king_positions.copy()
        new_game.en_passant_target = game.en_passant_target
        new_game.halfmove_clock = game.halfmove_clock
        new_game.fullmove_number = game.fullmove_number
        new_game.game_over = game.game_over
        new_game.result = game.result
        new_game.check_status = game.check_status.copy()

        return new_game

    def clear_cache(self):
        """Clear the move cache to free memory"""
        self.move_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        return {
            'cache_size': len(self.move_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }
