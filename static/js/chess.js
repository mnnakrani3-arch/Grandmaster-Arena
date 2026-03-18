class ChessGame {
    constructor() {
        this.socket = null;
        this.gameId = null;
        this.gameState = null;
        this.selectedSquare = null;
        this.possibleMoves = [];
        this.playerColor = 'white';
        this.isMyTurn = false;
        this.gameMode = null;
        
        this.initializeGame();
        this.setupEventListeners();
    }

    initializeGame() {
        this.socket = io();
        
        this.gameId = window.gameId || null;
        this.gameMode = window.gameMode || null;
        
        if (this.gameId) {
            this.joinGame(this.gameId);
        }
        
        this.setupSocketEvents();
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.showNotification('Connected to game server', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.showNotification('Disconnected from server', 'warning');
        });

        this.socket.on('game_state', (gameState) => {
            this.gameState = gameState;
            this.updateBoard();
            this.updateGameInfo();
            this.checkGameStatus();
        });

        this.socket.on('game_over', (data) => {
            this.handleGameOver(data.result, data.reason);
        });

        this.socket.on('error', (data) => {
            this.showNotification(data.message, 'error');
        });

        this.socket.on('draw_offer', (data) => {
            this.handleDrawOffer(data);
        });

        this.socket.on('draw_declined', (data) => {
            this.showNotification('Draw offer was declined', 'warning');
        });
    }

    joinGame(gameId) {
        this.socket.emit('join_game', { game_id: gameId });
    }

    setupEventListeners() {
        // Board click events
        document.addEventListener('click', (e) => {
            if (e.target.closest('.chess-square')) {
                const square = e.target.closest('.chess-square');
                this.handleSquareClick(square);
            }
        });

        // Promotion modal events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('promotion-choice')) {
                this.handlePromotion(e.target.dataset.piece);
            }
        });

        // Window events
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.disconnect();
            }
        });
    }

    createBoard() {
        const boardElement = document.getElementById('chess-board');
        if (!boardElement) return;

        boardElement.innerHTML = '';
        
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = `chess-square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
                square.dataset.row = row;
                square.dataset.col = col;
                square.dataset.position = this.getPositionNotation(row, col);
                
                boardElement.appendChild(square);
            }
        }
    }

    updateBoard() {
        if (!this.gameState || !this.gameState.board) return;

        const boardElement = document.getElementById('chess-board');
        if (!boardElement) {
            this.createBoard();
            return;
        }

        document.querySelectorAll('.chess-piece').forEach(piece => piece.remove());

        document.querySelectorAll('.chess-square').forEach(square => {
            square.classList.remove('selected', 'possible-move', 'in-check');
        });

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = this.gameState.board[row][col];
                if (piece) {
                    this.placePiece(row, col, piece);
                }
            }
        }

        this.isMyTurn = this.gameState.current_player === this.playerColor;
        this.updateTurnIndicator();

        if (this.gameState.check_status) {
            this.highlightCheck();
        }
    }

    placePiece(row, col, piece) {
        const square = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (!square) return;

        const pieceElement = document.createElement('div');
        pieceElement.className = 'chess-piece';
        pieceElement.dataset.piece = piece.piece_type;
        pieceElement.dataset.color = piece.color;
        pieceElement.textContent = this.getPieceSymbol(piece);
        
        square.appendChild(pieceElement);
    }

    getPieceSymbol(piece) {
        const symbols = {
            white: {
                king: '♔', queen: '♕', rook: '♖',
                bishop: '♗', knight: '♘', pawn: '♙'
            },
            black: {
                king: '♚', queen: '♛', rook: '♜',
                bishop: '♝', knight: '♞', pawn: '♟'
            }
        };
        return symbols[piece.color][piece.piece_type];
    }

    getPositionNotation(row, col) {
        return String.fromCharCode(97 + col) + (8 - row);
    }

    handleSquareClick(square) {
        if (!this.isMyTurn || !this.gameState) return;

        const row = parseInt(square.dataset.row);
        const col = parseInt(square.dataset.col);
        const position = square.dataset.position;

        if (this.possibleMoves.includes(position)) {
            this.makeMove(this.selectedSquare, position);
            this.clearSelection();
            return;
        }

        if (this.selectedSquare === position) {
            this.clearSelection();
            return;
        }

        const piece = this.gameState.board[row][col];
        if (piece && piece.color === this.gameState.current_player) {
            this.selectSquare(position);
            this.getPossibleMoves(position);
        } else {
            this.clearSelection();
        }
    }

    selectSquare(position) {
        this.clearSelection();
        this.selectedSquare = position;
        
        const square = document.querySelector(`[data-position="${position}"]`);
        if (square) {
            square.classList.add('selected');
        }
    }

    clearSelection() {
        this.selectedSquare = null;
        this.possibleMoves = [];
        
        document.querySelectorAll('.chess-square').forEach(square => {
            square.classList.remove('selected', 'possible-move');
        });
    }

    getPossibleMoves(position) {
        this.fetchPossibleMoves(position);
    }

    async fetchPossibleMoves(position) {
        try {
            const response = await fetch('/api/possible-moves', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    game_id: this.gameId,
                    position: position
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.possibleMoves = data.moves || [];
                this.highlightPossibleMoves();
            }
        } catch (error) {
            console.error('Error fetching possible moves:', error);
        }
    }

    highlightPossibleMoves() {
        this.possibleMoves.forEach(position => {
            const square = document.querySelector(`[data-position="${position}"]`);
            if (square) {
                square.classList.add('possible-move');
            }
        });
    }

    makeMove(from, to) {
        const move = { from, to };
        
        // Check for pawn promotion
        if (this.needsPromotion(from, to)) {
            this.showPromotionModal(from, to);
            return;
        }

        this.sendMove(move);
    }

    sendMove(move) {
        if (this.socket && this.gameId) {
            this.socket.emit('make_move', {
                game_id: this.gameId,
                move: move
            });
        }
    }

    needsPromotion(from, to) {
        const fromSquare = document.querySelector(`[data-position="${from}"]`);
        const piece = fromSquare?.querySelector('.chess-piece');
        
        if (!piece || piece.dataset.piece !== 'pawn') return false;
        
        const toRow = 8 - parseInt(to[1]);
        const color = piece.dataset.color;
        
        return (color === 'white' && toRow === 0) || (color === 'black' && toRow === 7);
    }

    showPromotionModal(from, to) {
        const modal = document.getElementById('promotion-modal');
        if (!modal) {
            this.createPromotionModal();
        }
        
        this.pendingPromotion = { from, to };
        document.getElementById('promotion-modal').classList.add('active');
    }

    createPromotionModal() {
        const modal = document.createElement('div');
        modal.id = 'promotion-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Choose Promotion Piece</h3>
                <div class="promotion-choices">
                    <div class="promotion-choice" data-piece="queen">♕ Queen</div>
                    <div class="promotion-choice" data-piece="rook">♖ Rook</div>
                    <div class="promotion-choice" data-piece="bishop">♗ Bishop</div>
                    <div class="promotion-choice" data-piece="knight">♘ Knight</div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    handlePromotion(piece) {
        if (this.pendingPromotion) {
            const move = {
                from: this.pendingPromotion.from,
                to: this.pendingPromotion.to,
                promotion: piece
            };
            this.sendMove(move);
            this.pendingPromotion = null;
        }
        
        document.getElementById('promotion-modal').classList.remove('active');
    }

    updateGameInfo() {
        if (!this.gameState) return;

        // Update current player indicator
        const currentPlayerElement = document.getElementById('current-player');
        if (currentPlayerElement) {
            currentPlayerElement.textContent = this.gameState.current_player;
            currentPlayerElement.className = `current-player ${this.gameState.current_player}`;
        }

        // Update move history
        this.updateMoveHistory();

        // Update captured pieces
        this.updateCapturedPieces();

        // Update player info
        this.updatePlayerInfo();
    }

    updateMoveHistory() {
        const historyElement = document.getElementById('move-history');
        if (!historyElement || !this.gameState.move_history) return;

        historyElement.innerHTML = '';
        
        this.gameState.move_history.forEach((move, index) => {
            const moveElement = document.createElement('div');
            moveElement.className = 'move-item';
            moveElement.textContent = `${Math.floor(index / 2) + 1}${index % 2 === 0 ? '.' : '...'} ${move.notation || move.from + '-' + move.to}`;
            historyElement.appendChild(moveElement);
        });

        // Scroll to bottom
        historyElement.scrollTop = historyElement.scrollHeight;
    }

    updateCapturedPieces() {
        ['white', 'black'].forEach(color => {
            const element = document.getElementById(`captured-${color}`);
            if (!element || !this.gameState.captured_pieces) return;

            element.innerHTML = '';
            
            this.gameState.captured_pieces[color].forEach(piece => {
                const pieceElement = document.createElement('span');
                pieceElement.className = 'captured-piece';
                pieceElement.textContent = this.getPieceSymbol(piece);
                element.appendChild(pieceElement);
            });
        });
    }

    updatePlayerInfo() {
        ['white', 'black'].forEach(color => {
            const element = document.getElementById(`player-${color}`);
            if (element) {
                if (this.gameState.current_player === color) {
                    element.classList.add('active');
                } else {
                    element.classList.remove('active');
                }
            }
        });
    }

    updateTurnIndicator() {
        const indicator = document.getElementById('turn-indicator');
        if (indicator) {
            indicator.textContent = this.isMyTurn ? 'Your Turn' : 'Opponent\'s Turn';
            indicator.className = `turn-indicator ${this.isMyTurn ? 'my-turn' : 'opponent-turn'}`;
        }
    }

    highlightCheck() {
        if (!this.gameState.check_status) return;

        ['white', 'black'].forEach(color => {
            if (this.gameState.check_status[color]) {
                const kingPos = this.gameState.king_positions[color];
                if (kingPos) {
                    const square = document.querySelector(`[data-row="${kingPos[0]}"][data-col="${kingPos[1]}"]`);
                    if (square) {
                        square.classList.add('in-check');
                    }
                }
            }
        });
    }

    checkGameStatus() {
        if (this.gameState.game_over) {
            setTimeout(() => {
                this.handleGameOver(this.gameState.result);
            }, 1000);
        }
    }

    handleGameOver(result, reason) {
        let message = '';
        let type = 'info';

        switch (result) {
            case 'white_wins':
                if (reason === 'resignation') {
                    message = this.playerColor === 'white' ? 'You resigned the game' : 'Opponent resigned - You win!';
                } else {
                    message = 'White wins!';
                }
                type = this.playerColor === 'white' ? 'error' : 'success';
                break;
            case 'black_wins':
                if (reason === 'resignation') {
                    message = this.playerColor === 'black' ? 'You resigned the game' : 'Opponent resigned - You win!';
                } else {
                    message = 'Black wins!';
                }
                type = this.playerColor === 'black' ? 'error' : 'success';
                break;
            case 'draw':
                if (reason === 'draw_agreed') {
                    message = 'Draw agreed!';
                } else {
                    message = 'Game ended in a draw!';
                }
                type = 'warning';
                break;
        }

        this.showNotification(message, type);
        this.showGameOverModal(result);
    }

    handleDrawOffer(data) {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.id = 'draw-offer-modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px; text-align: center;">
                <h2 style="margin-bottom: 20px;">🤝 Draw Offer</h2>
                <p style="margin-bottom: 30px; color: var(--text-secondary);">
                    Your opponent is offering a draw. Do you accept?
                </p>
                <div style="display: flex; gap: 15px;">
                    <button onclick="acceptDraw(${data.game_id})" class="btn btn-warning" style="flex: 1;">
                        Accept Draw
                    </button>
                    <button onclick="declineDraw(${data.game_id})" class="btn btn-secondary" style="flex: 1;">
                        Decline
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    showGameOverModal(result) {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Game Over</h2>
                <p class="game-result">${this.getResultMessage(result)}</p>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="location.href='/dashboard'">Back to Dashboard</button>
                    <button class="btn btn-secondary" onclick="location.reload()">New Game</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    getResultMessage(result) {
        switch (result) {
            case 'white_wins':
                return this.playerColor === 'white' ? 'Congratulations! You won!' : 'You lost. Better luck next time!';
            case 'black_wins':
                return this.playerColor === 'black' ? 'Congratulations! You won!' : 'You lost. Better luck next time!';
            case 'draw':
                return 'The game ended in a draw.';
            default:
                return 'Game ended.';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Authentication and Form Handling
class AuthManager {
    static async submitForm(formId, endpoint) {
        const form = document.getElementById(formId);
        if (!form) return;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                AuthManager.showError(result.error || 'An error occurred');
            }
        } catch (error) {
            AuthManager.showError('Network error. Please try again.');
        }
    }

    static showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        } else {
            alert(message);
        }
    }

    static async createGame(mode) {
        try {
            const response = await fetch('/create-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mode })
            });

            const result = await response.json();

            if (result.success !== false) {
                if (result.redirect) {
                    window.location.href = result.redirect;
                } else if (result.room_code) {
                    AuthManager.showRoomCode(result.room_code);
                }
            } else {
                AuthManager.showError(result.error || 'Failed to create game');
            }
        } catch (error) {
            AuthManager.showError('Network error. Please try again.');
        }
    }

    static async joinGame() {
        const roomCode = document.getElementById('room-code-input')?.value;
        if (!roomCode) {
            AuthManager.showError('Please enter a room code');
            return;
        }

        try {
            const response = await fetch('/join-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ room_code: roomCode.toUpperCase() })
            });

            const result = await response.json();

            if (result.success !== false) {
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                AuthManager.showError(result.error || 'Failed to join game');
            }
        } catch (error) {
            AuthManager.showError('Network error. Please try again.');
        }
    }

    static showRoomCode(roomCode) {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Game Created!</h2>
                <p>Share this room code with your friend:</p>
                <div class="room-code">${roomCode}</div>
                <p>Waiting for opponent to join...</p>
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    static async quickJoin() {
        try {
            const response = await fetch('/quick-join', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success !== false) {
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                AuthManager.showError(result.error || 'Failed to quick join');
            }
        } catch (error) {
            AuthManager.showError('Network error. Please try again.');
        }
    }
}

// Utility Functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

    // Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initialize chess game if on game page
    if (document.getElementById('chess-board')) {
        window.chessGame = new ChessGame();
    }

    // Add smooth animations to elements
    const elements = document.querySelectorAll('.glass-card, .game-mode-card, .stat-card');
    elements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
        element.classList.add('animate-slide-up');
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formId = form.id;
            const endpoint = form.action || form.dataset.endpoint;

            if (formId && endpoint) {
                AuthManager.submitForm(formId, endpoint);
            }
        });
    });

    // Game mode selection
    document.querySelectorAll('.game-mode-card').forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.dataset.mode;
            if (mode) {
                AuthManager.createGame(mode);
            }
        });
    });

    // Room code input formatting
    const roomCodeInput = document.getElementById('room-code-input');
    if (roomCodeInput) {
        roomCodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        });
    }

    // Game controls - hide draw button for non-multiplayer games
    const offerDrawBtn = document.getElementById('offer-draw-btn');
    if (offerDrawBtn && window.gameMode) {
        if (window.gameMode !== 'friend') {
            offerDrawBtn.style.display = 'none';
        }
    }
});

// Global functions for game controls
function resignGame() {
    if (window.chessGame && window.chessGame.socket && window.chessGame.gameId) {
        // Show confirmation modal
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px; text-align: center;">
                <h2 style="margin-bottom: 20px;">🏳️ Resign Game</h2>
                <p style="margin-bottom: 30px; color: var(--text-secondary);">
                    Are you sure you want to resign? This will end the game.
                </p>
                <div style="display: flex; gap: 15px;">
                    <button onclick="confirmResign()" class="btn btn-danger" style="flex: 1;">
                        Resign
                    </button>
                    <button onclick="this.closest('.modal').remove()" class="btn btn-secondary" style="flex: 1;">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

function confirmResign() {
    if (window.chessGame && window.chessGame.socket && window.chessGame.gameId) {
        window.chessGame.socket.emit('resign_game', { game_id: window.chessGame.gameId });
        document.querySelector('.modal').remove();
    }
}

function offerDraw() {
    if (window.chessGame && window.chessGame.socket && window.chessGame.gameId) {
        // Show confirmation modal
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 400px; text-align: center;">
                <h2 style="margin-bottom: 20px;">🤝 Offer Draw</h2>
                <p style="margin-bottom: 30px; color: var(--text-secondary);">
                    Send a draw offer to your opponent?
                </p>
                <div style="display: flex; gap: 15px;">
                    <button onclick="confirmOfferDraw()" class="btn btn-warning" style="flex: 1;">
                        Send Offer
                    </button>
                    <button onclick="this.closest('.modal').remove()" class="btn btn-secondary" style="flex: 1;">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

function confirmOfferDraw() {
    if (window.chessGame && window.chessGame.socket && window.chessGame.gameId) {
        window.chessGame.socket.emit('offer_draw', { game_id: window.chessGame.gameId });
        document.querySelector('.modal').remove();
        window.chessGame.showNotification('Draw offer sent to opponent', 'info');
    }
}

function acceptDraw(gameId) {
    if (window.chessGame && window.chessGame.socket) {
        window.chessGame.socket.emit('respond_draw', {
            game_id: gameId,
            response: 'accept'
        });
        document.getElementById('draw-offer-modal').remove();
    }
}

function declineDraw(gameId) {
    if (window.chessGame && window.chessGame.socket) {
        window.chessGame.socket.emit('respond_draw', {
            game_id: gameId,
            response: 'decline'
        });
        document.getElementById('draw-offer-modal').remove();
    }
}

// Export for use in other files
window.ChessGame = ChessGame;
window.AuthManager = AuthManager;
