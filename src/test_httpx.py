
import httpx
import sys

url = "http://localhost:8000/api/v1/agents"
print(f"Testing {url}...")
try:
    with httpx.Client() as client:
        resp = client.get(url)
        print(f"Status: {resp.status_code}")
        print(resp.text[:100])
except Exception as e:
    print(f"Error: {e}")

print("-" * 20)
print("Testing with trust_env=False...")
try:
    with httpx.Client(trust_env=False) as client:
        resp = client.get(url)
        print(f"Status: {resp.status_code}")
        print(resp.text[:100])
except Exception as e:
    print(f"Error: {e}")
