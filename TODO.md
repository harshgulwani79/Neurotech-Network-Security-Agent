# Integration Plan - NetMoniAI Unified System

## Objective
Integrate agent.py (LLM-powered AI) with network_simulator (real-time visualization) to create a unified system with:
- Two modes: Real-time Simulation + Historical CSV Analysis
- Agentic AI loop: Observe → Reason → Learn → Decide → Act
- TIER 1-3 severity system
- Visible anomaly impact on dashboard

## Tasks

### Phase 1: Core Backend Integration
- [ ] 1. Modify `backend/central_controller/gc_core.py`
  - [x] Add mode selection (REAL_TIME / HISTORICAL_CSV)
  - [x] Integrate LLM reasoning from agent.py
  - [x] Add TIER 1-3 severity classification
  - [x] Implement full Observe → Reason → Learn → Decide → Act cycle
  - [x] Make anomaly injection affect metrics properly
  - [x] Add learning/memory system

- [ ] 2. Modify `backend/app.py`
  - [x] Add API endpoint for mode switching (/api/mode)
  - [x] Add API endpoint to get current mode status
  - [x] Add API endpoint for learned policies
  - [x] Ensure AI analysis is properly broadcast with tier info

### Phase 2: Frontend Integration
- [x] 3. Modify `frontend/src/App.js`
  - [x] Add mode toggle (Real-time / Historical Analysis)
  - [x] Display TIER levels for each anomaly
  - [x] Show AI reasoning process visually
  - [x] Make anomaly injection show visible impact

- [x] 4. Modify `frontend/src/services/apiService.js`
  - [x] Add functions for mode switching
  - [x] Add functions for policies

### Phase 3: Testing
- [ ] 5. Test the integration
  - [ ] Real-time mode shows live anomalies with AI reasoning
  - [ ] Historical mode processes CSV with full LLM analysis
  - [ ] TIER 1 (autonomous), TIER 2 (approval), TIER 3 (escalation) work correctly
  - [ ] Dashboard reflects injected anomalies properly

## Dependencies
- agent.py LLM functions
- network_simulator metrics
- gc_core GlobalController
- Frontend components

