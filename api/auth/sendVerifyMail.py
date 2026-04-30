import resend
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

resend.api_key = os.environ["RESEND_API_KEY"]


def send_verify_mail(to_email: str, user_id: str, verify_id: str):
    verify_url = f"{os.environ['BASE_URL']}/api/auth/verify?userId={user_id}&verifyId={verify_id}"

    resend.Emails.send({
        "from": os.environ["MAIL_FROM"],
        "to": to_email,
        "subject": "Verify your account",
        "html": f'<p>Click <a href="{verify_url}">here</a> to verify your account.</p>',
    })
