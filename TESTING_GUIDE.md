# Chess 39 Backend - API Testing Guide

**For QA Team & Junior Developers**

This guide explains how to test the Chess 39 backend API step-by-step.

---

## Prerequisites

### 1. Start the Backend Server

```bash
cd /Users/admin/Desktop/chess-39-project/backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Start Docker Services (PostgreSQL + Redis)

```bash
cd /Users/admin/Desktop/chess-39-project/backend
docker compose up -d
```

**Verify services are running:**
```bash
docker compose ps
# Should show postgres and redis containers running
```

### 3. Apply Database Migrations

```bash
cd /Users/admin/Desktop/chess-39-project/backend
python3 -m alembic upgrade head
```

---

## Testing Methods

### Method 1: Interactive API Documentation (Recommended for Manual Testing)

**URL:** http://localhost:8000/docs

This Swagger UI allows you to:
- See all available endpoints
- Try endpoints directly in the browser
- View request/response schemas

### Method 2: Command Line (curl)

Good for automated testing and scripts.

### Method 3: Postman/Insomnia

Import the OpenAPI spec from http://localhost:8000/openapi.json

---

## Test Scenarios

### Scenario 1: User Registration & Authentication

#### Step 1.1: Create First User (Alice)

**Endpoint:** `POST /api/auth/signup`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@chess39.com",
    "password": "SecurePass123"
  }'
```

**Expected Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**⚠️ Save this token!** You'll need it for authenticated requests.

#### Step 1.2: Create Second User (Bob)

Repeat with different credentials:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob",
    "email": "bob@chess39.com",
    "password": "SecurePass456"
  }'
```

#### Step 1.3: Login

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@chess39.com&password=SecurePass123"
```

**Note:** The `username` field actually expects the email address (OAuth2 standard).

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Step 1.4: Get Current User Profile

**Endpoint:** `GET /api/auth/me-info`

**Request:**
```bash
curl http://localhost:8000/api/auth/me-info \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@chess39.com",
  "elo_rating": 1200,
  "games_played": 0,
  "wins": 0,
  "losses": 0,
  "draws": 0,
  "created_at": "2025-11-28T10:00:00",
  "last_login": "2025-11-28T10:05:00"
}
```

**✅ Test Passed If:**
- Status code is 200
- Response contains user data
- ELO rating starts at 1200
- Games/wins/losses/draws are all 0

---

### Scenario 2: Game Creation

#### Step 2.1: Get Alice's User ID

Use the `/api/auth/me-info` endpoint (as shown above) and copy Alice's `id`.

#### Step 2.2: Create a Game (Bob challenges Alice)

**Endpoint:** `POST /api/games`

**Request:**
```bash
curl -X POST http://localhost:8000/api/games \
  -H "Authorization: Bearer BOBS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "opponent_id": "ALICE_USER_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "id": "game-uuid-here",
  "white_player": {
    "id": "...",
    "username": "alice",
    "elo_rating": 1200
  },
  "black_player": {
    "id": "...",
    "username": "bob",
    "elo_rating": 1200
  },
  "board": {
    "a1": ["ROOK", "white"],
    "a2": ["PAWN", "white"],
    ...
  },
  "current_turn": "white",
  "status": "ongoing",
  "moves": [],
  "created_at": "2025-11-28T10:10:00"
}
```

**✅ Test Passed If:**
- Status code is 201
- Both players are assigned
- `board` contains pieces (random Chess 39 army)
- `status` is "ongoing"
- `current_turn` is "white"

**⚠️ Save the game `id`!** You'll need it to make moves.

#### Step 2.3: Verify Random Army Generation

Count the total point value of white's pieces (excluding King):
- Each Pawn = 1 point
- Each Knight = 3 points
- Each Bishop = 3 points
- Each Rook = 5 points
- Each Queen = 9 points

**Total should equal 39 points** ✅

---

### Scenario 3: Making Moves

#### Step 3.1: Make White's First Move

Let's say white has a pawn on e2. Move it to e4.

**Endpoint:** `POST /api/games/{game_id}/move`

**Request:**
```bash
curl -X POST http://localhost:8000/api/games/GAME_ID_HERE/move \
  -H "Authorization: Bearer ALICES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_square": "e2",
    "to_square": "e4"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Move successful",
  "captured": null,
  "is_check": false,
  "is_checkmate": false,
  "status": "ongoing"
}
```

#### Step 3.2: Try an Invalid Move

**Request:**
```bash
curl -X POST http://localhost:8000/api/games/GAME_ID_HERE/move \
  -H "Authorization: Bearer ALICES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_square": "e4",
    "to_square": "e6"
  }'
```

**Expected Response:**
```json
{
  "success": false,
  "message": "Not your turn",
  "status": "ongoing"
}
```

**✅ Test Passed If:** Invalid moves are rejected with appropriate error messages.

#### Step 3.3: Make Black's Move

**Request:**
```bash
curl -X POST http://localhost:8000/api/games/GAME_ID_HERE/move \
  -H "Authorization: Bearer BOBS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_square": "e7",
    "to_square": "e5"
  }'
```

---

### Scenario 4: Game State Retrieval

#### Step 4.1: Get Current Game State

**Endpoint:** `GET /api/games/{game_id}`

**Request:**
```bash
curl http://localhost:8000/api/games/GAME_ID_HERE \
  -H "Authorization: Bearer ALICES_TOKEN"
```

**Expected Response:**
Full game state with updated board and move history.

#### Step 4.2: List User's Games

**Endpoint:** `GET /api/games`

**Request:**
```bash
curl "http://localhost:8000/api/games?status=ongoing&limit=10" \
  -H "Authorization: Bearer ALICES_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": "game-uuid",
    "white_player": {...},
    "black_player": {...},
    "status": "ongoing",
    "created_at": "..."
  }
]
```

---

### Scenario 5: Game Resignation

**Endpoint:** `POST /api/games/{game_id}/resign`

**Request:**
```bash
curl -X POST http://localhost:8000/api/games/GAME_ID_HERE/resign \
  -H "Authorization: Bearer ALICES_TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Resignation accepted",
  "winner": "black"
}
```

**✅ Test Passed If:**
- Game status changes to "resignation"
- Winner is set correctly
- ELO ratings are updated for both players

---

## Common Test Cases

### Authentication Tests

| Test Case | Expected Result |
|-----------|----------------|
| Signup with existing email | 400 error: "Email already registered" |
| Signup with existing username | 400 error: "Username already registered" |
| Login with wrong password | 401 error: "Incorrect email or password" |
| Access protected endpoint without token | 401 error: "Not authenticated" |
| Access protected endpoint with invalid token | 401 error: "Could not validate credentials" |

### Game Logic Tests

| Test Case | Expected Result |
|-----------|----------------|
| Move opponent's piece | Error: "Cannot move opponent's piece" |
| Make move when not your turn | Error: "Not your turn" |
| Move to square occupied by own piece | Error: "Invalid move" |
| Move piece off the board | Error: "Invalid move" |
| Promote pawn (reach end rank) | Success, piece promoted to Queen (or specified piece) |
| Castle when path blocked | Error: "Invalid move" |
| Move king into check | Error: "Move would leave king in check" |

### Edge Cases

| Test Case | Expected Result |
|-----------|----------------|
| Create game with non-existent opponent | 404 error: "Opponent not found" |
| Make move in completed game | Error: "Game is checkmate/stalemate/resignation" |
| Get game that doesn't exist | 404 error: "Game not found" |

---

## Automated Testing Script

```bash
#!/bin/bash
# Simple automated test script

BASE_URL="http://localhost:8000"

echo "Test 1: Health Check"
curl $BASE_URL/health
echo "\n"

echo "Test 2: Create User"
RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"test123"}')

TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: $TOKEN"
echo "\n"

echo "Test 3: Get Profile"
curl -s $BASE_URL/api/auth/me-info \
  -H "Authorization: Bearer $TOKEN"
echo "\n"

echo "All tests complete!"
```

---

## Troubleshooting

### Server Not Starting

**Problem:** `ImportError` or `ModuleNotFoundError`

**Solution:**
```bash
cd backend
pip3 install -r requirements.txt
```

### Database Connection Error

**Problem:** `sqlalchemy.exc.OperationalError`

**Solution:**
```bash
# Check Docker is running
docker compose ps

# Restart containers
docker compose down
docker compose up -d

# Rerun migrations
python3 -m alembic upgrade head
```

### bcrypt Error

**Problem:** `ValueError: password cannot be longer than 72 bytes`

**Solution:**
```bash
pip3 install bcrypt --upgrade
# OR use shorter passwords for testing
```

### 401 Unauthorized Errors

**Problem:** Token expired or invalid

**Solution:**
```bash
# Login again to get a fresh token
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=your@email.com&password=yourpassword"
```

---

## Performance Benchmarks

Expected response times (on local machine):
- Signup: < 500ms
- Login: < 200ms
- Get game state: < 50ms (cached), < 200ms (from DB)
- Make move: < 100ms

---

## Security Checklist

- [ ] All endpoints require authentication (except signup/login)
- [ ] Passwords are hashed (never stored in plain text)
- [ ] JWT tokens expire after 60 minutes
- [ ] Users can only access their own games
- [ ] Move validation prevents cheating

---

## Next Steps

After all tests pass:
1. Test WebSocket real-time updates
2. Load test with multiple concurrent users
3. Test game completion and ELO calculation
4. Verify game history persistence

---

**Last Updated:** November 2025  
**For Support:** Check server logs in terminal where uvicorn is running
