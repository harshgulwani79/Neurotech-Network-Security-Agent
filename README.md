# Neurotech Network Security Agent

An AI-powered network security agent that autonomously detects and responds to network anomalies using machine learning and LLM reasoning.

## Features

- **Anomaly Detection**: Uses Isolation Forest ML algorithm to identify network anomalies
- **Tiered Response System**: 
  - Tier 1: Auto-execute low-risk actions (rate_limit, qos_adjustment)
  - Tier 2: Human-approved medium-risk actions (traffic_reroute, config_rollback)
  - Tier 3: Escalate high-risk critical incidents
- **LLM-Powered Reasoning**: Uses Groq LLM for root cause analysis and decision making
- **Learned Policies**: Continuously learns from past incidents to improve response
- **Partial Observability**: Simulates realistic sensor failures for testing
- **Blast Radius Calculation**: BFS-based impact analysis for affected devices and customers

## Architecture

```
├── backend/
│   ├── agent.py              # Main AI agent with ML & LLM
│   ├── app.py                # Flask API server
│   ├── config.py             # Configuration settings
│   ├── telemetry_generator.py # Generates network telemetry
│   ├── agents/               # AI agent implementations
│   ├── central_controller/  # Central controller logic
│   ├── mininet_integration/ # Mininet network simulator
│   └── network_simulator/    # Network simulation
├── frontend/                 # React-based dashboard
│   └── src/
│       └── components/       # UI components
└── network_memory.json       # Learned policies storage
```

## Prerequisites

- Python 3.10+
- Node.js (for frontend)
- Groq API Key

## Setup

### Backend

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set the Groq API key:
   ```bash
   # Set as environment variable
   export GROQ_API_KEY="your-groq-api-key"
   
   # Or create a .env file
   echo "GROQ_API_KEY=your-groq-api-key" > .env
   ```

4. Run the agent:
   ```bash
   python agent.py
   ```

### Frontend

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

The agent processes network telemetry data and:

1. **Detects Anomalies**: Uses Isolation Forest to identify anomalous network behavior
2. **Assigns Tiers**: Categorizes incidents by severity (1-3)
3. **Analyzes**: Uses LLM to determine root cause and blast radius
4. **Acts**: Executes appropriate response actions based on tier
5. **Learns**: Records outcomes and updates learned policies

## Configuration

Key configuration options in `backend/agent.py`:

- `TIER1_THRESHOLD`, `TIER2_THRESHOLD`: Anomaly score thresholds
- `AUTO_EXEC_MIN_CONF`: Minimum confidence for auto-execution (80%)
- `PARTIAL_OBS_RATE`: Sensor failure rate (20%)
- `MAX_RETRIES`: LLM API retry attempts

## API Endpoints

- `POST /api/analyze` - Analyze network metrics
- `GET /api/memory` - Get learned policies
- `GET /api/topology` - Get network topology
- `GET /api/telemetry` - Get real-time telemetry

## License

MIT License

