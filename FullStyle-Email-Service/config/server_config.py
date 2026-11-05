import os
from dotenv import load_dotenv

def configure_app(app):
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env')) # Load .env from root
    # Add any specific configurations for the email service app
    app.config['RABBITMQ_URL'] = os.environ.get('RABBITMQ_URL')
    app.config['RESEND_API_KEY'] = os.environ.get('RESEND_API_KEY')
