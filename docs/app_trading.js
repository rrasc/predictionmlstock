// Configuration - REAL DATA from Yahoo Finance (Client-Side!)
const CORS_PROXY = 'https://api.allorigins.win/raw?url=';
const USE_REAL_DATA = true; // TRUE = Real Yahoo Finance data!

// State
let currentStock = null;
let priceChart = null;
let volumeChart = null;
let currentPeriod = '3mo';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateClock();
    setInterval(updateClock, 1000);
});

function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    document.getElementById('currentTime').textContent = `${dateStr} ${timeStr}`;
}

function initializeEventListeners() {
    // Stock buttons
    document.querySelectorAll('.stock-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const symbol = btn.dataset.symbol;
            analyzeStock(symbol);
        });
    });

    // Custom symbol
    document.getElementById('analyzeBtn').addEventListener('click', () => {
        const symbol = document.getElementById('customSymbol').value.toUpperCase();
        if (symbol) analyzeStock(symbol);
    });

    document.getElementById('customSymbol').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const symbol = document.getElementById('customSymbol').value.toUpperCase();
            if (symbol) analyzeStock(symbol);
        }
    });

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        document.getElementById('dashboard').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Timeframe buttons
    document.querySelectorAll('.tf-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPeriod = btn.dataset.period;
            if (currentStock) {
                analyzeStock(currentStock, currentPeriod);
            }
        });
    });
}

async function analyzeStock(symbol, period = '3mo') {
    currentStock = symbol;
    currentPeriod = period;

    // Show dashboard and loading
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    // Scroll to dashboard
    document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });

    try {
        // Fetch REAL data from Yahoo Finance
        const data = await fetchRealYahooData(symbol, period);
        displayResults(data);
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('loading').innerHTML = `
            <div style="color: #ef5350; padding: 40px; text-align: center;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i>
                <p style="font-size: 18px; margin-bottom: 10px;">Could not fetch data for ${symbol}</p>
                <p style="font-size: 14px; color: #787b86;">Please check the symbol and try again</p>
                <button class="btn btn-primary" onclick="document.getElementById('dashboard').style.display='none'" style="margin-top: 20px;">
                    <i class="fas fa-arrow-left"></i> Go Back
                </button>
            </div>
        `;
    }
}

async function fetchRealYahooData(symbol, period = '3mo') {
    console.log('Fetching data for', symbol, 'period:', period);

    // Build Yahoo Finance API URL
    const range = period;
    const interval = '1d';
    const yahooUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?range=${range}&interval=${interval}`;

    console.log('Yahoo URL:', yahooUrl);

    try {
        // Try direct call first (works sometimes)
        let response;
        try {
            console.log('Attempting direct fetch...');
            response = await fetch(yahooUrl);
            console.log('Direct fetch response:', response.status);
        } catch (corsError) {
            // If CORS fails, use proxy
            console.log('Direct fetch failed, using CORS proxy...');
            const proxyUrl = CORS_PROXY + encodeURIComponent(yahooUrl);
            console.log('Proxy URL:', proxyUrl);
            response = await fetch(proxyUrl);
            console.log('Proxy fetch response:', response.status);
        }

        const json = await response.json();
        console.log('API response received');

        if (!json.chart || !json.chart.result || json.chart.result.length === 0) {
            console.error('Invalid API response:', json);
            throw new Error('Invalid data from Yahoo Finance');
        }

        const result = json.chart.result[0];
        console.log('Result obtained');

        // Extract data
        const timestamps = result.timestamp;
        const quote = result.indicators.quote[0];
        const meta = result.meta;

        console.log('Data points:', timestamps?.length);
        console.log('Meta:', meta);

        // Current price
        const currentPrice = meta.regularMarketPrice;
        console.log('Current price:', currentPrice);

        // Build historical data (OHLCV)
        const historical = [];
        for (let i = 0; i < timestamps.length; i++) {
            const date = new Date(timestamps[i] * 1000);
            historical.push({
                date: date.toISOString().split('T')[0],
                open: quote.open[i],
                high: quote.high[i],
                low: quote.low[i],
                close: quote.close[i],
                volume: quote.volume[i]
            });
        }

        // Calculate indicators
        const closes = historical.map(h => h.close).filter(c => c != null);
        const rsi = calculateRSI(closes, 14);
        const macd = calculateMACD(closes);
        const sma20 = calculateSMA(closes, 20);

        // Calculate 24h change
        const prevClose = historical[historical.length - 2]?.close || currentPrice;
        const change24h = ((currentPrice - prevClose) / prevClose) * 100;

        // Simple ML prediction (based on indicators)
        const prediction = makePrediction(rsi, macd, change24h);

        return {
            symbol: symbol,
            prediction: prediction.direction,
            confidence: prediction.confidence,
            up_probability: prediction.upProb,
            down_probability: prediction.downProb,
            current_price: currentPrice,
            historical_data: historical,
            indicators: {
                rsi: rsi,
                macd: macd.macd,
                sma_20: sma20,
                volume: historical[historical.length - 1].volume > historical[historical.length - 2].volume ? 'High' : 'Normal'
            },
            change_24h: change24h,
            data_source: 'Yahoo Finance',
            demo: false
        };

    } catch (error) {
        console.error('Yahoo Finance error:', error);
        throw new Error(`Failed to fetch data for ${symbol}`);
    }
}

// Technical Analysis Functions
function calculateRSI(prices, period = 14) {
    if (prices.length < period + 1) return 50;

    let gains = 0;
    let losses = 0;

    for (let i = prices.length - period; i < prices.length; i++) {
        const change = prices[i] - prices[i - 1];
        if (change > 0) gains += change;
        else losses -= change;
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;

    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
}

function calculateMACD(prices) {
    if (prices.length < 26) return { macd: 0, signal: 0, histogram: 0 };

    const ema12 = calculateEMA(prices, 12);
    const ema26 = calculateEMA(prices, 26);
    const macd = ema12 - ema26;

    return { macd: macd, signal: 0, histogram: macd };
}

function calculateEMA(prices, period) {
    if (prices.length === 0) return 0;

    const k = 2 / (period + 1);
    let ema = prices[prices.length - period];

    for (let i = prices.length - period + 1; i < prices.length; i++) {
        ema = prices[i] * k + ema * (1 - k);
    }

    return ema;
}

function calculateSMA(prices, period) {
    if (prices.length < period) return prices[prices.length - 1];

    const slice = prices.slice(-period);
    return slice.reduce((a, b) => a + b, 0) / period;
}

function makePrediction(rsi, macd, change24h) {
    // Simple rule-based prediction
    let score = 0;

    // RSI signals
    if (rsi < 30) score += 0.3; // Oversold = Buy
    if (rsi > 70) score -= 0.3; // Overbought = Sell

    // MACD signals
    if (macd.macd > 0) score += 0.2;
    if (macd.macd < 0) score -= 0.2;

    // Momentum
    if (change24h > 2) score += 0.2;
    if (change24h < -2) score -= 0.2;

    // Normalize to 0.5-0.9 range
    const upProb = 0.5 + (score * 0.4);
    const clampedProb = Math.max(0.5, Math.min(0.9, upProb));

    return {
        direction: clampedProb > 0.5 ? 'BUY' : 'SELL',
        confidence: Math.max(clampedProb, 1 - clampedProb),
        upProb: clampedProb,
        downProb: 1 - clampedProb
    };
}

function displayResults(data) {
    // Hide loading, show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';

    // Update stock header
    document.getElementById('stockSymbol').textContent = data.symbol;
    document.getElementById('stockName').textContent = data.symbol + ' Stock';
    document.getElementById('stockPrice').textContent = data.current_price.toFixed(2);

    // Price change
    const change = data.change_24h || 0;
    const changeEl = document.getElementById('priceChange');
    changeEl.innerHTML = `
        <span class="change-value">${change >= 0 ? '+' : ''}${change.toFixed(2)}</span>
        <span class="change-percent">(${change >= 0 ? '+' : ''}${change.toFixed(2)}%)</span>
    `;
    changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');

    // Prediction badge
    const predBadge = document.getElementById('predictionBadge');
    const isBuy = data.prediction === 'BUY';
    predBadge.className = 'prediction-badge ' + (isBuy ? 'buy' : 'sell');
    predBadge.innerHTML = `
        <i class="fas fa-arrow-${isBuy ? 'up' : 'down'}"></i>
        <span>${data.prediction}</span>
        <div class="confidence">${(data.confidence * 100).toFixed(0)}%</div>
    `;

    // Prediction details
    const predDir = document.getElementById('predDirection');
    predDir.className = 'pred-direction ' + (isBuy ? 'buy' : 'sell');
    predDir.innerHTML = `
        <i class="fas fa-arrow-${isBuy ? 'up' : 'down'}"></i>
        <span>${data.prediction}</span>
    `;

    document.getElementById('confValue').textContent = `${(data.confidence * 100).toFixed(0)}%`;
    document.getElementById('confFill').style.width = `${data.confidence * 100}%`;

    document.getElementById('upProb').textContent = `${(data.up_probability * 100).toFixed(1)}%`;
    document.getElementById('downProb').textContent = `${(data.down_probability * 100).toFixed(1)}%`;

    // Indicators
    document.getElementById('rsiValue').textContent = data.indicators.rsi ? data.indicators.rsi.toFixed(2) : '--';
    document.getElementById('macdValue').textContent = data.indicators.macd ? data.indicators.macd.toFixed(2) : '--';
    document.getElementById('smaValue').textContent = data.indicators.sma_20 ? '$' + data.indicators.sma_20.toFixed(2) : '--';
    document.getElementById('volumeValue').textContent = data.indicators.volume || '--';

    // Last update & data source
    document.getElementById('lastUpdate').textContent = 'Just now';

    // Update data source
    const sourceValue = document.querySelector('.source-card .source-value');
    if (sourceValue) {
        sourceValue.textContent = 'Yahoo Finance (Real-Time)';
        sourceValue.style.color = '#26a69a';
    }

    // Create charts
    createCharts(data.historical_data, data.symbol);
}

function createCharts(historicalData, symbol) {
    console.log('createCharts called with data:', historicalData?.length, 'points');

    // Clear existing charts
    const chartDiv = document.getElementById('tradingViewChart');
    const volumeDiv = document.getElementById('volumeChart');

    if (!chartDiv || !volumeDiv) {
        console.error('Chart containers not found!');
        return;
    }

    chartDiv.innerHTML = '';
    volumeDiv.innerHTML = '';

    if (!historicalData || historicalData.length === 0) {
        console.error('No historical data available');
        return;
    }

    // Check if LightweightCharts is loaded
    if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts library not loaded!');
        chartDiv.innerHTML = '<div style="color: #ef5350; padding: 20px; text-align: center;">Chart library failed to load. Please refresh the page.</div>';
        return;
    }

    console.log('LightweightCharts loaded successfully');

    // Filter out null values
    const validData = historicalData.filter(d =>
        d.open != null && d.high != null && d.low != null && d.close != null
    );

    console.log('Valid data points:', validData.length);

    if (validData.length === 0) {
        console.error('No valid data after filtering');
        chartDiv.innerHTML = '<div style="color: #ef5350; padding: 20px; text-align: center;">No valid price data available</div>';
        return;
    }

    // Prepare data for candlestick chart
    const candleData = validData.map(d => ({
        time: d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close
    }));

    const volumeData = validData.map(d => ({
        time: d.date,
        value: d.volume || 0,
        color: d.close >= d.open ? '#26a69a80' : '#ef535080'
    }));

    console.log('Candle data prepared:', candleData.length, 'candles');
    console.log('First candle:', candleData[0]);
    console.log('Last candle:', candleData[candleData.length - 1]);

    try {
        // Create price chart
        console.log('Creating price chart...');
        priceChart = LightweightCharts.createChart(document.getElementById('tradingViewChart'), {
            width: document.getElementById('tradingViewChart').offsetWidth,
            height: 450,
            layout: {
                background: { color: '#1e222d' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2a2e39' },
                horzLines: { color: '#2a2e39' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#2a2e39',
            },
            timeScale: {
                borderColor: '#2a2e39',
                timeVisible: true,
            },
        });

        console.log('Price chart created, adding candlestick series...');
        const candleSeries = priceChart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        candleSeries.setData(candleData);
        console.log('Candlestick data set successfully');
    } catch (error) {
        console.error('Error creating price chart:', error);
        chartDiv.innerHTML = '<div style="color: #ef5350; padding: 20px; text-align: center;">Error creating chart: ' + error.message + '</div>';
        return;
    }

    try {
        // Create volume chart
        console.log('Creating volume chart...');
        volumeChart = LightweightCharts.createChart(document.getElementById('volumeChart'), {
            width: document.getElementById('volumeChart').offsetWidth,
            height: 120,
            layout: {
                background: { color: '#1e222d' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2a2e39' },
                horzLines: { color: '#2a2e39' },
            },
            rightPriceScale: {
                borderColor: '#2a2e39',
            },
            timeScale: {
                borderColor: '#2a2e39',
                timeVisible: false,
            },
        });

        console.log('Volume chart created, adding histogram series...');
        const volumeSeries = volumeChart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
        });

        volumeSeries.setData(volumeData);
        console.log('Volume data set successfully');
        console.log('✓ Charts rendered successfully!');
    } catch (error) {
        console.error('Error creating volume chart:', error);
        volumeDiv.innerHTML = '<div style="color: #ef5350; padding: 20px; text-align: center;">Error creating volume chart: ' + error.message + '</div>';
    }

    // Sync time scales
    priceChart.timeScale().subscribeVisibleTimeRangeChange(() => {
        const timeRange = priceChart.timeScale().getVisibleRange();
        volumeChart.timeScale().setVisibleRange(timeRange);
    });

    volumeChart.timeScale().subscribeVisibleTimeRangeChange(() => {
        const timeRange = volumeChart.timeScale().getVisibleRange();
        priceChart.timeScale().setVisibleRange(timeRange);
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (priceChart) {
            priceChart.resize(document.getElementById('tradingViewChart').offsetWidth, 450);
        }
        if (volumeChart) {
            volumeChart.resize(document.getElementById('volumeChart').offsetWidth, 120);
        }
    });
}
