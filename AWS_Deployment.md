# 🚀 Supplero AWS EC2 Deployment Guide

Complete step-by-step guide for deploying Supplero on AWS EC2 using Docker Compose.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [AWS Account Setup](#aws-account-setup)
- [EC2 Instance Creation](#ec2-instance-creation)
- [Server Configuration](#server-configuration)
- [Application Deployment](#application-deployment)
- [Domain and SSL Setup](#domain-and-ssl-setup)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Prerequisites

- AWS Account (free tier eligible)
- Credit card for verification (won't be charged for free tier)
- Basic knowledge of Linux commands
- Your Supplero code repository

## AWS Account Setup

### 1. Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the registration process
4. Verify your email and phone number
5. Add a payment method (required but won't be charged for free tier)

### 2. Access AWS Console
1. Sign in to [AWS Console](https://console.aws.amazon.com)
2. Navigate to EC2 service
3. Select your preferred region (e.g., us-east-1, us-west-2)

## EC2 Instance Creation

### 1. Launch EC2 Instance

1. **Go to EC2 Dashboard**
   - Click "Launch Instance"
   - Name your instance: `supplero-testing`

2. **Choose AMI (Amazon Machine Image)**
   ```
   Application and OS Images: Ubuntu
   Version: Ubuntu Server 22.04 LTS (Free tier eligible)
   Architecture: 64-bit (x86)
   ```

3. **Instance Type**
   ```
   For Free Tier: t3.micro (1 vCPU, 1 GB RAM)
   For Better Performance: t3.small (2 vCPU, 2 GB RAM) - ~$15/month
   ```

4. **Key Pair**
   - Create new key pair: `supplero-keypair`
   - Download the `.pem` file
   - Store it securely (you'll need it to connect)

5. **Network Settings**
   ```
   VPC: Default VPC
   Subnet: Default subnet
   Auto-assign public IP: Enable
   Security Group: Create new security group
   ```

6. **Security Group Rules**
   ```
   SSH (22): My IP
   HTTP (80): Anywhere (0.0.0.0/0)
   HTTPS (443): Anywhere (0.0.0.0/0)
   Custom TCP (3000): Anywhere (0.0.0.0/0) - Frontend
   Custom TCP (8000): Anywhere (0.0.0.0/0) - Backend API
   ```

7. **Storage**
   ```
   Volume type: gp3
   Size: 20 GB (free tier: 30 GB)
   Encryption: Enabled
   ```

8. **Launch Instance**
   - Review all settings
   - Click "Launch Instance"
   - Wait for instance to be "Running"

### 2. Get Instance Information

1. **Note Down:**
   - Public IPv4 address (e.g., 3.15.123.45)
   - Public IPv4 DNS (e.g., ec2-3-15-123-45.compute-1.amazonaws.com)

## Server Configuration

### 1. Connect to Your Instance

**On Windows:**
```bash
# Using PuTTY or Windows Terminal
ssh -i "supplero-keypair.pem" ubuntu@your-public-ip
```

**On Mac/Linux:**
```bash
# Make key file secure
chmod 400 supplero-keypair.pem

# Connect to instance
ssh -i "supplero-keypair.pem" ubuntu@your-public-ip
```

### 2. Update System

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git nano htop unzip
```

### 3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 4. Configure Firewall

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000
sudo ufw allow 8000
sudo ufw --force enable

# Check status
sudo ufw status
```

## Application Deployment

### 1. Clone Repository

```bash
# Clone your repository
git clone https://github.com/your-username/Supplero.git
cd Supplero

# Or if using SSH
git clone git@github.com:your-username/Supplero.git
cd Supplero
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.testing.example .env.testing

# Edit environment file
nano .env.testing
```

**Update .env.testing with your values:**
```bash
# Environment
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
POSTGRES_DB=supplero
POSTGRES_USER=supplero
POSTGRES_PASSWORD=your_secure_database_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Security Configuration (CHANGE THESE!)
SECRET_KEY=your_very_secure_secret_key_for_testing
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Frontend Configuration (UPDATE WITH YOUR EC2 PUBLIC IP)
NEXT_PUBLIC_API_URL=http://your-ec2-public-ip:8000
NEXT_PUBLIC_APP_NAME=Supplero Testing
NEXT_PUBLIC_APP_VERSION=1.0.0

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200

# External API Keys (Optional)
DUN_BRADSTREET_API_KEY=
REFINITIV_API_KEY=
NEWS_API_KEY=73b1570193ea4621911c859decfda84b
```

### 3. Deploy Application

```bash
# Build and start all services
docker-compose -f docker-compose.testing.yml up -d --build

# Check status
docker-compose -f docker-compose.testing.yml ps

# View logs
docker-compose -f docker-compose.testing.yml logs -f
```

### 4. Verify Deployment

```bash
# Check if services are running
docker ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Check from outside (replace with your public IP)
curl http://your-ec2-public-ip:8000/health
```

### 5. Access Your Application

- **Frontend**: http://your-ec2-public-ip:3000
- **Backend API**: http://your-ec2-public-ip:8000
- **API Documentation**: http://your-ec2-public-ip:8000/docs

## Domain and SSL Setup

### 1. Get a Domain (Optional but Recommended)

**Popular Domain Registrars:**
- Namecheap: ~$10-15/year
- GoDaddy: ~$12-20/year
- Cloudflare: ~$10/year

### 2. Point Domain to EC2

1. **Get your EC2 Public IP**
2. **Update DNS Records:**
   ```
   Type: A
   Name: @ (or your subdomain)
   Value: your-ec2-public-ip
   TTL: 300
   ```

### 3. Install Nginx (Reverse Proxy)

```bash
# Install Nginx
sudo apt install nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/supplero
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/supplero /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Install SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. Basic Monitoring

```bash
# Check system resources
htop

# Check Docker containers
docker stats

# Check application logs
docker-compose -f docker-compose.testing.yml logs -f backend
docker-compose -f docker-compose.testing.yml logs -f frontend

# Check disk usage
df -h

# Check memory usage
free -h
```

### 2. Set Up Log Rotation

```bash
# Create log rotation config
sudo nano /etc/logrotate.d/supplero
```

**Log Rotation Configuration:**
```
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

### 3. Backup Strategy

```bash
# Create backup script
nano backup.sh
```

**Backup Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.testing.yml exec -T postgres pg_dump -U supplero supplero > $BACKUP_DIR/database_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/ubuntu/Supplero

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make script executable
chmod +x backup.sh

# Add to crontab for daily backups
crontab -e
# Add this line:
# 0 2 * * * /home/ubuntu/backup.sh
```

### 4. Update Application

```bash
# Pull latest changes
cd /home/ubuntu/Supplero
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.testing.yml down
docker-compose -f docker-compose.testing.yml up -d --build

# Check status
docker-compose -f docker-compose.testing.yml ps
```

## Troubleshooting

### Common Issues

1. **Can't connect to instance**
   ```bash
   # Check security group rules
   # Ensure port 22 is open for your IP
   # Verify key pair permissions
   chmod 400 supplero-keypair.pem
   ```

2. **Application not accessible**
   ```bash
   # Check if containers are running
   docker ps
   
   # Check logs
   docker-compose -f docker-compose.testing.yml logs
   
   # Check security group rules
   # Ensure ports 80, 443, 3000, 8000 are open
   ```

3. **Database connection issues**
   ```bash
   # Check PostgreSQL logs
   docker-compose -f docker-compose.testing.yml logs postgres
   
   # Test database connection
   docker-compose -f docker-compose.testing.yml exec postgres psql -U supplero -d supplero -c "SELECT version();"
   ```

4. **Out of memory**
   ```bash
   # Check memory usage
   free -h
   
   # Check swap
   swapon --show
   
   # Add swap if needed
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

5. **SSL certificate issues**
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew certificate
   sudo certbot renew
   
   # Check Nginx configuration
   sudo nginx -t
   ```

### Useful Commands

```bash
# Restart all services
docker-compose -f docker-compose.testing.yml restart

# Restart specific service
docker-compose -f docker-compose.testing.yml restart backend

# View real-time logs
docker-compose -f docker-compose.testing.yml logs -f

# Access container shell
docker-compose -f docker-compose.testing.yml exec backend bash

# Check resource usage
docker stats

# Clean up unused images
docker system prune -a
```

## Cost Optimization

### 1. Free Tier Usage

**AWS Free Tier includes:**
- 750 hours of t3.micro instance per month
- 30 GB of EBS storage
- 2 million I/O requests
- 1 GB of snapshot storage

### 2. Cost Monitoring

```bash
# Set up billing alerts in AWS Console
# Monitor costs in AWS Cost Explorer
# Use AWS Budgets for cost alerts
```

### 3. Optimization Tips

1. **Use Spot Instances** (for non-critical testing)
2. **Stop instance when not in use**
3. **Use smaller instance types**
4. **Clean up unused resources**
5. **Monitor data transfer costs**

### 4. Estimated Monthly Costs

**Free Tier (t3.micro):**
- EC2: $0 (750 hours free)
- EBS: $0 (30 GB free)
- Data Transfer: ~$1-5
- **Total: $1-5/month**

**Small Instance (t3.small):**
- EC2: ~$15/month
- EBS: ~$2/month
- Data Transfer: ~$1-5
- **Total: $18-22/month**

## Security Best Practices

### 1. Instance Security

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Configure fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart ssh
```

### 2. Application Security

```bash
# Use strong passwords
# Enable HTTPS
# Regular backups
# Monitor logs
# Keep Docker images updated
```

### 3. Network Security

- Use security groups properly
- Limit SSH access to your IP
- Use key pairs instead of passwords
- Enable VPC flow logs

## Next Steps

1. **Test your deployment** with a few users
2. **Monitor performance** and resource usage
3. **Set up monitoring** (CloudWatch, DataDog, etc.)
4. **Plan for scaling** when you have more users
5. **Consider migrating to Kubernetes** for production

---

**🎉 Congratulations! Your Supplero application is now running on AWS EC2!**

**Access URLs:**
- Frontend: http://your-ec2-public-ip:3000
- Backend: http://your-ec2-public-ip:8000
- With Domain: https://your-domain.com

For support or questions, refer to the troubleshooting section or create an issue in your repository.
