import copy
from typing import List, Dict, Tuple, Optional, Set

class ChessPiece:
    def __init__(self, piece_type: str, color: str):
        self.piece_type = piece_type
        self.color = color
        self.has_moved = False
    
    def __str__(self):
        symbols = {
            'white': {'pawn': '♙', 'rook': '♖', 'knight': '♘', 'bishop': '♗', 'queen': '♕', 'king': '♔'},
            'black': {'pawn': '♟', 'rook': '♜', 'knight': '♞', 'bishop': '♝', 'queen': '♛', 'king': '♚'}
        }
        return symbols[self.color][self.piece_type]
    
    def to_dict(self):
        return {
            'piece_type': self.piece_type,
            'color': self.color,
            'has_moved': self.has_moved
        }
    
    @classmethod
    def from_dict(cls, data):
        piece = cls(data['piece_type'], data['color'])
        piece.has_moved = data['has_moved']
        return piece

class ChessGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_player = 'white'
        self.move_history = []
        self.captured_pieces = {'white': [], 'black': []}
        self.king_positions = {'white': (7, 4), 'black': (0, 4)}
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.game_over = False
        self.result = None
        self.check_status = {'white': False, 'black': False}
    
    def initialize_board(self) -> List[List[Optional[ChessPiece]]]:         
        board = [[None for _ in range(8)] for _ in range(8)]
        
        # Black pieces (top of board)
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        for col, piece_type in enumerate(piece_order):
            board[0][col] = ChessPiece(piece_type, 'black')
        for col in range(8):
            board[1][col] = ChessPiece('pawn', 'black')
        
        # White pieces (bottom of board)
        for col, piece_type in enumerate(piece_order):
            board[7][col] = ChessPiece(piece_type, 'white')
        for col in range(8):
            board[6][col] = ChessPiece('pawn', 'white')
        
        return board
    
    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_piece_at(self, row: int, col: int) -> Optional[ChessPiece]:
        if self.is_valid_position(row, col):
            return self.board[row][col]
        return None
    
    def get_possible_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.get_piece_at(row, col)
        if not piece or piece.color != self.current_player:
            return []
        
        moves = []
        
        if piece.piece_type == 'pawn':
            moves = self.get_pawn_moves(row, col)
        elif piece.piece_type == 'rook':
            moves = self.get_rook_moves(row, col)
        elif piece.piece_type == 'knight':
            moves = self.get_knight_moves(row, col)
        elif piece.piece_type == 'bishop':
            moves = self.get_bishop_moves(row, col)
        elif piece.piece_type == 'queen':
            moves = self.get_queen_moves(row, col)
        elif piece.piece_type == 'king':
            moves = self.get_king_moves(row, col)

        valid_moves = []
        for to_row, to_col in moves:
            if self.is_move_legal(row, col, to_row, to_col):
                valid_moves.append((to_row, to_col))
        
        return valid_moves
    
    def get_pawn_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.get_piece_at(row, col)
        moves = []
        direction = -1 if piece.color == 'white' else 1
        start_row = 6 if piece.color == 'white' else 1

        new_row = row + direction
        if self.is_valid_position(new_row, col) and not self.get_piece_at(new_row, col):
            moves.append((new_row, col))

            if row == start_row:
                new_row = row + 2 * direction
                if self.is_valid_position(new_row, col) and not self.get_piece_at(new_row, col):
                    moves.append((new_row, col))

        for dc in [-1, 1]:
            new_row, new_col = row + direction, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.get_piece_at(new_row, new_col)
                if target and target.color != piece.color:
                    moves.append((new_row, new_col))

                elif self.en_passant_target == (new_row, new_col):
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_rook_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        return self.get_line_moves(row, col, [(0, 1), (0, -1), (1, 0), (-1, 0)])
    
    def get_bishop_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        return self.get_line_moves(row, col, [(1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    def get_queen_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        return self.get_line_moves(row, col, [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    def get_line_moves(self, row: int, col: int, directions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        piece = self.get_piece_at(row, col)
        moves = []
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            while self.is_valid_position(new_row, new_col):
                target = self.get_piece_at(new_row, new_col)
                if not target:
                    moves.append((new_row, new_col))
                elif target.color != piece.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
                new_row, new_col = new_row + dr, new_col + dc
        
        return moves
    
    def get_knight_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.get_piece_at(row, col)
        moves = []
        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.get_piece_at(new_row, new_col)
                if not target or target.color != piece.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def get_king_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        piece = self.get_piece_at(row, col)
        moves = []
        
        # Regular king moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if self.is_valid_position(new_row, new_col):
                    target = self.get_piece_at(new_row, new_col)
                    if not target or target.color != piece.color:
                        moves.append((new_row, new_col))
        
        # Castling
        if not piece.has_moved and not self.is_in_check(piece.color):
            # Kingside castling
            if (self.get_piece_at(row, 7) and 
                self.get_piece_at(row, 7).piece_type == 'rook' and 
                not self.get_piece_at(row, 7).has_moved and
                not self.get_piece_at(row, 5) and 
                not self.get_piece_at(row, 6) and
                not self.is_square_attacked(row, 5, piece.color) and
                not self.is_square_attacked(row, 6, piece.color)):
                moves.append((row, 6))
            
            # Queenside castling
            if (self.get_piece_at(row, 0) and 
                self.get_piece_at(row, 0).piece_type == 'rook' and 
                not self.get_piece_at(row, 0).has_moved and
                not self.get_piece_at(row, 1) and 
                not self.get_piece_at(row, 2) and 
                not self.get_piece_at(row, 3) and
                not self.is_square_attacked(row, 2, piece.color) and
                not self.is_square_attacked(row, 3, piece.color)):
                moves.append((row, 2))
        
        return moves
    
    def is_square_attacked(self, row: int, col: int, by_color: str) -> bool:
        """Check if a square is attacked by pieces of given color"""
        opponent_color = 'black' if by_color == 'white' else 'white'
        
        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r, c)
                if piece and piece.color == opponent_color:
                    if piece.piece_type == 'pawn':
                        # Pawn attacks diagonally
                        direction = 1 if piece.color == 'black' else -1
                        if (r + direction == row and abs(c - col) == 1):
                            return True
                    elif piece.piece_type == 'king':
                        # King attacks adjacent squares
                        if abs(r - row) <= 1 and abs(c - col) <= 1 and not (r == row and c == col):
                            return True
                    else:
                        # Other pieces
                        temp_current = self.current_player
                        self.current_player = opponent_color
                        if piece.piece_type == 'knight':
                            moves = self.get_knight_moves(r, c)
                        elif piece.piece_type == 'rook':
                            moves = self.get_rook_moves(r, c)
                        elif piece.piece_type == 'bishop':
                            moves = self.get_bishop_moves(r, c)
                        elif piece.piece_type == 'queen':
                            moves = self.get_queen_moves(r, c)
                        else:
                            moves = []
                        self.current_player = temp_current
                        
                        if (row, col) in moves:
                            return True
        
        return False
    
    def is_in_check(self, color: str) -> bool:
        """Check if king of given color is in check"""
        king_pos = self.king_positions[color]
        return self.is_square_attacked(king_pos[0], king_pos[1], color)
    
    def is_move_legal(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if move is legal (doesn't put own king in check)"""

        piece = self.get_piece_at(from_row, from_col)
        target = self.get_piece_at(to_row, to_col)
        
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

        if piece.piece_type == 'king':
            old_king_pos = self.king_positions[piece.color]
            self.king_positions[piece.color] = (to_row, to_col)

        legal = not self.is_in_check(piece.color)

        self.board[from_row][from_col] = piece
        self.board[to_row][to_col] = target

        if piece.piece_type == 'king':
            self.king_positions[piece.color] = old_king_pos
        
        return legal
    
    def make_move(self, from_pos: str, to_pos: str, promotion: str = None) -> bool:
        """Make a move on the board"""
        try:
            from_row, from_col = 8 - int(from_pos[1]), ord(from_pos[0]) - ord('a')
            to_row, to_col = 8 - int(to_pos[1]), ord(to_pos[0]) - ord('a')
        except (ValueError, IndexError):
            return False
        
        piece = self.get_piece_at(from_row, from_col)
        if not piece or piece.color != self.current_player:
            return False

        possible_moves = self.get_possible_moves(from_row, from_col)
        if (to_row, to_col) not in possible_moves:
            return False

        move_notation = self.get_move_notation(from_row, from_col, to_row, to_col, promotion)

        captured_piece = self.get_piece_at(to_row, to_col)

        if (piece.piece_type == 'pawn' and 
            self.en_passant_target == (to_row, to_col) and 
            not captured_piece):

            captured_row = to_row + (1 if piece.color == 'white' else -1)
            captured_piece = self.get_piece_at(captured_row, to_col)
            self.board[captured_row][to_col] = None
            if captured_piece:
                self.captured_pieces[captured_piece.color].append(captured_piece)
        

        if piece.piece_type == 'king' and abs(to_col - from_col) == 2:
            if to_col == 6:
                rook = self.get_piece_at(from_row, 7)
                self.board[from_row][7] = None
                self.board[from_row][5] = rook
                rook.has_moved = True
            else:
                rook = self.get_piece_at(from_row, 0)
                self.board[from_row][0] = None
                self.board[from_row][3] = rook
                rook.has_moved = True
        

        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.has_moved = True
        

        if captured_piece:
            self.captured_pieces[captured_piece.color].append(captured_piece)
            self.halfmove_clock = 0
        elif piece.piece_type == 'pawn':
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if piece.piece_type == 'king':
            self.king_positions[piece.color] = (to_row, to_col)

        if (piece.piece_type == 'pawn' and 
            ((piece.color == 'white' and to_row == 0) or 
             (piece.color == 'black' and to_row == 7))):
            promotion = promotion or 'queen'
            self.board[to_row][to_col] = ChessPiece(promotion, piece.color)
            self.board[to_row][to_col].has_moved = True

        if (piece.piece_type == 'pawn' and abs(to_row - from_row) == 2):
            self.en_passant_target = ((from_row + to_row) // 2, to_col)
        else:
            self.en_passant_target = None

        self.move_history.append({
            'from': from_pos,
            'to': to_pos,
            'piece': piece.piece_type,
            'color': piece.color,
            'captured': captured_piece.piece_type if captured_piece else None,
            'promotion': promotion,
            'notation': move_notation
        })
        
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        if self.current_player == 'white':
            self.fullmove_number += 1

        self.check_status['white'] = self.is_in_check('white')
        self.check_status['black'] = self.is_in_check('black')

        self.check_game_end()
        
        return True
    
    def get_move_notation(self, from_row: int, from_col: int, to_row: int, to_col: int, promotion: str = None) -> str:
        """Get algebraic notation for move"""
        piece = self.get_piece_at(from_row, from_col)
        target = self.get_piece_at(to_row, to_col)
        
        notation = ""

        if piece.piece_type != 'pawn':
            notation += piece.piece_type[0].upper()

        if target or (piece.piece_type == 'pawn' and self.en_passant_target == (to_row, to_col)):
            if piece.piece_type == 'pawn':
                notation += chr(ord('a') + from_col)
            notation += 'x'

        notation += chr(ord('a') + to_col) + str(8 - to_row)

        if promotion:
            notation += '=' + promotion[0].upper()
        
        return notation
    
    def check_game_end(self):
        has_legal_moves = False
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at(row, col)
                if piece and piece.color == self.current_player:
                    if self.get_possible_moves(row, col):
                        has_legal_moves = True
                        break
            if has_legal_moves:
                break
        
        if not has_legal_moves:
            if self.is_in_check(self.current_player):
                self.game_over = True
                self.result = 'white_wins' if self.current_player == 'black' else 'black_wins'
            else:
                self.game_over = True
                self.result = 'draw'

        elif self.halfmove_clock >= 100:
            self.game_over = True
            self.result = 'draw'
        
        elif self.is_insufficient_material():
            self.game_over = True
            self.result = 'draw'
    
    def is_insufficient_material(self) -> bool:
        pieces = {'white': [], 'black': []}
        
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at(row, col)
                if piece:
                    pieces[piece.color].append(piece.piece_type)
        

        if all(len(pieces[color]) == 1 for color in pieces):
            return True
        

        for color in pieces:
            other_color = 'black' if color == 'white' else 'white'
            if (len(pieces[color]) == 2 and len(pieces[other_color]) == 1 and
                any(p in pieces[color] for p in ['bishop', 'knight'])):
                return True
        
        return False
    
    def is_game_over(self) -> bool:
        return self.game_over
    
    def get_result(self) -> str:
        return self.result
    
    def to_dict(self) -> Dict:
        board_dict = []
        for row in self.board:
            row_dict = []
            for piece in row:
                row_dict.append(piece.to_dict() if piece else None)
            board_dict.append(row_dict)
        
        return {
            'board': board_dict,
            'current_player': self.current_player,
            'move_history': self.move_history,
            'captured_pieces': {
                color: [piece.to_dict() for piece in pieces] 
                for color, pieces in self.captured_pieces.items()
            },
            'king_positions': self.king_positions,
            'en_passant_target': self.en_passant_target,
            'halfmove_clock': self.halfmove_clock,
            'fullmove_number': self.fullmove_number,
            'game_over': self.game_over,
            'result': self.result,
            'check_status': self.check_status
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        game = cls()
        
        for row_idx, row_data in enumerate(data['board']):
            for col_idx, piece_data in enumerate(row_data):
                if piece_data:
                    game.board[row_idx][col_idx] = ChessPiece.from_dict(piece_data)
                else:
                    game.board[row_idx][col_idx] = None

        game.current_player = data['current_player']
        game.move_history = data['move_history']
        game.captured_pieces = {
            color: [ChessPiece.from_dict(piece_data) for piece_data in pieces]
            for color, pieces in data['captured_pieces'].items()
        }
        game.king_positions = {
            color: tuple(pos) if isinstance(pos, list) else pos 
            for color, pos in data['king_positions'].items()
        }
        en_passant = data.get('en_passant_target')
        game.en_passant_target = tuple(en_passant) if isinstance(en_passant, list) else en_passant
        game.halfmove_clock = data.get('halfmove_clock', 0)
        game.fullmove_number = data.get('fullmove_number', 1)
        game.game_over = data.get('game_over', False)
        game.result = data.get('result')
        game.check_status = data.get('check_status', {'white': False, 'black': False})
        
        return game 