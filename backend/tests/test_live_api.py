import json
import urllib.parse
import urllib.request
import uuid


def test_api():
    print("Testing upload...")
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"test.csv\"\r\n"
        f"Content-Type: text/csv\r\n\r\n"
        f"col1,col2\n1,2\n3,4\n\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/datasets/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        resp_text = response.read().decode('utf-8')
        print(response.status, resp_text)
        ds_id = json.loads(resp_text)["dataset_id"]
        
    print("Testing get...")
    req2 = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/datasets/{ds_id}")
    try:
        with urllib.request.urlopen(req2) as response:
            print(response.status, response.read().decode('utf-8'))
    except Exception as e:  # noqa: BLE001
        print("Error on get:", e)
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))

if __name__ == "__main__":
    test_api()
