# Devo Alert Manager

A comprehensive alert management system that automatically syncs alerts between Grafana and Jira Service Management (JSM).

## 🌟 Features

- **Real-time Alert Sync**: Automatically syncs alerts from Grafana to JSM
- **Intelligent Matching**: Multi-strategy alert matching with confidence scoring
- **Bulk Operations**: Acknowledge or resolve multiple alerts simultaneously
- **Web Dashboard**: Modern React interface for alert management
- **CSV Export**: Export alert data for reporting and analysis

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Grafana instance with API access
- Jira Service Management account
- JSM Cloud ID (retrieved automatically)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd grafana-jsm-alert-manager
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Required environment variables**
   ```env
   # Grafana
   GRAFANA_API_URL="https://your-grafana.com"
   GRAFANA_API_KEY="your_grafana_api_key"

   # Jira Service Management
   JIRA_URL="https://yourcompany.atlassian.net"
   JIRA_USER_EMAIL="your.email@company.com"
   JIRA_API_TOKEN="your_jira_api_token"
   JSM_CLOUD_ID="your_cloud_id"  # Optional - auto-retrieved if not set
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

### Access

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📋 Configuration

### Alert Matching
Configure matching thresholds in `.env`:
```env
ALERT_MATCH_CONFIDENCE_THRESHOLD=70.0  # Minimum confidence for auto-matching
ALERT_MATCH_TIME_WINDOW_MINUTES=15    # Time window for matching
```

### Sync Settings
```env
GRAFANA_SYNC_INTERVAL_SECONDS=300      # How often to sync (default: 5 minutes)
FILTER_NON_PROD_ALERTS=true           # Filter out non-production alerts
```

## 🔧 Usage

### Basic Operations

1. **View Alerts**: Navigate to the web interface to see all synchronized alerts
2. **Acknowledge Alerts**: Select alerts and click "Acknowledge in JSM"
3. **Resolve Alerts**: Select alerts and click "Close in JSM"
4. **Manual Sync**: Click "Sync with JSM" to trigger immediate synchronization

### Filtering & Search

- Use the filter panel to search by alert name, severity, status, or cluster
- Toggle advanced filters for more options
- Export filtered results to CSV

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset database
docker-compose down -v
```

## 🏗️ Architecture

- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React + Ant Design
- **Sync**: APScheduler for automated synchronization
- **Matching**: Multi-strategy algorithm with confidence scoring

## 📊 API Endpoints

- `GET /api/alerts` - List all alerts
- `POST /api/alerts/acknowledge` - Acknowledge alerts
- `POST /api/alerts/resolve` - Resolve alerts
- `POST /api/alerts/sync` - Trigger manual sync
- `GET /api/alerts/export/csv` - Export to CSV

## 🛠️ Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### 🛣️ Roadmap

Planned enhancements for future releases:
- ✅ Add “Acknowledge” and “Resolve” actions from the UI
- 🔗 Integrate OpsGenie and other ticketing systems (e.g., Jira, ServiceNow)
- 📈 Display time-series charts for alert frequency and trends
- 🔐 Implement user login & role-based access control (RBAC)
- 🧠 Add ML-based alert deduplication and noise reduction (future scope)
- 🛠️ Admin panel for managing config, integrations, and users

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Version**: 1.0.0  
**Status**: Production Ready