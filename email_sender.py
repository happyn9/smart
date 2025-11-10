import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

FROM_EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

def send_email(to_email, subject, body, html=False):
    """Envoie un email (texte ou HTML) via Gmail."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    part = MIMEText(body, "html" if html else "plain")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())


def send_email_confirmation(email, name):
    """Email de bienvenue pour un nouvel utilisateur."""
    subject = "Bienvenue 👋"
    body = f"""
    <p>Bonjour <strong>{name}</strong>,</p>
    <p>Votre compte a été bien créé.</p>
    <p>Vous pouvez maintenant prendre un rendez-vous.</p>
    """
    send_email(email, subject, body, html=True)


def send_admin_commande_email(user_name, user_email, commande_id):
    """Email de notification à l’admin pour une nouvelle commande."""
    subject = f"Nouvelle commande #{commande_id}"
    link = f"http://192.168.0.104:5173/commandes/{commande_id}/view"
    body = f"""
    <p>Bonjour Admin,</p>

    <p>L'utilisateur <strong>{user_name}</strong> ({user_email}) a passé une commande.</p>

    <p>
        Cliquez sur le lien ci-dessous pour voir l'aperçu et imprimer la carte :<br>
        <a href="{link}" target="_blank">{link}</a>
    </p>

    <p>Merci.</p>
    """
    send_email(ADMIN_EMAIL, subject, body, html=True)
