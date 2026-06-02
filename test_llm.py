#!/usr/bin/env python3
"""Test script for LLM connectivity."""

from llm.brain import OpenAIChatClient, LLMBrain


def test_chat():
    """Test chat completion."""
    print("Testing chat completion...")
    client = OpenAIChatClient()
    brain = LLMBrain(client)
    
    result = brain.chat(
        system="You are a helpful assistant.",
        user="Say 'test successful' in one sentence.",
    )
    
    if result.strip():
        print(f"[OK] Response: {result.strip()[:200]}")
    else:
        print("[FAIL] Empty response")
        return False
    return True


def test_chat_json():
    """Test JSON chat completion."""
    print("\nTesting chat_json...")
    client = OpenAIChatClient()
    brain = LLMBrain(client)
    
    result = brain.chat_json(
        system="You are a helpful assistant.",
        user="Reply with {\"status\": \"ok\"}",
    )
    
    if result:
        print(f"[OK] Response: {result}")
    else:
        print("[FAIL] Empty/invalid JSON response")
        return False
    return True


def test_raw_api():
    """Test raw API call to see full response structure."""
    print("\nTesting raw API call...")
    client = OpenAIChatClient()
    
    payload = {
        "model": client.model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello."},
        ],
        "temperature": 0.7,
        "n": 1,
    }
    
    response = client.create_chat_completion(**payload)
    print(f"Raw response: {response}")


if __name__ == "__main__":
    test_chat()
    test_chat_json()
    test_raw_api()