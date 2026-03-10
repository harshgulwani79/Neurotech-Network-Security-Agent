# Network Operations Center (NOC) Dashboard

A modern web-based frontend for your intelligent network monitoring system with AI-powered anomaly detection and tiered response automation.

## Features

✨ **Real-Time Monitoring**
- Live device status tracking (latency, packet loss, BGP flaps, throughput)
- Automatic anomaly detection and severity classification
- Interactive device visualizations

🎯 **Tier-Based Action Management**
- **Tier 1 (Auto-Fix):** Automatic execution of rate limiting & QoS adjustments
- **Tier 2 (Approval):** Human-approved traffic rerouting & config rollbacks
- **Tier 3 (Escalation):** Critical issues escalated to L3 engineering

📊 **Dashboard Features**
- Device health monitoring
- Anomaly viewer with real-time filtering
- Audit log tracking
- Network statistics and insights
- Responsive design (works on mobile & desktop)
- **Built-in Getting Started guide** on the dashboard

## Quick Start (3 Ways to Run)

### 🏃 **Fastest: Windows Batch File**
```bash
run.bat
```
Just double-click or run in PowerShell/CMD!

### ⚡ **PowerShell Script**
```powershell
.\run.ps1
```
Pretty console with colors and status indicators

### 📖 **Manual Steps**
```bash
python -m pip install flask flask-cors pandas numpy scikit-learn groq
python generate_data.py
python app.py
# Then open: http://localhost:5000
```

## File Structure

```
.
├── run.bat                      # ⭐ Windows startup (easiest!)
├── run.ps1                      # PowerShell startup (colorful!)
├── install_deps.py              # Install dependencies only
├── app.py                       # Flask API backend
├── agent.py                     # AI agent (Groq LLM)
├── generate_data.py             # Telemetry data generator
├── check_setup.py               # Environment checker
├── templates/
│   └── dashboard.html           # Web frontend ← Opens here!
├── network_memory.json          # Event memory
├── audit_log.txt                # Action audit trail
├── topology.json                # Network topology
├── telemetry_stream.csv         # Telemetry data
├── requirements.txt             # Python dependencies
├── QUICKSTART.md                # Detailed setup guide
└── README.md                    # This file
```

## Dashboard Tabs

### 🚀 Getting Started (Default Tab)
- Step-by-step instructions
- Copy-paste ready commands
- Live environment status checks
- Everything you need to know!

### 👁️ Devices
- View all network devices
- Real-time metrics (latency, packet loss, BGP flaps, throughput)
- Green = healthy, Red = anomaly detected

### 🎯 Anomalies  
- **Tier 1 (🟢):** Auto-execute fixes
- **Tier 2 (🟡):** Approve/deny actions
- **Tier 3 (🔴):** Escalate to engineers

### 📋 Audit Log
- Complete history of all actions
- Timestamps and details
- Compliance tracking

## How It Works

1. **Data Collection** → `generate_data.py` creates telemetry records
2. **Detection** → `agent.py` runs AI analysis via Groq LLM
3. **Categorization** → Isolation Forest ML model assigns Tier 1/2/3
4. **Frontend** → Dashboard shows results and accepts approvals
5. **Audit** → All actions logged to `audit_log.txt`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices` | GET | List all devices with latest metrics |
| `/api/telemetry` | GET | Get recent telemetry records |
| `/api/anomalies` | GET | Get anomalies grouped by tier |
| `/api/memory` | GET | Get memory stats (past events) |
| `/api/audit-log` | GET | Get audit log entries |
| `/api/topology` | GET | Get network topology |
| `/api/approve-action` | POST | Log approved/denied actions |
| `/api/health` | GET | Health check |

## Troubleshooting

**Dashboard won't load?**
- Ensure `python app.py` is running
- Check that port 5000 is available
- Try: `netstat -an | findstr :5000`

**Dependencies missing?**
```bash
python -m pip install flask flask-cors pandas numpy scikit-learn groq
```

**No devices showing?**
- Run `python generate_data.py` first
- Check that `telemetry_stream.csv` exists

**Port 5000 in use?**
- Change port in `app.py` line 41
- Or kill other Flask apps

## Further Reading

- **QUICKSTART.md** - Detailed setup with more options
- Check dashboard's "Getting Started" tab for live instructions
- See comments in `agent.py` for AI logic details
- See comments in `app.py` for API implementation

## Production Deployment

⚠️ **Before deploying to production:**

1. **Security**
   - Don't hardcode API keys (use environment variables)
   - Add authentication to Flask routes
   - Enable HTTPS/SSL

2. **Scaling**
   - Use gunicorn instead of Flask dev server
   - Add database (PostgreSQL) for persistence
   - Cache with Redis

3. **Infrastructure**
   - Containerize with Docker
   - Deploy with Kubernetes or Azure Container Apps
   - Set up monitoring and alerting

## License

MIT License - Feel free to modify and extend!

---

**Ready to get started?** Pick one of the 3 quick start methods above! ⚡

