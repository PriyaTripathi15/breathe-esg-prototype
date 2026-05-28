from django.contrib.auth.models import User
from django.core import signing


TOKEN_SALT = "breathe-esg-demo-auth"
TOKEN_MAX_AGE = 60 * 60 * 24 * 7


def create_demo_token(user: User) -> str:
    payload = {
        "username": user.username,
        "email": user.email,
        "full_name": user.get_full_name() or user.username,
    }
    return signing.dumps(payload, salt=TOKEN_SALT)


def decode_demo_token(token: str):
    return signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)


def extract_bearer_token(request):
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Demo-Token", "").strip() or request.query_params.get("token", "").strip()


def get_demo_user_from_request(request):
    token = extract_bearer_token(request)
    if not token:
        return None

    try:
        payload = decode_demo_token(token)
    except signing.BadSignature:
        return None

    return User.objects.filter(username=payload.get("username")).first()