# 🔧 Switching from Demo Mode to Real Data

The dashboard currently shows **DEMO MODE** with simulated data. Here's how to use real ML predictions:

---

## ✅ What's Fixed

I've just fixed these issues:

1. ✅ **Chart rendering** - No more weird expanding
2. ✅ **Chart sizing** - Fixed at proper 400px height
3. ✅ **Better mock data** - More realistic price movements
4. ✅ **Demo mode indicator** - Clear badge showing it's demo data
5. ✅ **Improved data generation** - Realistic trends instead of random

---

## 🎯 Current Status: DEMO MODE

**What you're seeing:**
- ✅ Stock prices: Simulated but realistic
- ✅ AI predictions: Random (50-90% confidence)
- ✅ Charts: Generated with realistic trends
- ✅ Technical indicators: Random values
- ✅ Everything works: Just not real data yet!

**Demo mode is PERFECT for:**
- Testing the interface
- Seeing how it works
- Showing to others
- Mobile testing
- Understanding the features

---

## 🚀 How to Use REAL Data

### Option 1: Quick Setup (5 minutes)

**Step 1: Get Alpaca API Keys (Free)**

1. Go to: https://alpaca.markets
2. Sign up for free paper trading account
3. Get your API keys from dashboard
4. Copy `API Key` and `Secret Key`

**Step 2: Configure Backend**

```bash
# In your project folder
cp .env.example .env

# Edit .env file and add your keys:
nano .env
```

Add these lines:
```bash
ALPACA_API_KEY=your-api-key-here
ALPACA_SECRET_KEY=your-secret-key-here
ALPACA_PAPER_TRADING=true
```

**Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Step 4: Start Backend API**

```bash
python api_server.py
```

You should see:
```
🚀 ML Trading System Frontend Server
✅ Server running successfully!
API: http://localhost:5000
```

**Step 5: Enable Real Data in Frontend**

Edit `docs/app.js` or `frontend/app.js`:

```javascript
// Change this line from:
const DEMO_MODE = true;

// To:
const DEMO_MODE = false;
```

**Step 6: Refresh Dashboard**

- Reload the page
- Demo mode badge disappears
- Real predictions start working! 🎉

---

### Option 2: Keep Demo Mode (Current Setup)

**If you want to keep demo mode:**
- ✅ No setup needed
- ✅ Works immediately
- ✅ Perfect for presentations
- ✅ No API keys required
- ✅ Great for testing interface

Just use it as-is! The demo data is now much more realistic.

---

## 📊 What Changes with Real Data

### DEMO MODE (Current):
- Stock prices: Simulated
- Predictions: Random
- Confidence: Random (50-90%)
- Technical indicators: Random values
- Speed: Instant
- Cost: Free

### REAL MODE:
- Stock prices: Live from Alpaca API
- Predictions: ML ensemble models (RF + GB + XGBoost)
- Confidence: Actual model probability
- Technical indicators: Real RSI, MACD, Bollinger Bands
- Speed: 2-3 seconds (model training)
- Cost: Free (Alpaca paper trading)

---

## 🔍 How to Tell if Real Data is Working

When you switch to real mode, you'll see:

1. **Demo badge disappears** ✅
2. **Longer loading time** (2-3 seconds for ML)
3. **Console logs** showing "Training model for AAPL..."
4. **Real stock prices** matching current market
5. **Different predictions** each time (based on real patterns)

---

## ⚙️ Backend API Endpoints

When backend is running, you can test:

```bash
# Health check
curl http://localhost:5000/health

# Get prediction (requires auth token)
curl -X POST http://localhost:5000/api/v1/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"symbol": "AAPL", "api_key": "...", "secret_key": "..."}'
```

---

## 🎨 Demo Mode Features (Already Working!)

The fixes I made improve demo mode:

**Before:**
- ❌ Chart expanding weirdly
- ❌ Random/unrealistic prices
- ❌ Confusing if it's real or demo
- ❌ Charts jumping around

**After:**
- ✅ Chart fixed at 400px
- ✅ Realistic price trends
- ✅ Clear "DEMO MODE" badge
- ✅ Smooth, stable charts
- ✅ Better mock data

---

## 📱 Your GitHub Pages Site

Your site is live at (or will be after you save /docs folder):
```
https://rrasc.github.io/predictionmlstock/
```

**It will always be in DEMO MODE for public viewers** (for security).

To use real data:
- Run locally with backend
- Or deploy backend to cloud (AWS, Heroku, etc.)
- Update API_BASE_URL in app.js

---

## 🔐 Security Note

**Never put real API keys in frontend code!**

The current setup is safe because:
- Demo mode doesn't need API keys
- Real mode requires backend server
- Backend keeps keys secure in .env file
- Frontend only talks to your backend

---

## 🎯 Recommended Setup

**For Demo/Testing:**
- ✅ Use current demo mode
- ✅ Perfect for mobile testing
- ✅ Share GitHub Pages link
- ✅ Show to friends/portfolio

**For Real Trading:**
- ✅ Run backend locally
- ✅ Use Alpaca paper trading (free)
- ✅ Set DEMO_MODE = false
- ✅ Test with real data locally

---

## 📚 Files Modified

I fixed these files:

1. **`docs/styles.css`** - Fixed chart container height
2. **`docs/index.html`** - Added demo badge and chart wrapper
3. **`docs/app.js`** - Better mock data + demo mode toggle
4. **`frontend/*`** - Copied all fixes to frontend folder

---

## ✨ Summary

**Current Status:**
- ✅ Demo mode working perfectly
- ✅ Charts render correctly
- ✅ Realistic mock data
- ✅ Clear demo indicator
- ✅ Ready for mobile

**To Use Real Data:**
1. Get Alpaca API keys (free)
2. Configure .env file
3. Run: `python api_server.py`
4. Set `DEMO_MODE = false` in app.js
5. Reload page

**Or Keep Demo Mode:**
- It's perfect as-is!
- Great for presentations
- No setup required
- Works on mobile

---

**Enjoy your fixed dashboard! The chart should now render properly with realistic data! 🎉**
