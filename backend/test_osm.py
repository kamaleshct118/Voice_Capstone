import httpx

client = httpx.Client(timeout=15)
headers={'User-Agent': 'VoiceMedicalAssistant/1.0'}
resp = client.get('https://nominatim.openstreetmap.org/search', params={'q': 'Chennai', 'format': 'json', 'limit': 1}, headers=headers)
print('Geo STATUS:', resp.status_code)
lat = resp.json()[0]['lat']
lng = resp.json()[0]['lon']

overpass_query = f"""
[out:json];
(
  node["amenity"="hospital"](around:8000,{lat},{lng});
  node["amenity"="clinic"](around:8000,{lat},{lng});
);
out body 5;
"""
resp2 = client.post('https://overpass-api.de/api/interpreter', data={"data": overpass_query}, headers=headers)
print('Overpass STATUS:', resp2.status_code)
print(resp2.text[:200])
