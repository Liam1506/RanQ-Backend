import uuid
import os
from supabase import Client

from auth.sendVerifyMail import send_verify_mail


def get_user_by_username(client: Client, username: str):
    response = client.table("users").select("id, username, email, password, verified, admin").eq("username", username).execute()
    return response.data[0] if response.data else None


def get_user_by_email(client: Client, email: str):
    response = client.table("users").select("id, username, email, password, verified, admin").eq("email", email).execute()
    return response.data[0] if response.data else None


def insert_user(client: Client, username: str, email: str, hashed_password: str):
    user_id = str(uuid.uuid4())
    skip_verification = os.environ.get("SKIP_EMAIL_VERIFICATION", "false").lower() == "true"

    client.table("users").insert({
        "id": user_id,
        "username": username,
        "email": email,
        "password": hashed_password,
        "verified": True if skip_verification else False,
        "admin": False,
    }).execute()

    if not skip_verification:
        verify_hash = str(uuid.uuid4())
        client.table("verificationWaitlist").insert({
            "id": user_id,
            "verifyId": verify_hash,
        }).execute()
        send_verify_mail(email, user_id, verify_hash)

    return user_id


def verify_user(client: Client, userId: str, verifyId: str):
    response = client.table("verificationWaitlist").select("id").eq("id", userId).eq("verifyId", verifyId).execute()

    if not response.data:
        return False

    client.table("users").update({"verified": True}).eq("id", userId).execute()
    client.table("verificationWaitlist").delete().eq("id", userId).execute()
    return True
