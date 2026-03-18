# Grandmaster-Arena
Chess created for Python project using PYTHoN, HTML, CSS, JS
>>>>>>> c0838e541e669a96f12a5068eb729fef3d1c1759
=======
# Grandmaster-Arena

A beautiful, modern chess application built with Python Flask, featuring AI opponents, real-time multiplayer, and a stunning glass morphism UI. All official FIDE chess rules are implemented for an authentic chess experience.

## ✨ Features

### 🎮 Game Modes
- **🤖 AI Challenge**: Intelligent AI opponent with multiple difficulty levels
- **💻 Computer Player**: Quick casual games for practice
- **👥 Multiplayer**: Real-time games with friends using room codes

### 🏆 Chess Features
- ✅ **Complete FIDE Rules**: All official chess rules implemented
- 🏰 **Special Moves**: Castling, en passant, pawn promotion
- 📋 **Game States**: Check, checkmate, stalemate detection
- 📊 **Move History**: Complete notation and replay
- ⏱️ **Real-time Play**: Instant move updates via WebSocket

### 🎨 UI/UX Features
- 🌟 **Glass Morphism Design**: Modern, beautiful interface
- 📱 **Fully Responsive**: Works on desktop, tablet, and mobile
- ⚡ **Smooth Animations**: Fluid transitions and effects
- 🎯 **Intuitive Controls**: Easy drag-and-drop or click-to-move
- 🌙 **Dark Theme**: Eye-friendly design

### 👤 User Features
- 🔐 **Authentication**: Secure login/registration system
- 📧 **Password Reset**: Email-based password recovery
- 📈 **Player Statistics**: Rating system and game history
- 🏅 **Achievements**: Progress tracking and badges
- 👥 **Social Features**: Friends and multiplayer rooms

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Manthan03117/Grandmaster-Arena.git
   cd Grandmaster-Arena
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv chess_env

   # On Windows
   chess_env\Scripts\activate

   # On macOS/Linux
   source chess_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional)**
   ```bash
   # Create .env file for email configuration
   echo "EMAIL_USER=your_email@gmail.com" > .env
   echo "EMAIL_PASS=your_app_password" >> .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 How to Play

### Getting Started
1. **Create an Account**: Register with username, email, and password
2. **Choose Game Mode**: Select AI, Computer, or Multiplayer
3. **Start Playing**: Make moves by clicking pieces and destination squares

### Game Modes

#### 🤖 AI Challenge
- Choose difficulty: Easy, Medium, Hard, Expert
- AI uses advanced minimax algorithm with alpha-beta pruning
- Positional evaluation and strategic play

#### 💻 Computer Player
- Quick games for practice
- Beginner-friendly opponent
- Instant game start

#### 👥 Multiplayer
- **Create Game**: Get a 6-character room code to share
- **Join Game**: Enter a room code to join a friend's game
- **Real-time**: Moves appear instantly for both players

### Chess Rules Implemented
- **Basic Movement**: All pieces move according to official rules
- **Castling**: Kingside and queenside castling
- **En Passant**: Pawn captures en passant
- **Promotion**: Pawn promotion to Queen, Rook, Bishop, or Knight
- **Check/Checkmate**: Automatic detection and game end
- **Stalemate**: Draw conditions properly handled
- **50-Move Rule**: Automatic draw after 50 moves without capture/pawn move

## 🛠️ Technical Details

### Architecture
- **Backend**: Flask with SQLAlchemy (SQLite database)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Real-time**: WebSocket via Flask-SocketIO
- **Authentication**: Flask-Bcrypt for password hashing
- **Email**: Flask-Mail for password reset

### Project Structure
```
Grandmaster-Arena/
├── app.py                 # Main Flask application
├── chess_engine.py        # Chess game logic and rules
├── ai_player.py          # AI opponent implementation
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── PROJECT_REPORT.md     # Comprehensive project documentation
├── PROJECT_REPORT.docx   # Word document version
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── auth.html         # Login/register forms
│   ├── dashboard.html    # User dashboard
│   └── play.html         # Game interface
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Main stylesheet
    ├── js/
    │   └── chess.js      # Frontend JavaScript
    └── images/           # Image assets
```

### AI Implementation
The AI opponent uses:
- **Minimax Algorithm**: With alpha-beta pruning for efficiency
- **Position Evaluation**: Piece values and positional bonuses
- **Opening Knowledge**: Basic opening principles
- **Endgame Logic**: King activity in endgames
- **Difficulty Levels**: Adjustable search depth

## 🔧 Configuration

### Environment Variables
```bash
# Email configuration (optional)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# Flask configuration
FLASK_ENV=development  # or production
SECRET_KEY=your_secret_key
```

### Database
The application uses SQLite by default. The database file (`chess.db`) will be created automatically when you first run the application.

To reset the database:
```bash
rm chess.db
python app.py  # Will recreate the database
```

## 🎨 Customization

### Themes
The CSS uses CSS custom properties (variables) for easy theming. Modify the `:root` section in `static/css/style.css`:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #f093fb;
    /* ... other variables */
}
```

### Chess Board
Customize the chess board appearance by modifying the `.chess-square` classes in the CSS file.

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -k eventlet -w 1 app:app
```

#### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Implement your feature or fix
4. **Test thoroughly**: Ensure everything works
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Areas for Contribution
- 🎨 **UI/UX Improvements**: Better animations, themes, mobile experience
- 🤖 **AI Enhancement**: Stronger chess engine, opening books
- 🌐 **Features**: Tournaments, spectator mode, analysis board
- 🐛 **Bug Fixes**: Report and fix issues
- 📚 **Documentation**: Improve guides and tutorials

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Chess.js**: Inspiration for chess logic implementation
- **Socket.IO**: Real-time communication
- **Flask Community**: Excellent documentation and support
- **Inter Font**: Beautiful typography by Rasmus Andersson
- **Chess Pieces**: Unicode chess symbols

## 📞 Support

Having issues? Here's how to get help:

1. **Check the Issues**: Look for existing solutions
2. **Create an Issue**: Describe your problem clearly
3. **Discord Community**: Join our Discord for real-time help
4. **Email Support**: contact@chessgamepro.com

## 🔮 Roadmap

### Version 2.0 (Coming Soon)
- 🏆 **Tournaments**: Organized competitions
- 📊 **Analysis Board**: Post-game analysis
- 🎓 **Tutorials**: Interactive chess lessons
- 👁️ **Spectator Mode**: Watch other games
- 🌍 **Internationalization**: Multiple languages

### Version 3.0 (Future)
- 📱 **Mobile App**: Native iOS/Android apps
- 🧠 **Neural Network AI**: Deep learning opponent
- ☁️ **Cloud Save**: Cross-device game sync
- 📺 **Streaming**: Twitch/YouTube integration

---

**Made with ♥ for chess enthusiasts worldwide**

*Experience the ultimate chess game today!* 🎮♔
=======
# Grandmaster-Arena
Chess created for Python project using PYTHoN, HTML, CSS, JS
>>>>>>> c0838e541e669a96f12a5068eb729fef3d1c1759
#   G r a n d m a s t e r - A r e n a  
 