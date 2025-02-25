import json
import boto3
import base64
import os
from urllib.parse import parse_qs
from datetime import datetime

# -------------------- CONFIG --------------------
S3_BUCKET = os.environ.get("SECRETS_BUCKET", "my-secrets-bucket-123456")
s3 = boto3.client("s3")

# Hard-coded users and passwords
USERS = {
    "alice": "password1",
    "bob":   "password2",
    "carol": "12345"   # admin example
}

# Admin users have full access to all secrets
ADMINS = {"carol"}

# Load the HTML page content
def load_html():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r") as file:
        return file.read()

# -------------------- PYTHON BACKEND --------------------
def check_auth(event):
    headers = event.get("headers") or {}
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return False, None
    try:
        encoded = auth_header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
        if USERS.get(username) == password:
            return True, username
    except Exception:
        pass
    return False, None

def is_admin(user: str) -> bool:
    return user in ADMINS

def get_metadata(key):
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        meta = head.get("Metadata", {})
        owner = meta.get("owner", "")
        updates_str = meta.get("updates", "[]")
        updates = json.loads(updates_str)
        return owner, updates
    except s3.exceptions.NoSuchKey:
        return None, None
    except Exception:
        return None, None

def user_can_access(key, user):
    if is_admin(user):
        return True
    owner, _ = get_metadata(key)
    if owner is None:
        return False
    return owner == user

def put_object_with_metadata(key, content, owner, updates):
    updates_str = json.dumps(updates)
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=content,
        ServerSideEncryption="AES256",
        Metadata={
            "owner": owner,
            "updates": updates_str
        }
    )

def lambda_handler(event, context):
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": load_html()
        }
    authorized, current_user = check_auth(event)
    if not authorized:
        return {
            "statusCode": 401,
            "headers": {"WWW-Authenticate": 'Basic realm="GardenOfSecrets"'},
            "body": "Unauthorized"
        }
    params = parse_qs(event.get("rawQueryString", ""))
    if path == "/list" and method == "GET":
        try:
            resp = s3.list_objects_v2(Bucket=S3_BUCKET)
            contents = resp.get("Contents", [])
            secrets_info = []
            for obj in contents:
                key = obj["Key"]
                owner, _ = get_metadata(key)
                if owner is None:
                    continue
                if is_admin(current_user) or (owner == current_user):
                    secrets_info.append({
                        "Key": key,
                        "LastModified": obj["LastModified"].isoformat(),
                        "Size": obj["Size"]
                    })
            return {"statusCode": 200, "body": json.dumps(secrets_info)}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    elif path == "/get" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            content = obj["Body"].read().decode("utf-8")
            return {"statusCode": 200, "body": content}
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "Not found"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/meta" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        owner, updates = get_metadata(key)
        if owner is None:
            return {"statusCode": 404, "body": "Not found"}
        return {"statusCode": 200, "body": json.dumps({"Owner": owner, "Updates": updates})}
    elif path == "/create" and method == "POST":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=key)
            return {"statusCode": 409, "body": "Secret key already exists"}
        except s3.exceptions.ClientError:
            pass
        content = event.get("body", "") or ""
        updates = [{
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "create"
        }]
        try:
            put_object_with_metadata(key, content, current_user, updates)
            return {"statusCode": 201, "body": "Created"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/save" and method == "POST":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        content = event.get("body", "") or ""
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            meta = head.get("Metadata", {})
            owner = meta.get("owner", current_user)
            updates = json.loads(meta.get("updates", "[]"))
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "No existing secret to update"}
        updates.append({
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": "update"
        })
        try:
            put_object_with_metadata(key, content, owner, updates)
            return {"statusCode": 200, "body": "Updated"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/delete" and method == "DELETE":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=key)
            return {"statusCode": 200, "body": "Deleted"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
    elif path == "/exists" and method == "GET":
        key = params.get("key", [""])[0]
        if not key:
            return {"statusCode": 400, "body": "Missing 'key' param"}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=key)
        except s3.exceptions.ClientError:
            return {"statusCode": 404, "body": "Key not found"}
        if not user_can_access(key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        return {"statusCode": 200, "body": "Key exists"}
    elif path == "/rename" and method == "POST":
        old_key = params.get("oldKey", [""])[0]
        new_key = params.get("newKey", [""])[0]
        if not old_key or not new_key:
            return {"statusCode": 400, "body": "Missing 'oldKey' or 'newKey' param"}
        if not user_can_access(old_key, current_user):
            return {"statusCode": 403, "body": "Forbidden"}
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=old_key)
            old_content = obj["Body"].read()
            head = s3.head_object(Bucket=S3_BUCKET, Key=old_key)
            meta = head.get("Metadata", {})
            owner = meta.get("owner", current_user)
            updates = json.loads(meta.get("updates", "[]"))
        except s3.exceptions.NoSuchKey:
            return {"statusCode": 404, "body": "Old key not found"}
        except Exception as e:
            return {"statusCode": 500, "body": str(e)}
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=new_key)
            return {"statusCode": 409, "body": "New key already exists"}
        except s3.exceptions.ClientError:
            pass
        updates.append({
            "user": current_user,
            "time": datetime.utcnow().isoformat() + "Z",
            "action": f"rename to {new_key}"
        })
        try:
            put_object_with_metadata(new_key, old_content, owner, updates)
        except Exception as e:
            return {"statusCode": 500, "body": f"Failed to create new key: {str(e)}"}
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=old_key)
        except Exception as e:
            return {"statusCode": 500, "body": f"New created, but failed to delete old: {str(e)}"}
        return {"statusCode": 200, "body": "Rename successful"}
    return {"statusCode": 404, "body": "Not found"}
