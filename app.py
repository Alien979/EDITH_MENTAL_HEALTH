from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from services import cohere_service, openai_service, pinecone_service

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\User\\Desktop\\language\\EDITH_MENTAL_HEALTH\\database.db' # Adjust this as needed
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Autogenerated unique ID for each entry
    user_id = db.Column(db.String)  # User ID can repeat across entries
    user_message = db.Column(db.String)
    openai_response = db.Column(db.String)
    cohere_response = db.Column(db.String)

pinecone_service.check_index()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    history = ''
    if request.method == 'GET':
        # Get the conversation history from the database
        history = ChatHistory.query.filter_by(user_id=user_id).all()
    elif request.method == 'POST':
        message = request.form['message']

        
        # Generate responses with OpenAI and Cohere
        openai_response = openai_service.generate_response(message)
        cohere_response = cohere_service.get_response(message)
        if cohere_response == "Sorry, I couldn't process that request.":
            cohere_response = "" # or you can set it to None, depending on your preference


        # Update the conversation history in the database
        new_message = ChatHistory(
            user_id=user_id,
            user_message=message,
            openai_response=openai_response,
            cohere_response=cohere_response
        )

        db.session.add(new_message)
        db.session.commit()

        # Update the embeddings in Pinecone
        pinecone_service.update_vectors(user_id, message, openai_response, cohere_response)

        history = ChatHistory.query.filter_by(user_id=user_id).all()

    return render_template('chat.html', history=history)

if __name__ == "__main__":
    app.run(debug=True)