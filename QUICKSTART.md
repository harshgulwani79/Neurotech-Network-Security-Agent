# 🚀 Quick Start Guide - Network NOC Dashboard

## ⚡ Fastest Way to Get Started (Choose One)

### **Option 1: Windows Batch File (Easiest)**
```powershell
.\run.bat
```
This automatically:
- ✅ Installs dependencies
- ✅ Generates sample data  
- ✅ Starts the Flask server
- 🌐 Opens the dashboard

---

### **Option 2: Manual Installation (PowerShell/CMD)**

**Step 1: Install Dependencies**
```powershell
python -m pip install flask flask-cors pandas numpy scikit-learn groq
```

**Step 2: Generate Sample Network Data**
```powershell
python generate_data.py
```

**Step 3: Start the Dashboard Server**
```powershell
python app.py
```

**Step 4: Open in Browser**
```
http://localhost:5000
```

---

### **Option 3: Python Installation Script**
```powershell
python install_deps.py
```

Then:
```powershell
python generate_data.py
python app.py
```

---

## 📱 What You'll See

Once the dashboard loads, you'll see:

1. **🚀 Getting Started Tab** (Default View)
   - Setup instructions
   - Copy-paste commands
   - Environment status checks

2. **Devices Tab**
   - All network devices (Mumbai-Core, Delhi-Edge, Bangalore, NYC-Peering, Chennai-Link)
   - Real-time metrics: latency, packet loss, BGP flaps, throughput
   - Health indicators (green = healthy, red = anomaly)

3. **Anomalies Tab**
   - Tier 1 (✅ Auto-Fix): Automatic rate limiting
   - Tier 2 (⚠️ Approval): Human decision required
   - Tier 3 (🔴 Escalate): Critical issues

4. **Audit Log Tab**
   - Complete history of all actions
   - Timestamps and approvals

---

## 🤖 Optional: Run the AI Agent

In a **separate terminal**, you can run the intelligent agent:

```powershell
python agent.py
```

This will:
- Analyze anomalies using Groq LLM
- Categorize into 3 tiers
- Ask for approval on Tier 2 actions
- Learn from past decisions

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: flask_cors"
**Solution:**
```powershell
pip install flask-cors
```

### "ModuleNotFoundError: scikit-learn"  
**Solution:**
```powershell
pip install scikit-learn
```

### Port 5000 already in use
**Solution A:** Stop other Flask apps
**Solution B:** Change port in app.py line 4
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Use 5001 instead
```

### No devices showing on dashboard
**Solution:** Run data generation first
```powershell
python generate_data.py
```

### Dashboard won't connect to API
Make sure `python app.py` is running in another terminal!

---

## 📂 File Directory

```
Adv code 2/
├── app.py                      # Flask API server
├── agent.py                    # AI agent (optional)
├── generate_data.py            # Data generator
├── run.bat                     # Windows startup script
├── install_deps.py             # Dependency installer
├── check_setup.py              # Setup checker
├── templates/
│   └── dashboard.html          # Web interface
├── telemetry_stream.csv        # Generated data (9,990 records)
├── network_memory.json         # Persistent memory
├── audit_log.txt               # Action history
├── topology.json               # Network topology
└── requirements.txt            # Python dependencies
```

---

## 🔑 Feature Highlights

| Feature | Description |
|---------|-------------|
| 📊 Real-Time Monitoring | Live device metrics |
| 🎯 Auto-Categorization | AI assigns Tier 1, 2, or 3 |
| 🔧 Auto-Execute | Tier 1 actions run automatically |
| 👥 Human Approval | Tier 2 requires human decision |
| 🚨 Escalation | Tier 3 goes to L3 engineering |
| 📋 Audit Trail | Complete action history |
| 🧠 AI Learning | Agent learns from past decisions |

---

## 💡 Next Steps

1. **Explore the Dashboard**
   - Visit the "Getting Started" tab for copy-paste commands
   - Check device health in the "Devices" tab
   - Review anomalies in the "Anomalies" tab

2. **Run the AI Agent** (Optional)
   - Open a new terminal
   - Run: `python agent.py`
   - Watch it analyze network anomalies

3. **Integrate with Real Data**
   - Replace `telemetry_stream.csv` with your own network metrics
   - Connect to your ISP routers via SNMP/API
   - Retrain ML model with production data

4. **Deploy to Production**
   - Use Docker for containerization
   - Deploy on Kubernetes or Azure Container Apps
   - Add authentication and HTTPS

---

## 📞 Support

Check the comments in:
- `app.py` - Flask API implementation
- `agent.py` - AI agent logic
- `templates/dashboard.html` - Frontend code

---

**Enjoy your Network Operations Center! 🛰️**
