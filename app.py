from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import secrets
import os
import json
from chess_engine import ChessGame
from ai_player import AIPlayer

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chess.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration (for password reset)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    rating = db.Column(db.Integer, default=1200)
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    white_player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    black_player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    game_state = db.Column(db.Text, nullable=False, default='{}')
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    result = db.Column(db.String(20), nullable=True)  # white_wins, black_wins, draw
    game_mode = db.Column(db.String(20), nullable=False)  # friend, computer, ai
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_code = db.Column(db.String(6), unique=True, nullable=True)

# Active games storage
active_games = {}

# AI Tutor Lesson Content
LESSONS = {
    'basics': {
        'title': 'Chess Basics',
        'description': 'Learn the fundamentals of chess',
        'sections': [
            {
                'title': 'The Chess Board',
                'content': 'The chess board is an 8x8 grid with 64 squares. Each player starts with 16 pieces.',
                'position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            },
            {
                'title': 'Piece Values',
                'content': 'Pawn=1, Knight=3, Bishop=3, Rook=5, Queen=9, King=∞',
                'position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            }
        ]
    },
    'piece_movement': {
        'title': 'How Pieces Move',
        'description': 'Master the movement of each chess piece',
        'sections': [
            {
                'title': 'The King',
                'content': 'The king moves one square in any direction.',
                'position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            },
            {
                'title': 'The Queen',
                'content': 'The queen combines the power of rook and bishop - she moves any number of squares in any direction.',
                'position': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            }
        ]
    },
    'tactics': {
        'title': 'Chess Tactics',
        'description': 'Learn essential tactical patterns',
        'sections': [
            {
                'title': 'Pins',
                'content': 'A pin occurs when a piece cannot move because it would expose a more valuable piece behind it.',
                'position': 'rnbqkbnr/ppp2ppp/8/3p4/8/3B4/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            }
        ]
    }
}

PRACTICE_POSITIONS = [
    {
        'id': 1,
        'title': 'Basic Checkmate',
        'description': 'Find the checkmate in 1 move',
        'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1',
        'solution': 'Qh5',
        'hint': 'Look for the queen to deliver checkmate'
    },
    {
        'id': 2,
        'title': 'Knight Fork',
        'description': 'Create a knight fork',
        'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1',
        'solution': 'Nxe5',
        'hint': 'The knight can attack two pieces at once'
    }
]

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({'success': True, 'redirect': '/dashboard'})
    
    return render_template('auth.html', form_type='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'redirect': '/dashboard'})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('auth.html', form_type='login')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send email (if configured)
            try:
                msg = Message('Chess Game Password Reset',
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[email])
                msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request, please ignore this email.
'''
                mail.send(msg)
                return jsonify({'success': True, 'message': 'Reset email sent'})
            except:
                return jsonify({'success': True, 'message': 'Reset token: ' + token})
        
        return jsonify({'success': True, 'message': 'If email exists, reset link sent'})
    
    return render_template('auth.html', form_type='forgot')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.token_expiry < datetime.utcnow():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')
        
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user.reset_token = None
        user.token_expiry = None
        db.session.commit()
        
        return jsonify({'success': True, 'redirect': '/login'})
    
    return render_template('auth.html', form_type='reset', token=token)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    recent_games = Game.query.filter(
        (Game.white_player_id == user.id) | (Game.black_player_id == user.id)
    ).order_by(Game.created_at.desc()).limit(5).all()
    
    # Calculate member days
    from datetime import datetime
    member_days = (datetime.utcnow() - user.created_at).days + 1
    
    return render_template('dashboard.html', user=user, recent_games=recent_games, member_days=member_days)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/game/<game_mode>')
def game(game_mode):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    valid_modes = ['friend', 'computer', 'ai']
    if game_mode not in valid_modes:
        return redirect(url_for('dashboard'))
    
    return render_template('game.html', game_mode=game_mode)

@app.route('/create-game', methods=['POST'])
def create_game():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    game_mode = data.get('mode')
    
    if game_mode not in ['friend', 'computer', 'ai']:
        return jsonify({'error': 'Invalid game mode'}), 400
    
    # Create new game
    game = Game(
        white_player_id=session['user_id'],
        game_mode=game_mode,
        game_state=json.dumps(ChessGame().to_dict())
    )
    
    if game_mode == 'friend':
        game.room_code = secrets.token_hex(3).upper()
    
    db.session.add(game)
    db.session.commit()
    
    # Initialize game in memory
    active_games[game.id] = ChessGame()
    
    if game_mode in ['computer', 'ai']:
        game.black_player_id = -1  # AI player
        game.status = 'active'
        db.session.commit()
    
    return jsonify({
        'game_id': game.id,
        'room_code': game.room_code,
        'redirect': f'/play/{game.id}'
    })

@app.route('/join-game', methods=['POST'])
def join_game():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    room_code = data.get('room_code')
    
    game = Game.query.filter_by(room_code=room_code, status='waiting').first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    if game.white_player_id == session['user_id']:
        return jsonify({'error': 'Cannot join your own game'}), 400
    
    game.black_player_id = session['user_id']
    game.status = 'active'
    db.session.commit()
    
    return jsonify({'game_id': game.id, 'redirect': f'/play/{game.id}'})

@app.route('/quick-join', methods=['POST'])
def quick_join():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Find a waiting game created by another user
    game = Game.query.filter(
        Game.status == 'waiting',
        Game.white_player_id != session['user_id'],
        Game.game_mode == 'friend'
    ).first()
    
    if game:
        game.black_player_id = session['user_id']
        game.status = 'active'
        db.session.commit()
        return jsonify({'game_id': game.id, 'redirect': f'/play/{game.id}'})
    else:
        # No waiting game found, create a new one
        new_game = Game(
            white_player_id=session['user_id'],
            game_mode='friend',
            game_state=json.dumps(ChessGame().to_dict()),
            room_code=secrets.token_hex(3).upper()
        )
        db.session.add(new_game)
        db.session.commit()
        active_games[new_game.id] = ChessGame()
        return jsonify({'game_id': new_game.id, 'redirect': f'/play/{new_game.id}'})

@app.route('/play/<int:game_id>')
def play_game(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    game = Game.query.get_or_404(game_id)
    
    # Check if user is part of this game
    if game.white_player_id != session['user_id'] and game.black_player_id != session['user_id']:
        return redirect(url_for('dashboard'))
    
    # Load game state
    if game_id not in active_games:
        game_state = json.loads(game.game_state)
        active_games[game_id] = ChessGame.from_dict(game_state)
    
    return render_template(
    'play.html',
    game=game,
    game_id=game.id,
    game_mode=game.game_mode
)


@app.route('/api/possible-moves', methods=['POST'])
def get_possible_moves():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    game_id = data.get('game_id')
    position = data.get('position')
    
    if game_id not in active_games:
        return jsonify({'error': 'Game not found'}), 404
    
    chess_game = active_games[game_id]
    
    try:
        # Convert position to row, col
        col = ord(position[0]) - ord('a')
        row = 8 - int(position[1])
        
        moves = chess_game.get_possible_moves(row, col)
        
        # Convert moves back to algebraic notation
        move_positions = []
        for move_row, move_col in moves:
            move_pos = chr(move_col + ord('a')) + str(8 - move_row)
            move_positions.append(move_pos)
        
        return jsonify({'moves': move_positions})
    
    except (ValueError, IndexError):
        return jsonify({'error': 'Invalid position'}), 400

# Socket.IO events
@socketio.on('join_game')
def on_join(data):
    game_id = data['game_id']
    join_room(f'game_{game_id}')

    if game_id in active_games:
        emit('game_state', active_games[game_id].to_dict())

@socketio.on('make_move')
def on_move(data):
    game_id = data['game_id']
    move = data['move']
    user_id = session.get('user_id')

    if game_id not in active_games:
        return

    game = Game.query.get(game_id)
    chess_game = active_games[game_id]

    # Validate it's the player's turn
    if (chess_game.current_player == 'white' and game.white_player_id != user_id) or \
       (chess_game.current_player == 'black' and game.black_player_id != user_id):
        return

    # Make move
    if chess_game.make_move(move['from'], move['to'], move.get('promotion')):
        # Save game state
        game.game_state = json.dumps(chess_game.to_dict())
        db.session.commit()

        # Broadcast new state
        emit('game_state', chess_game.to_dict(), room=f'game_{game_id}')

        # Check for game end
        if chess_game.is_game_over():
            result = chess_game.get_result()
            game.result = result
            game.status = 'finished'

            # Update player stats
            if result != 'draw':
                winner_id = game.white_player_id if result == 'white_wins' else game.black_player_id
                loser_id = game.black_player_id if result == 'white_wins' else game.white_player_id

                if winner_id > 0:  # Not AI
                    winner = User.query.get(winner_id)
                    winner.games_won += 1
                    winner.games_played += 1
                    winner.rating += 25

                if loser_id > 0:  # Not AI
                    loser = User.query.get(loser_id)
                    loser.games_played += 1
                    loser.rating = max(800, loser.rating - 25)

            db.session.commit()
            emit('game_over', {'result': result}, room=f'game_{game_id}')

        # AI move for computer/ai modes
        elif game.game_mode in ['computer', 'ai'] and chess_game.current_player == 'black':
            ai_player = AIPlayer(difficulty='hard' if game.game_mode == 'ai' else 'medium')
            ai_move = ai_player.get_move(chess_game)

            if ai_move and chess_game.make_move(ai_move['from'], ai_move['to'], ai_move.get('promotion')):
                game.game_state = json.dumps(chess_game.to_dict())
                db.session.commit()

                emit('game_state', chess_game.to_dict(), room=f'game_{game_id}')

                if chess_game.is_game_over():
                    result = chess_game.get_result()
                    game.result = result
                    game.status = 'finished'

                    # Update player stats
                    if result == 'white_wins':
                        user = User.query.get(game.white_player_id)
                        user.games_won += 1
                        user.games_played += 1
                        user.rating += 30  # Bonus for beating AI
                    elif result == 'black_wins':
                        user = User.query.get(game.white_player_id)
                        user.games_played += 1
                        user.rating = max(800, user.rating - 15)

                    db.session.commit()
                    emit('game_over', {'result': result}, room=f'game_{game_id}')

@socketio.on('resign_game')
def on_resign(data):
    game_id = data['game_id']
    user_id = session.get('user_id')

    if game_id not in active_games:
        return

    game = Game.query.get(game_id)
    if not game or game.status == 'finished':
        return

    # Determine the winner and loser
    if game.white_player_id == user_id:
        # White resigned, black wins
        winner_id = game.black_player_id
        loser_id = game.white_player_id
        result = 'black_wins'
    elif game.black_player_id == user_id:
        # Black resigned, white wins
        winner_id = game.white_player_id
        loser_id = game.black_player_id
        result = 'white_wins'
    else:
        return  # Not a player in this game

    # Update game status
    game.result = result
    game.status = 'finished'
    db.session.commit()

    # Update player stats
    if winner_id > 0:  # Not AI
        winner = User.query.get(winner_id)
        winner.games_won += 1
        winner.games_played += 1
        winner.rating += 25

    if loser_id > 0:  # Not AI
        loser = User.query.get(loser_id)
        loser.games_played += 1
        loser.rating = max(800, loser.rating - 25)

    db.session.commit()

    # Notify all players in the room
    emit('game_over', {'result': result, 'reason': 'resignation'}, room=f'game_{game_id}')

@socketio.on('offer_draw')
def on_offer_draw(data):
    game_id = data['game_id']
    user_id = session.get('user_id')

    if game_id not in active_games:
        return

    game = Game.query.get(game_id)
    if not game or game.status == 'finished' or game.game_mode != 'friend':
        return

    # Send draw offer to the opponent
    opponent_id = game.white_player_id if game.white_player_id != user_id else game.black_player_id
    if opponent_id > 0:  # Human opponent
        emit('draw_offer', {
            'from_player': user_id,
            'game_id': game_id
        }, room=f'game_{game_id}')

@socketio.on('respond_draw')
def on_respond_draw(data):
    game_id = data['game_id']
    response = data['response']  # 'accept' or 'decline'
    user_id = session.get('user_id')

    if game_id not in active_games:
        return

    game = Game.query.get(game_id)
    if not game or game.status == 'finished' or game.game_mode != 'friend':
        return

    if response == 'accept':
        # End game as draw
        game.result = 'draw'
        game.status = 'finished'

        # Update player stats for both players
        for player_id in [game.white_player_id, game.black_player_id]:
            if player_id > 0:  # Not AI
                player = User.query.get(player_id)
                player.games_played += 1

        db.session.commit()

        # Notify all players
        emit('game_over', {'result': 'draw', 'reason': 'draw_agreed'}, room=f'game_{game_id}')
    else:
        # Draw declined, notify the requesting player
        emit('draw_declined', {'game_id': game_id}, room=f'game_{game_id}')

@app.route('/ai-lesson')
def ai_lesson():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    lesson_id = request.args.get('lesson', 'basics')
    section_id = int(request.args.get('section', 0))

    lesson = LESSONS.get(lesson_id)
    if not lesson:
        return redirect(url_for('dashboard'))

    current_section = lesson['sections'][min(section_id, len(lesson['sections']) - 1)]
    next_section = section_id + 1 if section_id + 1 < len(lesson['sections']) else None
    prev_section = section_id - 1 if section_id > 0 else None

    return render_template('lesson.html',
                         lesson=lesson,
                         current_section=current_section,
                         section_id=section_id,
                         next_section=next_section,
                         prev_section=prev_section,
                         lesson_id=lesson_id)

@app.route('/ai-practice')
def ai_practice():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    position_id = int(request.args.get('position', 0))
    position = PRACTICE_POSITIONS[min(position_id, len(PRACTICE_POSITIONS) - 1)]

    next_position = position_id + 1 if position_id + 1 < len(PRACTICE_POSITIONS) else None
    prev_position = position_id - 1 if position_id > 0 else None

    return render_template('practice.html',
                         position=position,
                         position_id=position_id,
                         next_position=next_position,
                         prev_position=prev_position)

@app.route('/api/check-solution', methods=['POST'])
def check_solution():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    position_id = data.get('position_id')
    move = data.get('move')

    if position_id >= len(PRACTICE_POSITIONS):
        return jsonify({'error': 'Invalid position'}), 400

    position = PRACTICE_POSITIONS[position_id]
    correct = move.lower() == position['solution'].lower()

    return jsonify({
        'correct': correct,
        'solution': position['solution'] if not correct else None
    })

# Initialize database tables
def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=os.environ.get('FLASK_ENV') == 'development', host='0.0.0.0', port=5000)
