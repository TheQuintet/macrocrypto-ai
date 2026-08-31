"""Python examples for exports endpoints."""

import requests
import json

# ============================================
# BASE URL
# ============================================

BASE_URL = "http://localhost:8000/api/v1"


# ============================================
# 1. EXPORT PREDICTIONS AS CSV
# ============================================

def export_predictions_csv(access_token):
    """Export predictions as CSV."""
    url = f"{BASE_URL}/export"
    params = {
        "export_type": "predictions",
        "format": "csv",
        "timeframe": "24h"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Export Status: {response.status_code}")
    
    if response.status_code == 200:
        # Save to file
        with open("predictions.csv", "wb") as f:
            f.write(response.content)
        print("✅ CSV saved to predictions.csv")
        
        # Show first few lines
        content = response.text
        lines = content.split("\n")[:5]
        print("First lines:")
        for line in lines:
            print(f"  {line}")
    else:
        print(f"Error: {response.text}")
    return response

# Output: CSV file with headers and prediction data


# ============================================
# 2. EXPORT PREDICTIONS AS PNG
# ============================================

def export_predictions_png(access_token):
    """Export predictions as PNG chart."""
    url = f"{BASE_URL}/export"
    params = {
        "export_type": "predictions",
        "format": "png",
        "timeframe": "24h"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Export Status: {response.status_code}")
    
    if response.status_code == 200:
        # Save to file
        with open("predictions.png", "wb") as f:
            f.write(response.content)
        print("✅ PNG saved to predictions.png")
    else:
        print(f"Error: {response.text}")
    return response

# Output: PNG image file


# ============================================
# 3. EXPORT PREDICTIONS AS PDF
# ============================================

def export_predictions_pdf(access_token):
    """Export predictions as PDF report."""
    url = f"{BASE_URL}/export"
    params = {
        "export_type": "predictions",
        "format": "pdf",
        "timeframe": "24h"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"Export Status: {response.status_code}")
    
    if response.status_code == 200:
        # Save to file
        with open("predictions.pdf", "wb") as f:
            f.write(response.content)
        print("✅ PDF saved to predictions.pdf")
    else:
        print(f"Error: {response.text}")
    return response

# Output: PDF document with chart and summary


# ============================================
# 4. GET EXPORT HISTORY
# ============================================

def get_export_history(access_token):
    """Get export history."""
    url = f"{BASE_URL}/export/history"
    params = {"limit": 10}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, params=params, headers=headers)
    print(f"History Status: {response.status_code}")
    data = response.json()
    print(f"Total Exports: {data.get('total', 0)}")
    for item in data.get("items", []):
        print(f"  {item.get('id')}: {item.get('export_type')} - {item.get('format')} ({item.get('status')})")
    return data

# Output:
# {
#   "total": 3,
#   "limit": 10,
#   "offset": 0,
#   "items": [...]
# }


# ============================================
# 5. DOWNLOAD PREVIOUS EXPORT
# ============================================

def download_export(access_token, export_id):
    """Download a previous export by ID."""
    url = f"{BASE_URL}/export/{export_id}/download"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    print(f"Download Status: {response.status_code}")
    
    if response.status_code == 200:
        # Save to file
        filename = f"export_{export_id}.csv"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ File saved to {filename}")
    else:
        print(f"Error: {response.text}")
    return response