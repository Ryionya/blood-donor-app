# Run this once: python generate_cities.py
import json
import requests

# Using PSGC API to get all Philippine cities and municipalities
url = "https://psgc.gitlab.io/api/cities-municipalities/"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    cities = sorted([item['name'].title() for item in data])
    
    with open('static/data/ph_cities.json', 'w') as f:
        json.dump({'cities': cities}, f)
    
    print(f"Saved {len(cities)} cities!")

except Exception as e:
    print(f"Error: {e}")
    # Fallback — common Philippine cities
    cities = [
        "Calamba", "Santa Rosa", "Biñan", "Cabuyao", "San Pedro",
        "Antipolo", "Quezon City", "Manila", "Makati", "Pasig",
        "Taguig", "Mandaluyong", "Marikina", "Pasay", "Parañaque",
        "Las Piñas", "Muntinlupa", "Valenzuela", "Malabon", "Navotas",
        "Caloocan", "San Juan", "Pateros", "Cebu City", "Davao City",
        "Cagayan de Oro", "Zamboanga City", "General Santos", "Iloilo City",
        "Bacolod", "Baguio", "Angeles", "Olongapo", "San Fernando",
        "Lipa", "Batangas City", "Lucena", "Cabanatuan", "San Jose del Monte",
        "Malolos", "Meycauayan", "Marilao", "Cavite City", "Bacoor",
        "Dasmariñas", "Imus", "Tagaytay", "Trece Martires",
        "Los Baños", "Bay", "Victoria", "Magdalena", "Majayjay",
        "Nagcarlan", "Liliw", "San Pablo", "Calauan", "Calamba",
    ]
    with open('static/data/ph_cities.json', 'w') as f:
        json.dump({'cities': sorted(set(cities))}, f)
    print(f"Saved {len(cities)} fallback cities!")