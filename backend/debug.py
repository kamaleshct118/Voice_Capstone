import requests

files = {
    'mode': (None, 'image+text'),
    'medicine_name': (None, 'hello'),
    'image': ('test.png', b'notanimage', 'image/png')
}

res = requests.post("http://localhost:8000/api/classify-medicine", files=files)
print(res.status_code)
print(res.text)
