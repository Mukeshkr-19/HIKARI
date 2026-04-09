#!/usr/bin/env python3
"""
HIKARI v2.0 - Quick Test Script
Tests if HIKARI can use Ollama with Gemma 4
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.router import AIRouter


def test_ollama():
    print("=" * 60)
    print("Testing HIKARI with Ollama (Gemma 4 E4B)")
    print("=" * 60)

    router = AIRouter()

    print("\nProvider Status:")
    for name, status in router.providers.items():
        print(f"  {name}: {'✅ available' if status.available else '❌ unavailable'}")

    print("\n" + "-" * 60)
    print("Testing Ollama with Gemma 4 E4B...")
    print("-" * 60)

    response = router.generate(
        user_input="Hello! What can you do? Reply in one sentence.",
        system_prompt="You are HIKARI, a helpful AI assistant.",
        max_tokens=100,
    )

    if response:
        print("\n✅ SUCCESS! Response from Gemma 4:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        return True
    else:
        print("\n❌ FAILED - No response from Ollama")
        return False


if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)
