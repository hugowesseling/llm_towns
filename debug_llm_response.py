#!/usr/bin/env python3
"""Analyze llama-cpp response structure."""

import requests
import json
import sys


def get_raw_response():
    """Get raw response from llama-cpp server."""
    url = "http://192.168.1.117:8080/v1/chat/completions"
    payload = {
        "model": "models/Qwen_Qwen3.6-35B-A3B-Q2_K_L.gguf",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Reply with only: {\"test\": true}"},
            {"role": "user", "content": "Reply with only JSON: {\"test\": true}"},
        ],
        "temperature": 0.7,
        "max_tokens": 400,
        "n": 1,
    }

    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")

    result = response.json()

    print("\n=== RAW RESPONSE ===")
    print(json.dumps(result, indent=2))

    choices = result.get("choices", [])
    if choices:
        c = choices[0]
        print("\n=== choices[0] ===")
        print(json.dumps(c, indent=2))

        msg = c.get("message", {})
        print("\n=== message keys ===")
        print(list(msg.keys()))

        print("\n=== message.content ===")
        print(repr(msg.get("content", "")))

        print("\n=== message.reasoning_content ===")
        print(repr(msg.get("reasoning_content", "")))

        # Check for any other fields
        print("\n=== all message fields ===")
        for k, v in msg.items():
            print(f"  {k}: {repr(v[:100])}...")

        # Check finish_reason
        print(f"\n=== finish_reason ===")
        print(c.get("finish_reason"))

        # Check model field
        print(f"\n=== model field ===")
        print(result.get("model"))

        # Check if there's a separate 'response' or 'text' field at top level
        print(f"\n=== top-level keys ===")
        print(list(result.keys()))

        # Print the full reasoning content
        rc = msg.get("reasoning_content", "")
        if rc:
            print(f"\n=== full reasoning_content ({len(rc)} chars) ===")
            print(rc[:500])
            print("...")

        # Print full content
        content = msg.get("content", "")
        if content:
            print(f"\n=== full content ({len(content)} chars) ===")
            print(content[:500])


if __name__ == "__main__":
    get_raw_response()
