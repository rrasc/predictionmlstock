// Configuration
const API_BASE_URL = 'http://localhost:5000/api/v1';
const DEMO_MODE = true; // Set to false when backend is ready

// State
let currentStock = null;
let authToken = null;
let stockChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
});

// Event Listeners
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
        if (symbol) {
            analyzeStock(symbol);
        }
    });

    // Custom symbol enter key
    document.getElementById('customSymbol').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const symbol = document.getElementById('customSymbol').value.toUpperCase();
            if (symbol) {
                analyzeStock(symbol);
            }
        }
    });

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        document.getElementById('dashboard').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Login
    document.getElementById('loginBtn').addEventListener('click', () => {
        document.getElementById('loginModal').style.display = 'block';
    });

    // Close modal
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('loginModal').style.display = 'none';
    });

    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);

    // Other action buttons
    document.getElementById('viewReportBtn').addEventListener('click', () => {
        alert('Full report download feature coming soon!');
    });

    document.getElementById('setAlertBtn').addEventListener('click', () => {
        alert('Price alert feature coming soon!');
    });
}

// Analyze Stock
async function analyzeStock(symbol) {
    currentStock = symbol;

    // Show dashboard and loading
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    // Scroll to dashboard
    document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });

    // Update stock info
    document.getElementById('stockSymbol').textContent = symbol;

    try {
        if (DEMO_MODE) {
            // Demo mode with simulated data
            await simulateAnalysis(symbol);
        } else {
            // Real API call
            await fetchRealPrediction(symbol);
        }
    } catch (error) {
        console.error('Error analyzing stock:', error);
        alert('Error analyzing stock. Please try again.');
        document.getElementById('loading').style.display = 'none';
    }
}

// Simulate Analysis (Demo Mode)
async function simulateAnalysis(symbol) {
    // Simulate API delay
    await sleep(2000);

    // Generate random but realistic data
    const upProbability = 0.5 + (Math.random() * 0.4); // 50-90%
    const downProbability = 1 - upProbability;
    const prediction = upProbability > 0.5 ? 'BUY' : 'SELL';
    const confidence = Math.max(upProbability, downProbability);

    // Stock price (realistic range based on actual stocks)
    const priceRanges = {
        'NVDA': { min: 400, max: 600 },
        'AVGO': { min: 800, max: 1200 },
        'AMD': { min: 100, max: 200 },
        'TSLA': { min: 200, max: 400 },
        'META': { min: 300, max: 500 },
        'AAPL': { min: 150, max: 200 },
        'MSFT': { min: 350, max: 450 },
        'GOOGL': { min: 120, max: 180 }
    };

    const range = priceRanges[symbol] || { min: 50, max: 500 };
    const currentPrice = (Math.random() * (range.max - range.min) + range.min).toFixed(2);

    // Generate historical data for chart
    const historicalData = generateHistoricalData(currentPrice, 90);

    // Display results
    displayResults({
        symbol,
        prediction,
        confidence,
        upProbability,
        downProbability,
        currentPrice,
        historicalData,
        indicators: {
            rsi: (Math.random() * 100).toFixed(2),
            macd: (Math.random() * 10 - 5).toFixed(2),
            bb: 'Neutral',
            volume: Math.random() > 0.5 ? 'Increasing' : 'Decreasing'
        }
    });
}

// Fetch Real Prediction
async function fetchRealPrediction(symbol) {
    const response = await axios.post(`${API_BASE_URL}/predict`, {
        symbol,
        api_key: localStorage.getItem('alpaca_key'),
        secret_key: localStorage.getItem('alpaca_secret')
    }, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });

    const data = response.data;

    // Generate historical data (in real app, fetch from API)
    const historicalData = generateHistoricalData(data.current_price, 90);

    displayResults({
        symbol: data.symbol,
        prediction: data.prediction,
        confidence: data.confidence,
        upProbability: data.up_probability,
        downProbability: data.down_probability,
        currentPrice: data.current_price,
        historicalData,
        indicators: {
            rsi: '--',
            macd: '--',
            bb: 'Loading...',
            volume: 'Loading...'
        }
    });
}

// Display Results
function displayResults(data) {
    // Hide loading, show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';

    // Stock info
    document.getElementById('stockPrice').textContent = data.currentPrice;
    document.getElementById('stockDate').textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Prediction
    const predictionResult = document.getElementById('predictionResult');
    const predictionDirection = predictionResult.querySelector('.prediction-direction');

    if (data.prediction === 'BUY') {
        predictionDirection.classList.add('up');
        predictionDirection.classList.remove('down');
        predictionDirection.innerHTML = `
            <i class="fas fa-arrow-up"></i>
            <span>BUY</span>
        `;
    } else {
        predictionDirection.classList.add('down');
        predictionDirection.classList.remove('up');
        predictionDirection.innerHTML = `
            <i class="fas fa-arrow-down"></i>
            <span>SELL</span>
        `;
    }

    // Confidence
    const confidencePercent = (data.confidence * 100).toFixed(1);
    document.getElementById('confidenceValue').textContent = `${confidencePercent}%`;
    document.getElementById('confidenceFill').style.width = `${confidencePercent}%`;

    // Probabilities
    document.getElementById('upProb').textContent = `${(data.upProbability * 100).toFixed(1)}%`;
    document.getElementById('downProb').textContent = `${(data.downProbability * 100).toFixed(1)}%`;

    // Indicators
    document.getElementById('rsi').textContent = data.indicators.rsi;
    document.getElementById('macd').textContent = data.indicators.macd;
    document.getElementById('bb').textContent = data.indicators.bb;
    document.getElementById('volume').textContent = data.indicators.volume;

    // Chart
    renderChart(data.historicalData);

    // Animate elements
    animateResults();
}

// Generate Historical Data
function generateHistoricalData(currentPrice, days) {
    const data = [];
    let price = parseFloat(currentPrice);

    for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);

        // Random walk with slight upward bias
        const change = (Math.random() - 0.48) * (price * 0.03);
        price = Math.max(price + change, price * 0.5); // Prevent negative or too low

        data.push({
            date: date.toISOString().split('T')[0],
            price: parseFloat(price.toFixed(2))
        });
    }

    // Ensure last price matches current price
    data[data.length - 1].price = parseFloat(currentPrice);

    return data;
}

// Render Chart
function renderChart(data) {
    const ctx = document.getElementById('stockChart').getContext('2d');

    // Destroy existing chart
    if (stockChart) {
        stockChart.destroy();
    }

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 212, 255, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 212, 255, 0.0)');

    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: 'Price',
                data: data.map(d => d.price),
                borderColor: '#00d4ff',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#00d4ff',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(21, 26, 48, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: '#00d4ff',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `$${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(42, 47, 69, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#b0b8c9',
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(42, 47, 69, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#b0b8c9',
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    // Make chart responsive to container
    const chartContainer = document.querySelector('.chart-container canvas');
    chartContainer.style.height = '400px';
}

// Animate Results
function animateResults() {
    // Animate confidence bar
    setTimeout(() => {
        const fill = document.getElementById('confidenceFill');
        fill.style.transition = 'width 1.5s ease-out';
    }, 100);

    // Animate cards
    const cards = document.querySelectorAll('.prediction-card, .chart-container, .indicator-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.animation = 'fadeIn 0.5s ease';
        }, index * 100);
    });
}

// Handle Login
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (DEMO_MODE) {
        // Demo login
        authToken = 'demo_token_12345';
        localStorage.setItem('authToken', authToken);
        document.getElementById('loginModal').style.display = 'none';
        alert('Demo login successful!');
    } else {
        // Real login
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, {
                email,
                password
            });

            authToken = response.data.token;
            localStorage.setItem('authToken', authToken);
            document.getElementById('loginModal').style.display = 'none';
            alert('Login successful!');
        } catch (error) {
            alert('Login failed. Please check your credentials.');
        }
    }
}

// Utility Functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Load saved token on page load
window.addEventListener('load', () => {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
    }
});

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    const modal = document.getElementById('loginModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});
