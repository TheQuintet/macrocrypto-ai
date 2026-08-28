```markdown
# WebSocket Guide

This guide explains how to use WebSocket connections for real-time price updates.

## Overview

The WebSocket endpoint provides real-time BTC price updates and alerts. It follows an event-driven architecture where price updates are consumed from RabbitMQ and broadcast to all connected WebSocket clients.

## Connection

### Endpoint

```
ws://localhost:8000/ws
```

### Authentication (Optional)

```bash
wscat -c "ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN"
```

### Without Authentication

```bash
wscat -c "ws://localhost:8000/ws"
```

## Message Types

### Server → Client

#### Connection Message

Sent immediately after connection:

```json
{
  "type": "connection",
  "status": "connected",
  "user_id": null,
  "message": "Connected to MacroCrypto AI WebSocket",
  "timestamp": "2026-08-28T..."
}
```

#### Price Update

Sent when a new price is received from RabbitMQ:

```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC",
    "price": 45000.00,
    "change_24h_percent": 2.5,
    "volume": 1500000.00,
    "timestamp": "2026-08-28T..."
  },
  "timestamp": "2026-08-28T..."
}
```

#### Heartbeat (Ping)

Sent periodically to keep the connection alive:

```json
{
  "type": "ping"
}
```

#### Alert

Sent when an alert is triggered:

```json
{
  "type": "alert",
  "data": {
    "alert_id": 1,
    "message": "BTC price alert",
    "type": "price_alert"
  },
  "timestamp": "2026-08-28T..."
}
```

### Client → Server

#### Ping (Heartbeat Response)

Send to keep the connection alive:

```json
{
  "type": "ping"
}
```

#### Subscribe to Updates

```json
{
  "type": "subscribe"
}
```

#### Unsubscribe from Updates

```json
{
  "type": "unsubscribe"
}
```

## Python Example

```python
import asyncio
import websockets
import json

async def connect_websocket(access_token=None):
    """Connect to WebSocket with optional authentication."""
    
    # Build URI
    uri = "ws://localhost:8000/ws"
    if access_token:
        uri += f"?token={access_token}"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")
        
        # Receive welcome message
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}: {data.get('message', '')}")
        
        # Subscribe to updates
        await websocket.send(json.dumps({"type": "subscribe"}))
        
        # Listen for updates
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                
                if data.get('type') == 'price_update':
                    price_data = data.get('data', {})
                    print(f"💰 BTC: ${price_data.get('price', 0):,.2f} "
                          f"({price_data.get('change_24h_percent', 0):+.2f}%)")
                elif data.get('type') == 'ping':
                    await websocket.send(json.dumps({"type": "pong"}))
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send(json.dumps({"type": "ping"}))

# Run
asyncio.run(connect_websocket())
```

## JavaScript Example

```javascript
// Connect to WebSocket
const token = 'YOUR_ACCESS_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

// Connection opened
ws.onopen = function(event) {
  console.log('✅ Connected to WebSocket');
  
  // Subscribe to updates
  ws.send(JSON.stringify({ type: 'subscribe' }));
};

// Listen for messages
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connection':
      console.log(`📩 ${data.message}`);
      break;
      
    case 'price_update':
      const priceData = data.data;
      console.log(`💰 BTC: $${priceData.price.toFixed(2)} ` +
                  `(${priceData.change_24h_percent.toFixed(2)}%)`);
      break;
      
    case 'ping':
      // Respond to heartbeat
      ws.send(JSON.stringify({ type: 'pong' }));
      break;
      
    case 'alert':
      console.log(`🔔 Alert: ${data.data.message}`);
      break;
  }
};

// Connection closed
ws.onclose = function(event) {
  console.log('❌ Disconnected from WebSocket');
};

// Connection error
ws.onerror = function(error) {
  console.error('WebSocket Error:', error);
};

// Send heartbeat periodically
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 25000);
```

## cURL Example (with wscat)

### Install wscat

```bash
npm install -g wscat
```

### Connect without Authentication

```bash
wscat -c "ws://localhost:8000/ws"
```

### Connect with Authentication

```bash
# First, get a token
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"SecurePass123!"}' | jq -r '.access_token')

# Connect to WebSocket
wscat -c "ws://localhost:8000/ws?token=$TOKEN"
```

### Send Messages

Once connected, you can send messages:

```json
{"type": "ping"}
{"type": "subscribe"}
{"type": "unsubscribe"}
```

## WebSocket Status

Check the WebSocket connection status:

```bash
curl http://localhost:8000/ws/status | jq
```

Response:
```json
{
  "active_connections": 3,
  "user_connections": 2,
  "status": "operational",
  "timestamp": "2026-08-28T..."
}
```

## Error Handling

### Connection Errors

```python
try:
    async with websockets.connect(uri) as websocket:
        # ... use websocket
except websockets.exceptions.ConnectionClosed as e:
    print(f"Connection closed: {e}")
except websockets.exceptions.WebSocketException as e:
    print(f"WebSocket error: {e}")
```

### Reconnection Logic

```python
async def connect_with_retry(max_retries=5):
    for attempt in range(max_retries):
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ Connected (attempt {attempt + 1})")
                await handle_connection(websocket)
                return
        except websockets.exceptions.ConnectionClosed:
            wait_time = 2 ** attempt
            print(f"❌ Connection lost, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    print("❌ Failed to connect after max retries")
```

## Best Practices

1. **Handle reconnection**: Always implement reconnection logic
2. **Use heartbeat**: Send ping/pong to keep connection alive
3. **Subscribe after connection**: Don't assume subscription persists
4. **Handle errors gracefully**: Log errors and attempt recovery
5. **Close connections properly**: Clean up when done

## Rate Limits

The WebSocket endpoint is not rate limited, but individual REST API endpoints are.

## Connection Status Codes

| Status | Description |
|--------|-------------|
| `CONNECTING` | Connection is being established |
| `OPEN` | Connection is open and ready |
| `CLOSING` | Connection is closing |
| `CLOSED` | Connection is closed |

## Message Flow Diagram

```
Client → WebSocket → API Gateway → RabbitMQ → Data Service
                    ↑                           ↓
                    └───────────────────────────┘
                             (Price Updates)
```

## WebSocket Security

1. **Authentication**: Optional JWT token via query parameter
2. **Rate Limiting**: Not applied to WebSocket
3. **Data Validation**: All messages are validated
4. **Connection Limits**: Configurable max connections
5. **Heartbeat**: Prevents stale connections

## Troubleshooting

### Connection Refused

```bash
# Check if service is running
curl http://localhost:8000/health

# Check WebSocket status
curl http://localhost:8000/ws/status
```

### Authentication Failed

Make sure your token is valid and not expired:

```bash
# Refresh your token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### No Messages Received

1. Ensure you're subscribed: send `{"type": "subscribe"}`
2. Check if price updates are being published
3. Verify RabbitMQ consumer is running

### Connection Dropping

1. Implement reconnection logic
2. Send periodic ping messages
3. Check network connectivity
```