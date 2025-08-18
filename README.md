# Supplero - AI-Powered Intelligent Procurement & Supplier Risk Management

An enterprise-grade platform that leverages AI to transform procurement processes, automate contract analysis, and provide intelligent supplier risk management.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Kubernetes cluster (for production deployment)
- OpenAI API key

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Supplero
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configurations
   ```

3. **Start development environment**
   ```bash
   make dev
   ```

4. **Access services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Elasticsearch: http://localhost:9200

## 🏗️ Architecture

### Core Components

- **Backend**: FastAPI-based Python application with OpenAI integration
- **Frontend**: Next.js React application with modern UI components
- **Database**: PostgreSQL for structured data storage
- **Cache**: Redis for session management and caching
- **Search**: Elasticsearch for document search and embeddings
- **AI**: OpenAI GPT-4 and Vision API for intelligent analysis
- **External Data**: News APIs, financial data APIs for supplier risk assessment

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **AI Integration**: OpenAI API
- **Search**: Elasticsearch
- **Authentication**: JWT with OAuth 2.0
- **Logging**: Structured logging with structlog

#### Frontend
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Forms**: React Hook Form with Zod validation
- **UI Components**: Radix UI primitives
- **Charts**: Recharts for data visualization

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus & Grafana (planned)
- **Security**: OAuth 2.0, RBAC, audit logging

## 🔍 Supplier Risk Management

### Enhanced Risk Assessment

Supplero now includes advanced supplier risk assessment capabilities that aggregate data from multiple external sources:

- **News API Integration**: Real-time news sentiment analysis for risk detection
- **Financial Data APIs**: Company financial health indicators and credit ratings
- **Industry Risk Models**: Sector-specific risk factors and compliance frameworks
- **Automated Risk Scoring**: Combines internal data with external signals

### API Endpoints

- `POST /api/v1/suppliers/profile` - Create supplier profile with initial risk assessment
- `GET /api/v1/suppliers/{id}/risk` - Get basic risk assessment
- `POST /api/v1/suppliers/{id}/risk/enhanced` - Trigger enhanced risk assessment with external data

### External Data Sources

- **News API**: Free tier available (1,000 requests/day)
- **Dun & Bradstreet**: Enterprise financial data and credit ratings
- **Refinitiv**: Real-time financial market data and risk metrics

For detailed setup instructions, see [EXTERNAL_APIS_SETUP.md](backend/EXTERNAL_APIS_SETUP.md).

## 🛠️ Development

```bash
# Development environment
make dev          # Build and start all services
make up           # Start services
make down         # Stop services
make logs         # View service logs
make restart      # Restart services

# Testing & Quality
make test         # Run all tests
make lint         # Run linting checks
make format       # Format code

# Database operations
make db-init      # Initialize database schema
make db-reset     # Reset database

# Health checks
make health       # Check service health

# Kubernetes deployment
make k8s-deploy   # Deploy to Kubernetes
make k8s-delete   # Delete from Kubernetes
```

### Project Structure

```
Supplero/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile.dev      # Development Dockerfile
├── frontend/               # Next.js frontend application
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utility functions
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile.dev      # Development Dockerfile
├── kubernetes/             # Kubernetes manifests
├── scripts/                # Database and utility scripts
├── docker-compose.yml      # Local development setup
├── Makefile                # Development commands
└── README.md               # This file
```

### API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Schema

The application includes a comprehensive database schema with tables for:
- Organizations and users
- Suppliers and risk assessment
- Contracts and contract clauses
- AI request tracking
- Audit logging

## 🔒 Security Features

- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: Encryption at rest and in transit
- **Audit Logging**: Comprehensive activity tracking
- **Input Validation**: Request validation with Pydantic
- **CORS**: Configurable cross-origin resource sharing

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Testing
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Testing
```bash
npm run test:e2e
```

## 📊 Monitoring & Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Service health endpoints
- **Metrics**: Prometheus metrics (planned)
- **Tracing**: Distributed tracing with OpenTelemetry (planned)

## 🚀 Deployment

### Local Development
```bash
make dev
```

### Production Deployment
```bash
# Build production images
make docker-build

# Push to registry
make docker-push

# Deploy to Kubernetes
make k8s-deploy
```

### Environment Variables

Key environment variables for production:
- `OPENAI_API_KEY`: OpenAI API key for AI services
- `SECRET_KEY`: Application secret key
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `ENVIRONMENT`: Environment name (production/staging)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Quality Standards

- **Python**: Black, isort, flake8, mypy
- **JavaScript**: ESLint, Prettier, TypeScript strict mode
- **Testing**: Minimum 80% code coverage
- **Documentation**: Comprehensive docstrings and README updates

## 📝 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation and API docs

## 🔮 Roadmap

### Phase 1: MVP (Months 1-3) ✅
- [x] Core infrastructure and security foundation
- [x] Basic contract analysis and risk assessment
- [x] User management and authentication
- [x] Document ingestion and processing

### Phase 2: Advanced Risk Management (Months 4-6)
- [ ] Advanced supplier risk scoring
- [ ] Real-time risk monitoring
- [ ] Compliance tracking and reporting
- [ ] Integration with external data sources

### Phase 3: Strategic Sourcing (Months 7-9)
- [ ] Supplier performance analytics
- [ ] Cost optimization recommendations
- [ ] Market intelligence and benchmarking
- [ ] Advanced procurement workflows

### Phase 4: Enterprise Production (Months 10-12)
- [ ] Enterprise-grade scalability
- [ ] Advanced security and compliance
- [ ] Multi-tenant architecture
- [ ] Advanced AI capabilities

---

**Built with ❤️ by the Supplero Team** 