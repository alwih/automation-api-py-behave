# Test data configuration

BASE_URL = "https://jsonplaceholder.typicode.com"

# Request payloads
POST_PAYLOAD = {
    "title": "Test Post",
    "body": "This is a test post",
    "userId": 1
}

PUT_PAYLOAD = {
    "id": 1,
    "title": "Updated Post",
    "body": "This post has been updated",
    "userId": 1
}

PATCH_PAYLOAD = {
    "title": "Patched Title"
}
