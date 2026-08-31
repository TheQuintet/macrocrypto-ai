"""Python examples for WebSocket real-time price updates."""

import asyncio
import websockets
import json


# ============================================
# 1. CONNECT TO WEBSOCKET (guest)
# ============================================

async def websocket_guest():
    """Connect to WebSocket as guest."""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket (guest)")
        
        # Receive welcome message
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}: {data.get('message', '')}")
        
        # Receive initial price update
        response = await websocket.recv()
        data = json.loads(response)
        print(f"💰 Price: ${data.get('data', {}).get('price', 0):,.2f}")
        
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}")
        
        # Keep connection alive
        for i in range(5):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                if data.get('type') == 'price_update':
                    price = data.get('data', {}).get('price', 0)
                    print(f"💰 Price update: ${price:,.2f}")
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send(json.dumps({"type": "ping"}))

# Run: asyncio.run(websocket_guest())


# ============================================
# 2. CONNECT TO WEBSOCKET (authenticated)
# ============================================

async def websocket_auth(access_token):
    """Connect to WebSocket with authentication."""
    uri = f"ws://localhost:8000/ws?token={access_token}"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket (authenticated)")
        
        # Receive welcome message with user info
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}: {data.get('message', '')}")
        print(f"👤 User ID: {data.get('user_id')}")
        
        # Subscribe to updates
        await websocket.send(json.dumps({"type": "subscribe"}))
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}: {data.get('message', '')}")
        
        # Listen for price updates
        for i in range(10):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                if data.get('type') == 'price_update':
                    price_data = data.get('data', {})
                    print(f"💰 BTC: ${price_data.get('price', 0):,.2f} "
                          f"({price_data.get('change_24h_percent', 0):+.2f}%)")
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({"type": "ping"}))


# ============================================
# 3. WEBSOCKET WITH HEARTBEAT
# ============================================

async def websocket_with_heartbeat():
    """Connect to WebSocket with automatic heartbeat."""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")
        
        # Receive welcome
        response = await websocket.recv()
        print(f"📩 {json.loads(response).get('message')}")
        
        # Heartbeat loop
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                if data.get('type') == 'price_update':
                    price = data.get('data', {}).get('price', 0)
                    print(f"💰 Price: ${price:,.2f}")
                elif data.get('type') == 'ping':
                    await websocket.send(json.dumps({"type": "pong"}))
                    print("💓 Heartbeat")
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({"type": "ping"}))
                print("💓 Ping sent")

# Run: asyncio.run(websocket_with_heartbeat())


# ============================================
# 4. WEBSOCKET STATUS
# ============================================

def get_websocket_status():
    """Get WebSocket connection status."""
    import requests
    response = requests.get("http://localhost:8000/ws/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

# Output:
# {
#   "active_connections": 1,
#   "user_connections": 1,
#   "status": "operational",
#   "timestamp": "..."
# }