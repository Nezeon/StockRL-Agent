# StockRL-Agent

**Autonomous RL-powered stock trading simulator** with web dashboard, reinforcement learning agents, and paper trading capabilities.

A modular, production-minded application that uses reinforcement learning to autonomously analyze live stock data and make buy/sell/hold decisions for user portfolios.

## Features

### 🤖 Reinforcement Learning

- **Custom PPO Agent**: Full PyTorch implementation with GAE and clipped objective
- **DQN & A2C**: Skeleton implementations for discrete/continuous action spaces
- **Modular Design**: Easy to swap algorithms or add new ones
- **Realistic Environment**: Trading simulation with slippage, fees, and risk profiles

### 📊 Trading Simulator

- **Paper Trading**: Simulated order execution with realistic market impact
- **Risk Profiles**: Conservative, Moderate, Aggressive (different fee structures)
- **Slippage Model**: Market impact based on order size
- **Multi-Asset Support**: Trade multiple tickers simultaneously

### 📈 Data Providers

- **Mock Provider**: Realistic synthetic data (no API keys needed)
- **Yahoo Finance**: Free real-time market data
- **Alpha Vantage**: Premium intraday data
- **Finnhub**: Alternative data source
- **Easy Switching**: Change providers via configuration

### 🎯 Backend Features

- **FastAPI**: Modern async Python web framework
- **PostgreSQL/SQLite**: Flexible database support
- **JWT Authentication**: Secure user sessions
- **WebSocket**: Real-time portfolio and agent updates
- **REST API**: Complete CRUD operations for portfolios, trades, agents

### 🔧 Developer Experience

- **Docker Compose**: One-command deployment
- **Alembic Migrations**: Database version control
- **Type Safety**: Full type hints and Pydantic validation
- **Demo Mode**: Pre-seeded data for instant testing
- **Comprehensive Logging**: Track agent training and trading

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
cd StockRL-Agent

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access API
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

**Demo credentials:**
- Username: `demo`
- Password: `demo123`

### Option 2: Local Development

```bash
# Run setup script
./scripts/run_local.sh

# Or manually:
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Create demo data
python ../scripts/create_demo_user.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  Dashboard │ Portfolio Settings │ Agent Control │ Trade Log  │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────┴─────────────────────────────────────┐
│                     Backend (FastAPI)                        │
├──────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ├─ Auth (JWT)                                              │
│  ├─ Portfolios (CRUD)                                       │
│  ├─ Trades (History)                                        │
│  ├─ Agent Control (Start/Stop)                             │
│  └─ Market Data (Quotes, Historical)                       │
├──────────────────────────────────────────────────────────────┤
│  Services Layer                                              │
│  ├─ Portfolio Service (NAV calculation, metrics)           │
│  ├─ Agent Manager (Training, Live trading)                 │
│  └─ Data Provider Registry                                  │
├──────────────────────────────────────────────────────────────┤
│  RL Framework                                                │
│  ├─ Trading Environment (Gym-like)                         │
│  ├─ Agents (PPO, DQN, A2C)                                 │
│  ├─ Observation Builder                                     │
│  └─ Reward Function                                         │
├──────────────────────────────────────────────────────────────┤
│  Trading Simulator                                           │
│  ├─ Order Executor                                          │
│  ├─ Slippage Model                                          │
│  └─ Fee Calculator                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│         Data Providers │ Database │ WebSocket Manager       │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
StockRL-Agent/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # REST + WebSocket endpoints
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── data_providers/    # Market data adapters
│   │   ├── rl_agents/         # Reinforcement learning
│   │   ├── simulator/         # Paper trading execution
│   │   ├── services/          # Business logic
│   │   └── db/                # Database session & migrations
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile
├── scripts/                   # Utility scripts
│   ├── create_demo_user.py   # Seed demo data
│   └── run_local.sh          # Local development setup
├── docker-compose.yml         # Full stack orchestration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## API Documentation

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "username": "user1",
  "email": "user1@example.com",
  "password": "secure123"
}

# Login
POST /api/v1/auth/login
{
  "username": "user1",
  "password": "secure123"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

### Portfolios

```bash
# List portfolios
GET /api/v1/portfolios
Authorization: Bearer <token>

# Create portfolio
POST /api/v1/portfolios
{
  "name": "My Portfolio",
  "initial_budget": 10000,
  "tickers": ["AAPL", "GOOGL", "MSFT"],
  "risk_profile": "moderate"
}

# Get portfolio details
GET /api/v1/portfolios/{id}

# Update portfolio
PATCH /api/v1/portfolios/{id}
{
  "name": "Updated Name",
  "is_active": true
}
```

### Agent Control

```bash
# Start agent training
POST /api/v1/agent/start
{
  "portfolio_id": "uuid",
  "algorithm": "PPO",
  "mode": "train",
  "action_space_type": "continuous",
  "hyperparameters": {
    "learning_rate": 0.0003,
    "batch_size": 64,
    "episodes": 100
  }
}

# Get agent status
GET /api/v1/agent/status?portfolio_id=<uuid>

# Stop agent
POST /api/v1/agent/stop
{
  "agent_run_id": "uuid"
}

# Get agent statistics
GET /api/v1/agent/{agent_run_id}/stats?limit=1000
```

### Market Data

```bash
# Get quote
GET /api/v1/market/ticker/AAPL/quote

# Get historical data
GET /api/v1/market/ticker/AAPL/history?start_date=2024-01-01&interval=1d
```

### WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?channel=portfolio_updates:uuid');

// Subscribe to channels
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'agent_stats:agent_run_id'
}));

// Receive messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data);
};
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/stockrl
# For SQLite: DATABASE_URL=sqlite+aiosqlite:///./stockrl.db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-min-32-chars-change-in-production

# Data Provider
DATA_MODE=demo              # demo or live
DATA_PROVIDER=mock          # mock, yahoo, alphavantage, finnhub
DATA_FETCH_INTERVAL_SECONDS=60

# API Keys (only if DATA_MODE=live)
ALPHA_VANTAGE_KEY=your-key
FINNHUB_KEY=your-key

# Application
DEBUG=false
```

### Switching Data Providers

```python
# In .env
DATA_PROVIDER=yahoo         # Use Yahoo Finance
DATA_PROVIDER=alphavantage  # Use Alpha Vantage (requires API key)
DATA_PROVIDER=mock          # Use mock data (no internet required)
```

### Changing RL Algorithms

When starting an agent, specify the algorithm:

```json
{
  "algorithm": "PPO",  // or "DQN", "A2C"
  "action_space_type": "continuous"  // or "discrete"
}
```

## Development

### Running Tests

```bash
cd backend
pytest                          # Run all tests
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests
pytest --cov=app --cov-report=html  # With coverage
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Linting & Type Checking

```bash
# Linting
ruff check app/

# Type checking
mypy app/

# Formatting
black app/
```

## Deployment

### Production Considerations

1. **Change SECRET_KEY**: Use a strong random string
2. **Use PostgreSQL**: Not SQLite for production
3. **Enable HTTPS**: Use reverse proxy (nginx/traefik)
4. **Set Rate Limits**: Protect API endpoints
5. **Use Production DB**: Managed PostgreSQL (AWS RDS, etc.)
6. **Monitor Logs**: Set up centralized logging
7. **Backup Database**: Regular automated backups

### Environment Variables for Production

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@prod-host:5432/stockrl
SECRET_KEY=<generated-with-openssl-rand-hex-32>
DATA_MODE=live
DATA_PROVIDER=yahoo
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
```

## Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Ensure you're in virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**"Database connection failed"**
```bash
# Check DATABASE_URL in .env
# For local dev, use SQLite:
DATABASE_URL=sqlite+aiosqlite:///./stockrl.db
```

**"API key required" errors**
```bash
# Either use mock provider
DATA_PROVIDER=mock

# Or add API key
ALPHA_VANTAGE_KEY=your-key-here
```

**Agent training not starting**
```bash
# Check logs
docker-compose logs -f backend

# Verify portfolio exists and is active
# Check database for agent_runs table
```

## RL Agent Details

### Observation Space

The agent receives:
1. **Portfolio State**: Cash ratio, position ratios, unrealized P&L
2. **Market Data**: Last 30 timesteps of OHLCV (normalized)
3. **Technical Indicators**: SMA, RSI, MACD, Bollinger Bands

Total dimension: ~389 features for 4-ticker portfolio

### Action Space

**Discrete** (for DQN):
- Actions per ticker: HOLD (0), BUY (1), SELL (2)
- Total actions: 3^N where N is number of tickers

**Continuous** (for PPO):
- One value per ticker in [-1, 1]
- Negative = SELL, Positive = BUY, Near zero = HOLD

### Reward Function

```
reward = NAV_change - transaction_costs - risk_penalty - drawdown_penalty
```

- **NAV Change**: Primary signal (portfolio value change)
- **Transaction Costs**: Discourages overtrading
- **Risk Penalty**: Based on volatility (adjusted by risk profile)
- **Drawdown Penalty**: Encourages capital preservation

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

- **Documentation**: See `/docs` folder
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: GitHub Issues

## Roadmap

- [ ] Frontend React dashboard
- [ ] Advanced technical indicators (more TA features)
- [ ] Multi-timeframe analysis
- [ ] Backtesting module with historical replay
- [ ] Risk management rules (stop-loss, position limits)
- [ ] Real broker integration (Alpaca, Interactive Brokers)
- [ ] Portfolio optimization algorithms
- [ ] Sentiment analysis integration
- [ ] Mobile app

---

**⚠️ Disclaimer**: This is a paper trading simulator for educational purposes. Do not use for live trading without proper testing, risk management, and understanding of financial markets.
