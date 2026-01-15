# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📊 Current Project Status

**Backend: ✅ Complete**
- FastAPI backend is fully implemented and functional
- PostgreSQL database integration with SQLAlchemy ORM
- Redis caching and pub/sub messaging
- JWT authentication system
- Game logic with chess39-core module
- ELO rating system
- Database migrations with Alembic
- Deployed to AWS Elastic Beanstalk with GitHub auto-deployment
- All API endpoints tested and working

**Frontend: ⏳ Not Started**
- Frontend development has not yet begun
- Planned tech stack: Next.js (to be discussed with Harel)
- Will connect to the existing backend API
- When starting frontend work, remember the learning philosophy below - use GUI tools and explain each step

**Next Steps**: Ready to begin frontend development when Harel decides to start.

## 🎓 Learning Philosophy

**This is Harel's first software project - prioritize education over efficiency.**

### Core Principles:
1. **Explain Every Step**: Don't just execute commands - explain what they do, why they're necessary, and what happens behind the scenes
2. **Present Options**: When there are multiple approaches, present 2-3 alternatives with trade-offs so Harel can make informed decisions and expand his knowledge
3. **GUI Over CLI for Infrastructure**: For tools like AWS, Docker Desktop, database management - guide Harel to use the graphical interface so he can see all available options and understand what's being configured. Terminal commands hide the learning opportunity.
4. **Learning > Speed**: Take time to explain concepts. Avoid "just run this" without context.

### Examples:
- ❌ "Run `docker compose up -d`"
- ✅ "Let's start the database. We have two options: (1) Use Docker Desktop's GUI where you can see containers, logs, and resource usage, or (2) Use `docker compose up -d` command. I recommend Docker Desktop for learning because..."

- ❌ "Deploy to AWS with this CLI command"
- ✅ "Let's deploy to AWS Elastic Beanstalk. Open the AWS Console so you can see the deployment options, environment settings, and monitoring dashboards. This way you'll understand..."

## Project Overview

Chess 39 is an online chess platform where players start with random armies worth exactly 39 points instead of standard chess pieces. The backend is a FastAPI application with PostgreSQL for persistence and Redis for caching/pub-sub.

## Common Commands

### Development Setup

**Note**: When possible, guide Harel to use graphical interfaces (Docker Desktop, database GUIs) to see what these commands do visually.

```bash
# Start PostgreSQL and Redis containers
# What it does: Starts two Docker containers in background (-d = detached mode)
# Alternative: Use Docker Desktop GUI - you can see container status, logs, resource usage
docker compose up -d

# Create and activate virtual environment
# Why: Isolates Python packages for this project from system packages
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
# What it does: Downloads and installs all Python packages listed in requirements.txt
pip install -r requirements.txt

# Run database migrations
# What it does: Creates/updates database tables to match SQLAlchemy models
# Explain: Alembic tracks database schema versions - like Git for your database structure
python3 -m alembic upgrade head

# Start development server (auto-reloads on changes)
# --reload: Automatically restarts server when you save code changes
# --host 0.0.0.0: Makes server accessible from other devices on network
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run chess core tests
python3 chess39-core/test_core.py

# Run pytest tests (if available)
pytest

# Test specific file
pytest path/to/test_file.py
```

### Database Migrations
```bash
# Create a new migration after model changes
python3 -m alembic revision --autogenerate -m "description of changes"

# Apply migrations
python3 -m alembic upgrade head

# Revert last migration
python3 -m alembic downgrade -1
```

### API Testing
```bash
# Interactive API documentation (Swagger UI)
# After starting server, visit: http://localhost:8000/docs
# This is a web interface where you can test all endpoints visually!

# Health check
curl http://localhost:8000/health
```

### Recommended GUI Tools for Learning

**Instead of CLI commands, use these visual tools:**

1. **Docker Desktop** (https://www.docker.com/products/docker-desktop/)
   - See all containers, images, volumes visually
   - View real-time logs, resource usage
   - Start/stop containers with clicks
   - Alternative to: `docker compose up/down`, `docker ps`, `docker logs`

2. **pgAdmin or DBeaver** (Database GUI)
   - Browse tables, view data visually
   - Run SQL queries with autocomplete
   - See table relationships and schemas
   - Alternative to: `psql` command-line tool

3. **Redis Insight** (https://redis.io/insight/)
   - View cached data in Redis
   - Monitor pub/sub channels
   - See memory usage and key expirations
   - Alternative to: `redis-cli` commands

4. **Postman or Insomnia** (API Testing)
   - Test API endpoints with nice UI
   - Save request collections
   - See formatted JSON responses
   - Alternative to: `curl` commands (but Swagger UI at `/docs` works great too!)

**Why GUI tools?**
- See what's happening under the hood
- Explore features you didn't know existed
- Build mental models of how systems work
- Learn by clicking and exploring

## Architecture

### Three-Layer Architecture

**1. API Layer** (`app/api/routes/`)
- `auth.py`: User signup, login, JWT token management
- `games.py`: Game creation, move submission, game queries
- Routes are thin - they validate input and delegate to services

**2. Service Layer** (`app/services/`)
- `game_service.py`: Core business logic for game management
  - Integrates chess39-core with database and cache
  - Handles game creation, move processing, ELO updates
- `redis_client.py`: Cache operations and pub/sub messaging

**3. Data Layer** (`app/db/`)
- `models.py`: SQLAlchemy ORM models (User, GameModel, Move)
- `database.py`: Database connection and session management

### Chess39-Core Module

The `chess39-core/` directory is a standalone Python module containing pure game logic:
- `game.py`: Game class managing state, move validation, check/checkmate detection
- `board.py`: Board representation and piece placement
- `pieces.py`: Piece types and movement rules (PieceType enum)
- `army.py`: Random army generation (exactly 39 points, max 8 pawns)
- `fen.py`: FEN notation parsing/generation

**Important**: chess39-core is imported by adding it to sys.path in `game_service.py:13-14`. It has no dependencies on the FastAPI backend.

### Data Flow for Moves

1. Client sends move request to `POST /api/games/{id}/move`
2. Route extracts JWT token, validates user
3. Route calls `game_service.make_move()`
4. Service loads game from Redis cache (or PostgreSQL fallback)
5. Service calls chess39-core's `game.make_move()` for validation
6. If valid: Update PostgreSQL, update Redis cache, publish to Redis pub/sub
7. Response returned to client with updated game state

### Caching Strategy

- **Hot Path**: Active games cached in Redis (24-hour TTL)
- **Cold Path**: Inactive games loaded from PostgreSQL, then cached
- Game state stored as JSON in both database and cache
- Redis pub/sub used for real-time move broadcasting

## Key Technical Decisions

**When discussing these topics, explain WHY each choice was made and what alternatives exist.**

### Authentication
**Current approach**: JWT tokens with 60-minute expiration
- **Why JWT?** Stateless authentication - server doesn't need to store sessions in database
- **Alternative**: Session cookies stored in Redis (more secure but requires storage)
- **Trade-off**: JWTs can't be revoked before expiration; sessions can be deleted instantly

**Password hashing**: bcrypt
- **Why bcrypt?** Industry standard, automatically salted, computationally expensive (slows down attackers)
- **Alternative**: argon2 (more modern, won a competition), scrypt
- **Important**: Never store plain text passwords - hashing is one-way encryption

### Game State Storage
**Dual storage approach**:
- Initial setup in `GameModel.initial_setup_json` (never changes)
- Current state in `GameModel.current_state_json` (updated after each move)
- Every move in `Move` table for complete history

**Why JSON in database?**
- Flexible - board state structure can evolve without migrations
- **Alternative**: Separate tables for pieces and positions (more normalized, harder to query)
- **Trade-off**: JSON is less structured but easier to work with for complex game state

### ELO Rating System
**Standard ELO calculation with K=32**
- **Why K=32?** Standard for chess - determines how much ratings change per game
- **Higher K** (like 64): Ratings change faster, more volatile
- **Lower K** (like 16): Ratings change slower, more stable
- All players start at 1200 ELO (arbitrary middle point)

### Server-Authoritative Design
**All validation happens server-side**
- **Why?** Prevents cheating - client sends "move request", not "update game state"
- **Alternative**: Client-side validation (faster UI feedback but can be hacked)
- **Trade-off**: Extra network round-trip for validation, but security is worth it

## Configuration

### Environment Variables (.env)
```
DATABASE_URL=postgresql://chess39:chess39@localhost:5432/chess39
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Copy `.env.example` to `.env` and update values as needed.

### CORS Settings
Default CORS origin is `http://localhost:3000` (configured in `app/core/config.py:24`). Update `settings.CORS_ORIGINS` for production.

## Important Patterns

**When explaining code, describe WHAT it does, WHY it's needed, and WHAT alternatives exist.**

### Import Path Handling
**Pattern**: chess39-core modules use try/except for imports
```python
try:
    from pieces import PieceType  # Standalone execution
except ImportError:
    from .pieces import PieceType  # Package import (when imported by backend)
```

**Why needed?**
- Makes chess39-core work both as standalone module (`python3 chess39-core/game.py`) and when imported by backend
- **Alternative**: Always use relative imports, but then standalone execution breaks
- **Trade-off**: Slight complexity for maximum flexibility

### Dependency Injection
**Pattern**: FastAPI automatically provides dependencies
```python
def endpoint(db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    # db session and authenticated user automatically injected
    # No need to manually create connections or parse JWT tokens
```

**Why use this?**
- Cleaner code - business logic separate from boilerplate
- Automatic cleanup - database sessions close after request
- Reusable - authentication logic in one place
- **Alternative**: Manually create db sessions and parse tokens in each endpoint
- **FastAPI magic**: Runs `get_db()` and `get_current_user()` before your function, passes results as parameters

### Error Handling
**Pattern**: Raise HTTPException for API errors
```python
if not game:
    raise HTTPException(status_code=404, detail="Game not found")
```

**Why this way?**
- FastAPI automatically converts to proper HTTP response with correct status code
- Client receives JSON: `{"detail": "Game not found"}`
- **Alternative**: Return dict with error, but HTTP status would be 200 (wrong!)
- **HTTP status codes**: 404 = Not Found, 401 = Unauthorized, 400 = Bad Request, 500 = Server Error

## Code Review Approach

When reviewing or writing code with Harel:
1. **Explain the problem** being solved
2. **Show the solution** with code
3. **Explain why this solution** (what makes it good?)
4. **Mention alternatives** (what else could we do?)
5. **Discuss trade-offs** (when would we choose differently?)

Example: "We're using SQLAlchemy ORM instead of raw SQL because it prevents SQL injection and makes code more readable. The trade-off is a small performance cost, but security and maintainability are more important for this project."

## Repository Structure

This is a monorepo with backend at root level (Elastic Beanstalk convention):
- Root directory contains backend Python code
- `frontend/` directory is a placeholder for future Next.js frontend
- `chess39-core/` is a standalone module shared by both backend and (future) frontend

## Common Gotchas

1. **chess39-core imports**: After restructuring, chess39-core is at root level, not in backend/. Path manipulation in `game_service.py:13-14` is required.

2. **Database sessions**: Always use FastAPI's `Depends(get_db)` to get sessions - they auto-close after requests.

3. **Redis connection**: Redis must be running for the app to start. Use `docker compose up -d` to start services.

4. **Alembic migrations**: Database schema changes require creating and applying Alembic migrations - don't modify tables directly.

5. **UUID types**: User IDs and Game IDs are UUIDs, not integers. Import from `uuid` module.

## Deployment

**IMPORTANT**: Always guide Harel to use the AWS Console (web interface) rather than AWS CLI commands.

Application is configured for AWS Elastic Beanstalk:
- `Procfile`: Tells EB how to run the application (`uvicorn app.main:app`)
- `.ebextensions/`: Configuration files for EB environment setup
- Root-level structure matches EB expectations (backend files at root, not in subdirectory)

**Deployment approach**:
1. Open AWS Elastic Beanstalk Console in browser
2. Walk through the GUI options together - explain environment types, instance sizes, scaling options
3. Show how to monitor deployments, view logs, configure environment variables
4. Let Harel see and understand each setting rather than running blind CLI commands

**Why GUI over CLI?**
- See all available options and settings
- Understand what's being configured
- Learn AWS interface that transfers to other services
- Can explore without breaking anything

For local development, use uvicorn directly with `--reload` flag.

## When to Present Options

Present 2-3 alternatives with trade-offs in these situations:
- **Architecture decisions**: "We could structure this as X, Y, or Z..."
- **Library choices**: "For authentication, we could use..."
- **Design patterns**: "There are several ways to handle this..."
- **Deployment strategies**: "We can deploy to..."

### Example Format:
```
We need to handle [problem]. Here are the main approaches:

**Option 1: [Name]**
- How it works: ...
- Pros: ...
- Cons: ...
- Best for: ...

**Option 2: [Name]**
- How it works: ...
- Pros: ...
- Cons: ...
- Best for: ...

My recommendation: [Option X] because [reason], but [Option Y] would also work well if [condition].

What would you like to do?
```
