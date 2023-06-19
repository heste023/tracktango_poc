from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
from sqlalchemy.exc import OperationalError

load_dotenv()  # load environment variables from .env file

app = Flask(__name__)

# Configure your database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy(app)

# Define a model for your messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(500), nullable=False)
    sender = db.Column(db.String(50), nullable=False)

@app.route("/sms", methods=['POST'])
def sms_reply():
    # Get the message body and the sender number
    message_body = request.form.get('Body')
    sender_number = request.form.get('From')

    # Store message in the database
    message = Message(body=message_body, sender=sender_number)
    db.session.add(message)

    for attempt in range(5):  # try 5 times
        try:
            db.session.commit()
            break
        except OperationalError:
            db.session.rollback()
            if attempt == 4:  # if 5th attempt, raise the exception
                raise
            continue  # otherwise, try again

    resp = MessagingResponse()

    # A simple auto-reply (optional)
    resp.message("Your message has been received!")

    return str(resp)

@app.route('/')
def home():
    return "Still changin."

if __name__ == "__main__":
    app.run(debug=True)
