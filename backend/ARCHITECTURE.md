# Chess 39 Backend - Architecture & Services Documentation

**For Junior Developers & New Team Members**

This document explains the architecture, purpose of each service, and how everything works together.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Service Breakdown](#service-breakdown)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)

---

## System Overview

Chess 39 is an online chess platform where players start with **random armies worth 39 points** (instead of the standard chess setup). The backend handles:

- ✅ User authentication and profiles
- ✅ Random army generation
- ✅ Move validation using chess rules
- ✅ Game state management
- ✅ ELO rating calculation
- ✅ Real-time game updates (via Redis pub/sub)

**Key Design Principle:** Server-authoritative validation
- All game logic runs on the server
- Clients can only request moves; server validates them
- This prevents cheating and ensures fair play

---

## Architecture Diagram

```
┌─────────────────┐
│   Client/UI     │  (Future: Next.js Frontend)
│  (Web Browser)  │
└────────┬────────┘
         │ HTTP/WebSocket
         │
┌────────▼─────────────────────────────────────┐
│         FastAPI Backend (Python)              │
│                                               │
│  ┌──────────────────────────────────────┐   │
│  │  API Routes (/api/auth, /api/games)  │   │
│  └──────────┬───────────────────────────┘   │
│             │                                 │
│  ┌──────────▼──────────┐  ┌───────────────┐ │
│  │   Game Service      │  │  Auth Service │ │
│  │  (Business Logic)   │  │     (JWT)     │ │
│  └──────────┬──────────┘  └───────────────┘ │
│             │                                 │
│  ┌──────────▼──────────────────────────────┐│
│  │      chess39-core (Game Engine)         ││
│  │   - Move validation                     ││
│  │   - Check/checkmate detection           ││
│  │   - Random army generation              ││
│  └─────────────────────────────────────────┘│
└──────────┬────────────────────┬──────────────┘
           │                    │
  ┌────────▼────────┐  ┌────────▼────────┐
  │   PostgreSQL    │  │      Redis      │
  │   (Persistent   │  │    (Cache &     │
  │     Storage)    │  │    Pub/Sub)     │
  └─────────────────┘  └─────────────────┘
```

---

## Service Breakdown

### 1. **FastAPI Application** (`app/main.py`)

**Purpose:** The main web server that handles HTTP requests.

**What it does:**
- Starts the web server
- Routes requests to the correct API endpoints
- Handles CORS (allows frontend to connect)
- Serves API documentation at `/docs`

**Key Code:**
```python
app = FastAPI(title="Chess 39 API")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(games_router, prefix="/api/games")
```

**Why we need it:**
Without this, there'd be no way for clients to communicate with the backend.

---

### 2. **Authentication Service** (`app/api/routes/auth.py`, `app/core/security.py`)

**Purpose:** Manages user accounts and login security.

**What it does:**
- **Signup:** Creates new user accounts with hashed passwords
- **Login:** Verifies credentials and issues JWT tokens
- **Token Validation:** Ensures only logged-in users can access protected endpoints

**Key Components:**

#### Password Hashing (`security.py`)
```python
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)  # One-way encryption
```

**Why hash passwords?**
- If database is compromised, attackers can't read passwords
- Uses bcrypt (industry standard)

#### JWT Tokens
```python
def create_access_token(data: dict) -> str:
    # Creates a signed token that expires in 60 minutes
    return jwt.encode(data, SECRET_KEY)
```

**Why JWT?**
- Stateless (server doesn't need to store session data)
- Can't be tampered with (signed cryptographically)
- Expires automatically

**Example Flow:**
1. User sends email + password
2. Server verifies credentials
3. Server creates JWT with user's ID
4. Client stores JWT and sends it with every request
5. Server verifies JWT to identify user

---

### 3. **Database Layer** (`app/db/`)

**Purpose:** Stores and retrieves persistent data.

#### PostgreSQL Database (`app/db/models.py`)

**What it stores:**

**Users Table:**
- User accounts (username, email, hashed password)
- Stats (ELO rating, wins, losses, draws)
- Timestamps (created_at, last_login)

**Games Table:**
- Game metadata (players, status, winner)
- Initial board setup (random armies)
- Current game state (updated after each move)

**Moves Table:**
- Every move made in every game
- Used for game replay and history
- Helps detect patterns/cheating

#### SQLAlchemy ORM
```python
class User(Base):
    id = Column(UUID, primary_key=True)
    username = Column(String, unique=True)
    elo_rating = Column(Integer, default=1200)
```

**Why use an ORM?**
- Write Python code instead of SQL
- Automatic table creation
- Prevents SQL injection attacks

---

### 4. **Redis Cache** (`app/services/redis_client.py`)

**Purpose:** Fast temporary storage and real-time messaging.

**What it does:**

#### Caching Game State
```python
def cache_game_state(game_id, state, ttl=86400):
    # Store game in RAM for 24 hours
    redis.setex(f"game:{game_id}", ttl, json.dumps(state))
```

**Why cache?**
- 🚀 **Speed:** Redis is in-memory (100x faster than disk)
- 🎯 **Hot data:** Active games are accessed frequently
- 💰 **Cost:** Reduces database load

**Flow:**
1. First request: Load from PostgreSQL → Cache in Redis
2. Subsequent requests: Serve from Redis (instant)
3. After 24 hours: Clear cache (game inactive)

#### Pub/Sub for Real-Time Updates
```python
def publish_game_update(game_id, message):
    redis.publish(f"game:{game_id}", json.dumps(message))
```

**Why pub/sub?**
- Broadcast moves to all connected players instantly
- Supports WebSocket notifications
- Enables multi-server scaling

**Example:**
1. Alice makes a move
2. Server publishes: `{"type": "move", "from": "e2", "to": "e4"}`
3. All subscribed clients (Bob's browser) receive update
4. Bob's board updates automatically

---

### 5. **Game Service Layer** (`app/services/game_service.py`)

**Purpose:** Core business logic for game management.

**What it does:**

#### Create Game
```python
def create_game(white_id, black_id, db):
    # 1. Generate random armies using chess39-core
    game = Game(white_id, black_id)
    game.start_game()  # Random 39-point armies
    
    # 2. Save to database
    db_game = GameModel(initial_state=game.get_state())
    db.add(db_game)
    
    # 3. Cache in Redis
    cache_game_state(db_game.id, game.get_state())
    
    return db_game
```

#### Process Move
```python
def make_move(game_id, from_sq, to_sq, player_id, db):
    # 1. Load game (try cache → fallback to DB)
    # 2. Validate move using chess39-core
    # 3. Update database
    # 4. Update cache
    # 5. Publish to Redis pub/sub
    # 6. Update ELO if game ended
```

**Why this layer?**
- Keeps API routes thin (they just call service functions)
- Centralizes business logic
- Easier to test

---

### 6. **Chess39-Core** (`chess39-core/`)

**Purpose:** Pure game logic (no database, no API, just chess).

**What it does:**

#### Move Validation (`game.py`)
```python
def make_move(from_sq, to_sq, player_id):
    # 1. Verify it's player's turn
    # 2. Validate piece can make that move (chess rules)
    # 3. Ensure move doesn't leave king in check
    # 4. Execute move
    # 5. Check for checkmate/stalemate
```

**Rules Implemented:**
- ♟️ Pawn moves (1 or 2 forward, diagonal capture, en passant)
- ♞ Knight L-shaped moves
- ♗ Bishop diagonal slides
- ♜ Rook orthogonal slides
- ♛ Queen (combines bishop + rook)
- ♚ King 1-square moves + castling
- ✓ Check/checkmate detection
- ✓ Stalemate detection
- ✓ 50-move rule

#### Random Army Generation (`army.py`)
```python
def generate_random_army():
    # Generate pieces that sum to exactly 39 points
    # Max 8 pawns (prevents pawn-only armies)
    # Always includes 1 King (worth 0 points)
```

**Point Values:**
- Pawn: 1
- Knight: 3
- Bishop: 3
- Rook: 5
- Queen: 9
- King: 0 (always included)

**Why separate from backend?**
- Reusable (could use in desktop app, mobile app)
- Testable independently
- No dependencies on web frameworks

---

### 7. **API Routes** (`app/api/routes/`)

**Purpose:** HTTP endpoints that clients call.

#### Auth Routes (`auth.py`)
```
POST   /api/auth/signup      → Create account
POST   /api/auth/login       → Get JWT token
GET    /api/auth/me-info     → Get user profile
```

#### Game Routes (`games.py`)
```
POST   /api/games                    → Create new game
GET    /api/games/{id}               → Get game state
GET    /api/games                    → List user's games
POST   /api/games/{id}/move          → Submit move
POST   /api/games/{id}/resign        → Resign game
```

**Example Request/Response:**
```bash
# Request
POST /api/games
Authorization: Bearer <token>
{
  "opponent_id": "user-uuid"
}

# Response
{
  "id": "game-uuid",
  "white_player": {...},
  "black_player": {...},
  "board": {"a1": ["ROOK", "white"], ...},
  "status": "ongoing"
}
```

---

### 8. **ELO Rating System** (`game_service.py`)

**Purpose:** Calculate player skill ratings after each game.

**How it works:**
```python
def update_elo_ratings(game, db):
    # 1. Get current ratings
    white_elo = white_player.elo_rating
    black_elo = black_player.elo_rating
    
    # 2. Calculate expected scores (probability of winning)
    white_expected = 1 / (1 + 10^((black_elo - white_elo)/400))
    
    # 3. Calculate actual scores
    white_score = 1.0  # (1=win, 0.5=draw, 0=loss)
    
    # 4. Update ratings
    K = 32  # How much ratings change per game
    white_elo += K * (white_score - white_expected)
```

**Example:**
- Alice (1200) beats Bob (1200)
- Expected outcome: 50% chance each
- Alice gains: +16 ELO
- Bob loses: -16 ELO
- New ratings: Alice 1216, Bob 1184

**Why ELO?**
- Industry standard (used in chess, gaming)
- Self-correcting (everyone starts at 1200)
- Higher rated players gain less for beating lower rated players

---

## Data Flow

### Example: Making a Move

```
1. Client Request
   └─> POST /api/games/abc123/move
       {from: "e2", to: "e4"}
       Authorization: Bearer <token>

2. FastAPI
   └─> Verify JWT token
   └─> Extract user_id from token
   └─> Call games.make_move() route

3. Game Route
   └─> Get game_id from URL
   └─> Call game_service.make_move()

4. Game Service
   ├─> Load game from Redis/PostgreSQL
   ├─> Validate move using chess39-core
   ├─> Update PostgreSQL (new state + move record)
   ├─> Update Redis cache
   └─> Publish to Redis pub/sub

5. chess39-core
   ├─> Check it's player's turn
   ├─> Validate piece movement
   ├─> Check for check/checkmate
   └─> Return validation result

6. Response to Client
   └─> {
         "success": true,
         "is_check": false,
         "status": "ongoing"
       }

7. Real-Time Update (Optional)
   └─> Redis pub/sub → WebSocket → Other player's browser
```

---

## Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **Web Framework** | FastAPI | Fast, modern, auto-generates docs |
| **Language** | Python 3.9+ | Easy to read, great libraries |
| **Database** | PostgreSQL | Reliable, supports complex queries |
| **Cache** | Redis | In-memory speed, pub/sub support |
| **ORM** | SQLAlchemy | Python ↔ SQL translation |
| **Migrations** | Alembic | Version control for database schema |
| **Auth** | JWT + bcrypt | Stateless auth, secure passwords |
| **API Docs** | OpenAPI (Swagger) | Auto-generated from code |
| **Deployment** | Uvicorn (ASGI) | High-performance server |

---

## Security Features

1. **Password Hashing:** Bcrypt with salt (can't reverse)
2. **JWT Tokens:** Cryptographically signed, expire in 60 minutes
3. **CORS Protection:** Only allowed origins can access API
4. **SQL Injection Prevention:** ORM parameterizes queries
5. **Move Validation:** Server-side only (client can't cheat)
6. **Rate Limiting:** (TODO) Prevent spam/DDoS

---

## Performance Optimizations

1. **Redis Caching:** Active games loaded from RAM
2. **Database Indexing:** Fast lookups on email, username, game_id
3. **Connection Pooling:** Reuse database connections
4. **ASGI Server:** Handles thousands of concurrent requests
5. **Pub/Sub:** Efficient real-time updates

---

## Common Patterns

### Dependency Injection
```python
def create_user(db: Session = Depends(get_db)):
    # FastAPI automatically provides db session
    # Automatically closes connection after request
```

###Error Handling
```python
if not user:
    raise HTTPException(status_code=404, detail="User not found")
```

### Authentication
```python
@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    # Only logged-in users can access this
```

---

## Glossary

- **ORM:** Object-Relational Mapping (Python objects ↔ database rows)
- **JWT:** JSON Web Token (secure way to transmit user identity)
- **CORS:** Cross-Origin Resource Sharing (allows frontend on different domain)
- **Pub/Sub:** Publish/Subscribe (messaging pattern for real-time updates)
- **ASGI:** Asynchronous Server Gateway Interface (handles async Python)
- **ELO:** Rating system named after Arpad Elo
- **Migration:** Script that updates database schema
- **Serialization:** Converting objects to JSON for storage/transmission

---

## File Structure Reference

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Environment variables
│   │   └── security.py         # JWT & password hashing
│   ├── db/
│   │   ├── database.py         # SQLAlchemy setup
│   │   └── models.py           # Database tables (User, Game, Move)
│   ├── schemas/
│   │   ├── user.py             # API request/response models (users)
│   │   └── game.py             # API request/response models (games)
│   ├── api/
│   │   ├── dependencies.py     # Common dependencies (auth)
│   │   └── routes/
│   │       ├── auth.py         # /api/auth/* endpoints
│   │       └── games.py        # /api/games/* endpoints
│   └── services/
│       ├── redis_client.py     # Redis operations
│       └── game_service.py     # Game business logic
├── alembic/                    # Database migrations
├── docker-compose.yml          # PostgreSQL + Redis containers
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (SECRET_KEY, etc.)
```

---

## Development Workflow

1. **Make Code Changes:** Edit Python files
2. **Server Auto-Reloads:** Uvicorn `--reload` flag
3. **Test in Browser:** http://localhost:8000/docs
4. **Check Logs:** Terminal where uvicorn is running
5. **Database Changes:** Create Alembic migration

---

## Debugging Tips

**Problem:** 500 Internal Server Error

**Solution:** Check server logs in terminal

---

**Problem:** Database error

**Solution:**
```bash
docker compose ps  # Check PostgreSQL is running
python3 -m alembic upgrade head  # Run migrations
```

---

**Problem:** Authentication error

**Solution:** Token might be expired, login again

---

## Next Steps for New Developers

1. [ ] Read this entire document
2. [ ] Follow TESTING_GUIDE.md to try all endpoints
3. [ ] Read chess39-core/game.py to understand move validation
4. [ ] Try creating a new API endpoint
5. [ ] Add a new database field with Alembic migration

---

**Questions?** Ask senior developers or check:
- FastAPI docs: https://fastapi.tiangolo.com
- SQLAlchemy docs: https://docs.sqlalchemy.org
- Redis docs: https://redis.io/docs

**Last Updated:** November 2025
