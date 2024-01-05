
# Initialize Flask application
from flask import Flask, render_template, request, jsonify, send_file
from google.cloud import texttospeech
import openai
from openai.error import ServiceUnavailableError
from openai.error import APIConnectionError
import logging
import os
import uuid
import base64
from flask_cors import cross_origin
from openai.error import RateLimitError
import logging
import api_keys

# Initialize Flask application
app = Flask(__name__)

# Dictionaries to store logs
logs = {}  # A dictionary with usernames as keys and logs as values.
assistant_logs = {}  # A dictionary that retains Assistant's response content with usernames as keys.

# Specify the path to the service account key file.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gtts.json"

# Instantiates a client
client = texttospeech.TextToSpeechClient()

# Set OpenAI API key
openai.api_key = api_keys.openai_key

# System-wide variables
EXIT_PHRASE = 'exit'

# Initial user message
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': f'just return {EXIT_PHRASE} only'}
]

# Set up logging
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

def synthesize_text(text):
    '''
    Function to synthesize text to speech using Google Text-to-Speech API
    text: text from ChatGPT

    return: audio file
    '''
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(
        ssml="<speak><break time='800ms'/>" + text + "</speak>"
    )

    # Build the voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    # Return the binary audio file.
    return response.audio_content

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to recognize audio using OpenAI API
@app.route('/recognize', methods=['POST'])
def recognize():
    audio = request.files['audio']
    transcription = openai.Audio.transcribe('whisper-1', audio)
    return transcription['text']

# Route for the chat functionality
@app.route('/chat', methods=['POST'])
@cross_origin()  # This will enable CORS for the /chat route only
def chat():

    data = request.get_json()
    text = data.get('text')
    username = data.get('username')
    #print("Username python: {}".format(username))    

    # Check if username is provided
    if username is None or username.strip() == '':
        audio_base64 = base64.b64encode(synthesize_text("input username")).decode('utf-8')
        return jsonify({
            'text': "Please input username",
            'audio': audio_base64
        })
    
    # Store logs for each username.
    if username not in logs:
        logs[username] = []
        logs[username].append({'role': 'user', 'content': text})
    else:
    # Delete the oldest log if the number of logs exceeds 18.
        if len(logs[username]) >= 18:
            logs[username] = logs[username][-17:]  # Store last 17 logs

    # Log recognition information
    logs[username].append({'role': 'user', 'content': text})

    app.logger.info("Recognizing of,{},{}".format(username, text))

    # Create messages for OpenAI API
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': f'just return {EXIT_PHRASE} only'}
    ]
    messages.append(
        {'role': 'user', 'content': text}
    )

    # Add user logs to messages
    if username in logs:
        messages += logs[username]

    # Log user logs
    app.logger.info("userlogs: {}, {}".format(username, logs[username]))
    
    try:
        # Make a request to OpenAI API for chat completion
        result = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=1024
        )
    except RateLimitError:
        return jsonify(text="Too much usage, please wait a moment.")
    except ServiceUnavailableError as e:
        return jsonify(text="The server is overloaded. Please wait a moment and try again.")
    except APIConnectionError as e:
        return jsonify(text="An error occurred during communication. Please wait a moment and try again.")
    except Exception as e:
        return jsonify(text="An unexpected error has occurred. Please contact the support team for assistance.")
    else:
        # Extract Assistant's response text
        response_text = result['choices'][0]['message']['content']
        # Add the response content of the Assistant to the log.
        logs[username].append({'role': 'assistant', 'content': response_text})

    # Log Assistant's answer
    app.logger.info("Answering for,{},{}".format(username, response_text))

    # Encode the response audio to base64
    audio_base64 = base64.b64encode(synthesize_text(response_text)).decode('utf-8')

    return jsonify({
        'text': response_text,
        'audio': audio_base64
    })
    #return response_text

# Run the application if it is executed as the main script
if __name__ == '__main__':
    app.run(port=8080)
    #app.run()