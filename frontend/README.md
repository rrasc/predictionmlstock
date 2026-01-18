# ML Trading System - Frontend Dashboard

Beautiful, interactive stock prediction dashboard with real-time charts and AI predictions.

## Features

- **Stock Selection**: Quick access to popular stocks (NVDA, AVGO, AMD, TSLA, META, AAPL, MSFT, GOOGL)
- **Custom Symbol Search**: Analyze any stock symbol
- **Interactive Charts**: 90-day price history with Chart.js
- **AI Predictions**: Buy/Sell predictions with confidence scores
- **Probability Breakdown**: Detailed up/down probabilities
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Volume trends
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Theme**: Modern, eye-friendly dark interface
- **Subscription Plans**: Clear pricing tiers

## Quick Start

### Option 1: Open Directly (Demo Mode)

Simply open `index.html` in your web browser:

```bash
cd frontend
# On macOS
open index.html

# On Linux
xdg-open index.html

# On Windows
start index.html
```

The dashboard works in **DEMO MODE** by default with simulated data.

### Option 2: Local Server

For better performance and CORS handling:

```bash
# Using Python
cd frontend
python -m http.server 8000

# Using Node.js (if you have http-server)
npx http-server -p 8000

# Using PHP
php -S localhost:8000
```

Then open: http://localhost:8000

### Option 3: Integrate with Backend

1. Update `app.js` configuration:
```javascript
const API_BASE_URL = 'http://localhost:5000/api/v1';
const DEMO_MODE = false; // Enable real API calls
```

2. Start the backend API server:
```bash
cd ..
python api_server.py
```

3. Open frontend and enjoy real predictions!

## Testing the Dashboard

### Demo Mode (No Setup Required)

1. Open `index.html`
2. Click any stock button (e.g., NVDA)
3. Watch the AI analyze the stock
4. View prediction results with interactive charts

### Test Links

**Desktop**: http://localhost:8000 (after starting local server)

**Live Demo**: Deploy to GitHub Pages, Netlify, or Vercel for instant live preview

## Features Walkthrough

### 1. Stock Selection
Click any of the 8 popular stock buttons or enter a custom symbol.

### 2. AI Analysis
- 2-second realistic loading animation
- Real-time prediction generation
- Confidence score calculation

### 3. Prediction Results
- **Direction**: BUY (up arrow) or SELL (down arrow)
- **Confidence Score**: 0-100% with animated progress bar
- **Probability Breakdown**:
  - Up Probability (green)
  - Down Probability (red)

### 4. Price Chart
- 90-day historical price data
- Interactive hover tooltips
- Smooth gradient fill
- Responsive to window size

### 5. Technical Indicators
- **RSI (14)**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Volatility indicator
- **Volume Trend**: Trading volume analysis

### 6. Action Buttons
- Download full report (PDF)
- Set price alerts
- Analyze another stock

## Customization

### Change Colors

Edit `styles.css`:

```css
:root {
    --primary-color: #00d4ff;     /* Main accent color */
    --secondary-color: #6c63ff;   /* Secondary accent */
    --success-color: #00e676;     /* Success/Buy color */
    --danger-color: #ff1744;      /* Danger/Sell color */
    --dark-bg: #0a0e27;          /* Dark background */
    --card-bg: #151a30;          /* Card background */
}
```

### Add More Stocks

Edit `index.html` in the stock-grid section:

```html
<button class="stock-btn" data-symbol="AMZN">
    <span class="symbol">AMZN</span>
    <span class="name">Amazon</span>
</button>
```

### Modify Demo Data

Edit `app.js` in the `simulateAnalysis` function:

```javascript
const priceRanges = {
    'YOUR_SYMBOL': { min: 100, max: 200 },
    // Add more symbols...
};
```

## Deployment

### GitHub Pages

1. Push to GitHub repository
2. Go to Settings > Pages
3. Select branch and `/frontend` folder
4. Get your live URL: `https://username.github.io/repo`

### Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod
```

### Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel
```

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

All dependencies are loaded via CDN (no npm install needed):

- **Chart.js 4.4.0**: Stock price charts
- **Axios**: HTTP requests
- **Font Awesome 6.4.0**: Icons

## Performance

- Fast loading: < 2 seconds
- Optimized animations
- Responsive images
- Minimal dependencies

## Screenshots

### Desktop View
- Full dashboard with charts
- Interactive prediction cards
- Technical indicators

### Mobile View
- Responsive grid layout
- Touch-friendly buttons
- Optimized charts

## API Integration

When connecting to real backend:

### Required Environment Variables

```javascript
// In app.js
const API_BASE_URL = 'https://your-api.com/api/v1';
const DEMO_MODE = false;
```

### API Endpoints Used

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/predict` - Get stock prediction
- `GET /api/v1/performance` - Performance metrics

### Authentication

Uses JWT tokens stored in localStorage:

```javascript
localStorage.setItem('authToken', token);
localStorage.setItem('alpaca_key', your_key);
localStorage.setItem('alpaca_secret', your_secret);
```

## Troubleshooting

### Charts not displaying
- Check browser console for errors
- Ensure Chart.js CDN is loading
- Clear browser cache

### API calls failing
- Verify `API_BASE_URL` is correct
- Check CORS settings on backend
- Ensure authentication token is valid

### Slow performance
- Reduce chart data points
- Optimize animations
- Use local server instead of file://

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Multiple timeframe charts (1D, 5D, 1M, 1Y)
- [ ] Candlestick charts
- [ ] Portfolio tracking
- [ ] Price alerts with notifications
- [ ] Social features (share predictions)
- [ ] Dark/Light theme toggle
- [ ] Export to CSV/PDF
- [ ] Mobile app (React Native)

## Support

Issues? Questions? Feedback?

- Email: support@yourdomain.com
- GitHub Issues: https://github.com/yourusername/predictionmlstock/issues
- Discord: Join our community

## License

MIT License - Free to use and modify

## Credits

- Design: Inspired by modern fintech apps
- Charts: Chart.js
- Icons: Font Awesome
- Developed by: Claude Code

---

**Enjoy predicting the market with AI! 🚀📈**
