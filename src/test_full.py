#!/usr/bin/env python3
"""
HIKARI v2.0 - Full System Test
Tests the complete orchestrator with Ollama
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("HIKARI v2.0 - Full System Test")
print("=" * 60)

print("\n[1] Creating Orchestrator...")
from core.orchestrator import Orchestrator

orch = Orchestrator()
print("✅ Orchestrator created")

print("\n[2] Testing with simple query...")
response = orch.process_input("Hello! How are you?", source="test")
print(f"\nResponse: {response[:300] if response else 'No response'}...")

if response:
    print("\n✅ HIKARI is working with Ollama (Gemma 4)!")
else:
    print("\n❌ No response - check logs above")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)
