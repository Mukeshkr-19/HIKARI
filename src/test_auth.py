#!/usr/bin/env python3
"""
HIKARI v2.0 - Test with Authentication
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import Orchestrator

print("Creating Orchestrator...")
orch = Orchestrator()

print("\n--- Test 1: With codename 'harsha27' ---")
response = orch.process_input("harsha27", source="test")
print(f"Response: {response[:500] if response else 'None'}")

print("\n--- Test 2: Simple question (now authenticated) ---")
response = orch.process_input("What is 2+2?", source="test")
print(f"Response: {response[:500] if response else 'None'}")

print("\n--- Test 3: Capabilities question ---")
response = orch.process_input("What can you do?", source="test")
print(f"Response: {response[:500] if response else 'None'}")
