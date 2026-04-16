# 🌾 KisanAI - Smart Farming Assistant

> An AI-powered farming assistant providing weather forecasts, market prices, soil health monitoring, expense tracking, and intelligent crop management.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Optimized-success.svg)](SYSTEM_STATUS.md)

---

## ✅ System Status

**Latest Version:** 2.0 (Refactored & Optimized) ✅  
**Code Quality:** Production-Grade ✅  
**Structure:** Clean & Organized ✅

- ✅ All security vulnerabilities addressed
- ✅ Dependencies updated to latest stable versions
- ✅ Codebase fully refactored and organized
- ✅ Consistent coding patterns enforced
- ✅ Documentation updated and comprehensive

---

## 📑 Table of Contents

- [System Status](#-system-status)
- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Setup](#-environment-setup)
- [Development](#-development)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [Documentation](#-documentation)

---

## 🎯 Overview

KisanAI is a full-stack web application designed to help farmers make data-driven decisions. It combines real-time weather data, market price tracking, soil health monitoring, and AI-powered insights to optimize farming operations.

**Key Highlights:**
- 🌦️ Real-time weather forecasts with 5-day predictions
- 💰 Live market price tracking across multiple states
- 🌱 Soil health analysis with NPK levels and pH monitoring
- 📊 Financial tracking with income/expense analytics
- 🌾 Crop management with growth stage tracking
- 🤖 AI-powered chatbot for farming advice
- 📱 Responsive design - works on all devices
- 🔐 Secure authentication with JWT tokens

---

## ✨ Features

### 🌦️ Weather Forecasts
- Current weather conditions (temperature, humidity, wind speed)
- 5-day weather forecast with daily predictions
- City-based weather search
- Intelligent caching (6-hour TTL)

### 💰 Market Prices
- Real-time crop prices from government APIs
- State-wise price comparison
- Price history visualization (7-day trend)
- Modal, minimum, and maximum price tracking

### 🌱 Soil Health Monitoring
- NPK (Nitrogen, Phosphorus, Potassium) level tracking
- pH level monitoring with status indicators
- Moisture percentage tracking
- Historical soil reports

### 📊 Financial Management
- Income and expense tracking
- Category-based expense organization
- Crop-linked transactions
- Visual analytics with charts:
  - Timeline chart (income vs expenses)
  - Category breakdown (pie/bar chart)
- Profit/loss calculation

### 🌾 Crop Management
- Add and track multiple crops
- Plot/field assignment
- Growth stage tracking (Sown → Germination → Vegetative → Flowering → Fruiting → Harvest Ready → Harvested)
- Sowing date recording
- Quick crop status overview

### 🤖 AI-Powered Features
- **Smart Dashboard Insights**: AI-generated recommendations based on weather and crop data
- **Chatbot Assistant**: Ask farming questions and get AI-powered answers
- Intent detection for context-aware responses
- LLM integration via OpenRouter (Llama 3.1)

### 🔐 Authentication & Security
- User registration and login
- JWT token-based authentication
- Password hashing with bcrypt
- Protected API routes
- Session persistence

---

## 🛠️ Tech Stack

### Frontend
- **React 19** - UI library
- **React Router DOM 7** - Client-side routing
- **TanStack React Query 5** - Server state management & caching
- **TailwindCSS 3** - Utility-first CSS framework
- **Framer Motion 12** - Animation library
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **Recharts** - Chart visualization
- **Vite 7** - Build tool and dev server

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0+** - SQL toolkit and ORM
- **SQLite** - Lightweight database
- **Uvicorn** - ASGI server
- **Pydantic 2.0+** - Data validation
- **python-jose** - JWT token handling
- **passlib[bcrypt]** - Password hashing
- **httpx** - Async HTTP client for external APIs

### External APIs
- **OpenWeatherMap** - Weather data
- **India Government Open Data** - Market prices
- **OpenRouter** - LLM integration (Llama 3.1)

### Development Tools
- **Git** - Version control
- **Docker** - Containerization
- **Ruff** - Python Linter and Formatter
- **ESLint** - JavaScript Linter

---

## 📁 Project Structure

See [STRUCTURE.md](STRUCTURE.md) for detailed project organization.

```
kisan-ai/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 16+** and npm
- **Git**

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/kisan-ai.git
cd kisan-ai
```

### 2. Run Setup Script
```bash
scripts\setup.bat
```

### 3. Configure Environment
```bash
# Copy example env files
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env

# Edit backend\.env and add your API keys
```

### 4. Start Application
```bash
scripts\start.bat
```

### 5. Access the App
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Default Login
- **Username:** demo
- **Password:** demo123

---

## 💻 Development

### Backend Development

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run development server
uvicorn backend.main:app --reload --port 8000

# Run linter
ruff check backend

# Format code
ruff format backend
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run linter
npm run lint

# Build for production
npm run build
```

---

## 🧪 Testing

### Backend Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend
```

### Frontend Tests
```bash
cd frontend

# Install test dependencies
npm install -D vitest @testing-library/react

# Run tests
npm test
```

---

## 🐳 Deployment

See [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) for the complete production deployment guide.

### Quick Deploy with Docker

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

---

## 📡 API Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

### Coding Standards
- Follow [docs/BACKEND_GUIDE.md](docs/BACKEND_GUIDE.md) for backend code
- Follow [docs/UI_UX_GUIDE.md](docs/UI_UX_GUIDE.md) for frontend code
- Write tests for new features
- Update documentation as needed

---

## 📚 Documentation

Comprehensive guides are available in the `docs/` directory:

- **[STRUCTURE.md](STRUCTURE.md)** - Project structure overview
- **[BACKEND_GUIDE.md](docs/BACKEND_GUIDE.md)** - Backend best practices
- **[REACT_QUERY_GUIDE.md](docs/REACT_QUERY_GUIDE.md)** - React Query patterns
- **[UI_UX_GUIDE.md](docs/UI_UX_GUIDE.md)** - UI/UX standardization
- **[DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** - Production deployment

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenWeatherMap for weather data
- India Government Open Data for market prices
- OpenRouter for LLM access
- The open-source community

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the changelog

---

**Version:** 2.0  
**Last Updated:** November 30, 2025  
**Status:** Production Ready 🚀
