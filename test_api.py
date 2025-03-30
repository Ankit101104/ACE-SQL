import requests
import json
import time

def test_health():
    url = 'http://127.0.0.1:8000/api/health'
    try:
        response = requests.get(url)
        print(f"Health Check Status Code: {response.status_code}")
        print(f"Health Check Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Check Error: {str(e)}")
        return False

def test_query():
    url = 'http://127.0.0.1:8000/api/generate'
    headers = {'Content-Type': 'application/json'}
    data = {'query': 'Show me total sales by region'}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\nQuery Status Code: {response.status_code}")
        print(f"Query Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"\nQuery Error: {str(e)}")

if __name__ == "__main__":
    # Wait for server to be ready
    print("Checking server health...")
    time.sleep(2)  # Give the server a moment to start
    
    if test_health():
        print("\nServer is healthy, testing query endpoint...")
        test_query()
    else:
        print("\nServer health check failed, please check if the server is running.") 