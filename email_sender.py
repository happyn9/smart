# email_sender.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

FROM_EMAIL = os.getenv("EMAIL_ADDRESS")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_email(to_email, subject, body, html=True):
    """Envoie un email via SendGrid."""
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=body if html else None,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return None

# 1️⃣ Email de création de compte
def send_account_creation_email(user_name, user_email):
    subject = "Bienvenue sur SmartCard!"
    body = f"""
    <p>Bonjour {user_name},</p>
    <p>Votre compte a été créé avec succès.</p>
    <p>Merci de nous faire confiance!</p>
    """
    return send_email(user_email, subject, body)

# 2️⃣ Email de connexion
def send_login_notification_email(user_name, user_email):
    subject = "Connexion à votre compte"
    body = f"""
    <p>Bonjour {user_name},</p>
    <p>Nous avons remarqué que vous vous êtes connecté à votre compte {user_email}.</p>
    <p>Si ce n'était pas vous, veuillez contacter notre support immédiatement.</p>
    """
    return send_email(user_email, subject, body)

# 3️⃣ Email de notification de commande à l’admin
def send_admin_commande_email(user_name, user_email, commande_id, qr_link=None):
    subject = f"Nouvelle commande #{commande_id}"
    link = f"http://192.168.0.104:5173/commandes/{commande_id}/view"
    body = f"""
    <p>Bonjour Admin,</p>
    <p>L'utilisateur <strong>{user_name}</strong> ({user_email}) a passé une commande.</p>
    <p>Cliquez sur le lien ci-dessous pour voir l'aperçu et imprimer la carte :<br>
       <a href="{link}" target="_blank">{link}</a>
    </p>
    """
    if qr_link:
        body += f'<p>Voici le QR Code généré pour la commande :<br><img src="{qr_link}" alt="QR Code"></p>'
    body += "<p>Merci.</p>"

    return send_email(ADMIN_EMAIL, subject, body)
