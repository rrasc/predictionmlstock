# Deployment Guide

Complete guide for deploying the ML Trading System to production.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Security Setup](#security-setup)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Accounts
- **Alpaca**: Trading API access (https://alpaca.markets)
- **Stripe**: Payment processing (https://stripe.com)
- **Domain**: For production API
- **SSL Certificate**: Let's Encrypt or commercial

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04+ or similar Linux distribution

## Local Deployment

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/yourusername/predictionmlstock.git
cd predictionmlstock

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit with your values
nano .env
```

Required variables:
```
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
SECRET_KEY=generate_strong_random_key
STRIPE_SECRET_KEY=your_stripe_key
```

### 3. Initialize Database

```bash
# Run database initialization
python -c "from production_trading_system import TradingDatabase; TradingDatabase()"
```

### 4. Run Development Server

```bash
# Start API server
python api_server.py
```

### 5. Test API

```bash
# Health check
curl http://localhost:5000/health

# Get subscription tiers
curl http://localhost:5000/api/v1/subscriptions/tiers
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t ml-trading-system .

# Verify build
docker images | grep ml-trading
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 3. Access Services

- **API**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Database Migration

```bash
# Access database container
docker-compose exec db psql -U trading_user -d trading_db

# Or run migration script
docker-compose exec api python migrate.py
```

## AWS Deployment

### 1. EC2 Instance Setup

```bash
# Launch EC2 instance (Ubuntu 22.04)
# Instance type: t3.medium or larger
# Security group: Allow ports 22, 80, 443, 5000

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/predictionmlstock.git
cd predictionmlstock

# Setup environment
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:5000/health
```

### 3. Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/ml-trading
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ml-trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 5. RDS Database (Optional)

```bash
# Create RDS PostgreSQL instance
# Engine: PostgreSQL 15
# Instance class: db.t3.medium
# Storage: 50GB SSD

# Update .env with RDS endpoint
DATABASE_URL=postgresql://user:pass@your-rds-endpoint:5432/trading_db
```

### 6. ElastiCache Redis (Optional)

```bash
# Create ElastiCache Redis cluster
# Node type: cache.t3.medium

# Update .env with Redis endpoint
REDIS_URL=redis://your-redis-endpoint:6379/0
```

## Security Setup

### 1. Firewall Configuration

```bash
# UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Environment Variables Security

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use AWS Secrets Manager
aws secretsmanager create-secret --name ml-trading/prod \
  --secret-string file://.env

# Rotate keys regularly
```

### 3. API Security

```python
# Update api_server.py

# Add rate limiting per user
@limiter.limit("1000 per day", key_func=lambda: g.user_id)

# Add IP whitelisting
ALLOWED_IPS = ['1.2.3.4', '5.6.7.8']

# Add request signing
# Implement HMAC signature verification
```

### 4. Database Security

```bash
# PostgreSQL SSL mode
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Restrict access by IP
# Edit pg_hba.conf to allow only specific IPs
```

## Monitoring Setup

### 1. Application Monitoring (Sentry)

```python
# In api_server.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 2. Infrastructure Monitoring (Prometheus + Grafana)

```yaml
# Add to docker-compose.yml

prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Log Aggregation

```bash
# Setup CloudWatch Logs (AWS)
aws logs create-log-group --log-group-name /ml-trading/api

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 4. Uptime Monitoring

Services to use:
- **UptimeRobot**: Free monitoring
- **Pingdom**: Advanced monitoring
- **StatusPage**: Status page for users

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_status ON trades(status);
```

### 2. Redis Caching

```python
# Cache predictions
@cache.memoize(timeout=300)  # 5 minutes
def get_prediction(symbol):
    # Prediction logic
    pass
```

### 3. Load Balancing

```bash
# AWS Application Load Balancer
# Create target group with health checks
# Point to multiple EC2 instances
```

### 4. Auto-Scaling

```yaml
# AWS Auto Scaling Group
# Min: 2 instances
# Max: 10 instances
# Target CPU: 70%
```

## Backup Strategy

### 1. Database Backups

```bash
# Automated daily backups
0 2 * * * docker-compose exec -T db pg_dump -U trading_user trading_db | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz

# Retain 30 days
find /backups -name "db-*.sql.gz" -mtime +30 -delete
```

### 2. Model Backups

```bash
# Sync models to S3
aws s3 sync ./models s3://ml-trading-models/backups/$(date +%Y%m%d)/
```

### 3. Configuration Backups

```bash
# Backup .env and configs
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml nginx.conf
aws s3 cp config-backup-$(date +%Y%m%d).tar.gz s3://ml-trading-config/
```

## Disaster Recovery

### 1. Recovery Plan

1. Launch new EC2 instance
2. Restore database from latest backup
3. Deploy application from git
4. Restore models from S3
5. Update DNS to new instance

### 2. Testing Recovery

```bash
# Quarterly DR test
# Document recovery time (RTO target: 1 hour)
# Document data loss (RPO target: 1 hour)
```

## Troubleshooting

### Common Issues

**Issue**: Database connection failed
```bash
# Check database status
docker-compose ps db
docker-compose logs db

# Restart database
docker-compose restart db
```

**Issue**: API not responding
```bash
# Check API logs
docker-compose logs api

# Check resource usage
docker stats

# Restart API
docker-compose restart api
```

**Issue**: Model predictions failing
```bash
# Check model files
ls -lh models/

# Retrain models
python production_trading_system.py --retrain
```

### Performance Issues

```bash
# Check system resources
htop
df -h
free -m

# Check Docker resources
docker stats

# Database queries
docker-compose exec db psql -U trading_user -d trading_db
# Run: EXPLAIN ANALYZE SELECT ...
```

### Security Incidents

```bash
# Check access logs
sudo tail -f /var/log/nginx/access.log

# Check authentication failures
grep "401" logs/trading_*.log

# Block malicious IP
sudo ufw deny from 1.2.3.4
```

## Maintenance

### Regular Tasks

**Daily**
- Check error logs
- Monitor API performance
- Verify backup completion

**Weekly**
- Review security logs
- Update dependencies
- Check disk space

**Monthly**
- Retrain ML models
- Review performance metrics
- Update SSL certificates
- Security audit

### Updating Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify deployment
curl http://localhost:5000/health
```

## Cost Optimization

### AWS Cost Estimates

**Basic Setup** (~$100/month):
- EC2 t3.medium: $30
- RDS db.t3.medium: $50
- Data transfer: $10
- CloudWatch: $10

**Production Setup** (~$500/month):
- EC2 t3.large x2 (load balanced): $120
- RDS db.m5.large: $200
- ElastiCache: $50
- Load Balancer: $20
- Data transfer: $50
- CloudWatch/monitoring: $30
- S3/backups: $30

### Cost Saving Tips

1. Use Reserved Instances (40% savings)
2. Enable auto-scaling (scale down during off-hours)
3. Use S3 Glacier for old backups
4. Optimize database queries
5. Use CloudFront CDN for static assets

## Support

For deployment assistance:
- Email: devops@yourdomain.com
- Slack: #ml-trading-ops
- On-call: +1-555-0100

## Appendix

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart api

# Execute command in container
docker-compose exec api python script.py

# Database shell
docker-compose exec db psql -U trading_user

# Redis CLI
docker-compose exec redis redis-cli
```

### Environment Variables Reference

See `.env.example` for complete list of configuration options.

### API Endpoints

See README.md for complete API documentation.
