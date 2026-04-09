#!/usr/bin/env python3
"""Quick HIKARI test"""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import Orchestrator

orch = Orchestrator()
# Authenticate first
orch.process_input("harsha27", source="test")
# Then ask
response = orch.process_input("Say 'HIKARI is working' in one sentence", source="test")
print(response[:300] if response else "No response")
