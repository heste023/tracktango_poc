import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
import io
import base64
from flask import Flask, request, Response, render_template
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
import os

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

    # Validate message_body and sender_number before continuing
    if not message_body or not sender_number:
        app.logger.error(f"Invalid data: message_body={message_body}, sender_number={sender_number}")
        return "Invalid data", 400

    # Store message in the database
    message = Message(body=message_body, sender=sender_number)
    db.session.add(message)

    for attempt in range(5):  # try 5 times
        try:
            db.session.commit()
            app.logger.info(f"Message from {sender_number} committed to database.")
            break
        except OperationalError as e:
            db.session.rollback()
            app.logger.error(f"Database commit failed on attempt {attempt+1}: {str(e)}")
            if attempt == 4:  # if 5th attempt, raise the exception
                raise
            continue  # otherwise, try again

    resp = MessagingResponse()

    # A simple auto-reply (optional)
    resp.message("Your message has been received!")

    return str(resp)

# get the directory of the current file
basedir = os.path.abspath(os.path.dirname(__file__))

@app.route('/')
def home():
    # your other code...

    # load the cleaned messages file
    cleaned_messages_path = os.path.join(basedir, 'cleaned_messages.csv')
    df = pd.read_csv(cleaned_messages_path)

    # Convert 'date' column to datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Define week start on Sunday and end on Saturday
    df['week'] = df['date'].dt.to_period('W-SAT').apply(lambda r: r.start_time)

    # Convert time to minutes
    df['time'] = df['time'].apply(lambda x: int(x.split()[0]) * 60 if 'hour' in x else int(x.split()[0]))

    # Compute total time and time per subject for each student per week
    total_time = df.groupby(['student', 'week'])['time'].sum()
    time_per_subject = df.groupby(['student', 'week', 'subject'])['time'].sum()

    # Convert to HTML
    total_time_html = total_time.to_frame().to_html()
    time_per_subject_html = time_per_subject.to_frame().to_html()

    # Render the HTML
    return render_template('summary.html', total_time_table=total_time_html,
                           time_per_subject_table=time_per_subject_html)


if __name__ == "__main__":
    app.run(debug=True)
