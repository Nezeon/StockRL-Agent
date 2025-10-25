# 📊 Agent Training Monitoring Guide

## Overview

This guide explains how to view real-time training progress on the dashboard.

## ✅ What Was Fixed

1. **Backend WebSocket Broadcasting** - Added `broadcast_agent_metric()` calls in `agent_manager.py`
2. **Frontend RewardChart** - Fixed message type from `agent_stat` to `agent_metric`
3. **AgentMonitor WebSocket** - Added real-time updates to the monitor page
4. **Message Format** - Aligned frontend expectations with backend broadcasts

## 🎯 How to View Training Progress

### Method 1: Dashboard View (Quick Overview)

1. **Open** `http://localhost:3000` in your browser
2. **Login** with:
   - Username: `Ayushmaan`
   - Password: `demo123`
3. **Dashboard shows**:
   - Portfolio card (top-left)
   - RewardChart (when agent is running)
   - Real-time metrics updating every few seconds

### Method 2: Agent Monitor Page (Detailed View)

1. **Start an agent** from the Dashboard
2. **Navigate to**: `http://localhost:3000/agent/monitor/{agent_run_id}`
   - Or click "View Details" button
3. **You'll see**:
   - Real-time reward chart
   - Step counter
   - Cumulative reward
   - Portfolio NAV
   - Episode rewards
   - Training statistics

## 📈 What You'll See

### Real-Time Updates

- **Step counter** - Increases as agent takes actions
- **Reward values** - Updates with each episode
- **NAV (Net Asset Value)** - Portfolio value changes
- **Chart line** - Growing chart showing training progress
- **Status** - Running/Stopped indicator

### WebSocket Channels

The frontend automatically subscribes to:

- `agent_stats:{agent_run_id}` - Training metrics
- `portfolio_updates:{portfolio_id}` - Portfolio changes
- `trade_executed:{portfolio_id}` - Trade notifications

## 🔧 Technical Details

### Backend Broadcasting

File: `backend/app/services/agent_manager.py`

```python
# In _log_metric() method
from app.api.websocket import broadcast_agent_metric
await broadcast_agent_metric(agent_run_id, {
    "step": step,
    "episode_reward": float(reward),
    "cumulative_reward": float(cumulative_reward),
    "portfolio_nav": float(nav)
})
```

### Frontend Subscription

File: `frontend/src/components/RewardChart.tsx`

```typescript
const { subscribe } = useWebSocket(WS_URL, {
  onMessage: (message) => {
    if (message.type === "agent_metric") {
      // Update chart with new data
    }
  },
});
subscribe(`agent_stats:${agentRunId}`);
```

## 🐛 Troubleshooting

### No Updates Appearing?

1. **Check WebSocket Connection**

   - Open Browser DevTools (F12)
   - Go to **Console** tab
   - Look for: `WebSocket message:` logs
   - Should see messages every few seconds

2. **Check Network Tab**

   - Go to **Network** tab in DevTools
   - Filter by **WS** (WebSocket)
   - Should see active connection to `ws://localhost:8000/ws`

3. **Verify Agent is Running**

   ```bash
   # Check active agents
   curl http://localhost:8000/api/v1/agent/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Check Backend Logs**

   - Look at the terminal where backend is running
   - Should see training episodes logging

5. **Refresh the Page**
   - Sometimes a hard refresh (Ctrl+Shift+R) helps
   - WebSocket will reconnect automatically

### Common Issues

**Issue**: Chart shows "Training starting..."

- **Cause**: No metrics logged yet
- **Solution**: Wait a few seconds for first episode to complete

**Issue**: WebSocket disconnects frequently

- **Cause**: Network issues or backend restart
- **Solution**: Frontend auto-reconnects, just wait

**Issue**: Old data showing

- **Cause**: Cache or stale state
- **Solution**: Hard refresh browser (Ctrl+Shift+R)

## 🚀 Quick Start

```bash
# 1. Ensure backend is running
cd backend
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Ensure frontend is running
cd frontend
npm run dev

# 3. Open browser
http://localhost:3000

# 4. Start an agent and watch the magic! ✨
```

## 📋 Checklist

Before viewing training:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Logged into frontend
- [ ] Portfolio created
- [ ] Agent started
- [ ] Browser DevTools open (to see logs)

## 🎓 Understanding the Metrics

- **Step**: Number of actions taken by the agent
- **Episode Reward**: Reward earned in current episode
- **Cumulative Reward**: Total reward across all episodes
- **NAV**: Current portfolio value (cash + positions)
- **Loss**: Training loss (how well agent is learning)

## 🔗 Useful URLs

- **Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

---

**All set! Your training metrics are now streaming in real-time! 🎉**
