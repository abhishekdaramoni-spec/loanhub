from flask import current_app
from flask_mail import Message
from app.utils.extensions import mail

def send_async_email(subject, recipient, body_text, body_html=None):
    """Sends email. Catches exceptions if SMTP is not configured and prints to console instead."""
    msg = Message(subject, recipients=[recipient])
    msg.body = body_text
    if body_html:
        msg.html = body_html
    try:
        if current_app.config.get('MAIL_USERNAME'):
            mail.send(msg)
        else:
            print("\n--- [MOCK MAIL SENDER] ---")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body_text}")
            print("---------------------------\n")
    except Exception as e:
        print(f"Mail delivery failed: {e}. Outputting message below:")
        print(f"Subject: {subject} | To: {recipient}\n{body_text}")
