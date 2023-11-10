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

app = Flask(__name__)
logs = {}  # ユーザーネームをキー、ログを値とする辞書
assistant_logs = {}  # Assistantの応答内容をユーザー名をキーとして保持する辞書

# サービスアカウントキーファイルへのパスを指定します。
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gtts.json"

# Instantiates a client
client = texttospeech.TextToSpeechClient()

openai.api_key = api_keys.openai_key

EXIT_PHRASE = 'exit'

messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': f'just return {EXIT_PHRASE} only'}
]

# get instance of logger and set log severity as defined by the cli parameter
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

def synthesize_text(text):
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    audio = request.files['audio']
    transcription = openai.Audio.transcribe('whisper-1', audio)
    return transcription['text']

@app.route('/chat', methods=['POST'])
@cross_origin()  # This will enable CORS for the /chat route only
def chat():

    data = request.get_json()
    text = data.get('text')
    username = data.get('username')
    #print("Username python: {}".format(username))    

    if username is None or username.strip() == '':
        audio_base64 = base64.b64encode(synthesize_text("input username")).decode('utf-8')
        return jsonify({
            'text': "Please input username",
            'audio': audio_base64
        })
    
    # ユーザーネームごとにログを保管
    if username not in logs:
        logs[username] = []
        logs[username].append({'role': 'user', 'content': text})
    else:
    # ログが18件を超えた場合は、古いログを削除
        if len(logs[username]) >= 18:
            logs[username] = logs[username][-17:]  # 最新の17件を保持

    logs[username].append({'role': 'user', 'content': text})

    app.logger.info("Recognizing of,{},{}".format(username, text))

    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': f'just return {EXIT_PHRASE} only'}
    ]
    messages.append(
        {'role': 'user', 'content': text}
    )

    if username in logs:
        messages += logs[username]

    app.logger.info("userlogs: {}, {}".format(username, logs[username]))
    
    try:
        result = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=1024
        )
    except RateLimitError:
        return jsonify(text="使い過ぎです、少し待ってください。")
    except ServiceUnavailableError as e:
        return jsonify(text="サーバーが過負荷です。少し待って再度試してください。")
    except APIConnectionError as e:
        return jsonify(text="通信中にエラーが発生しました。少し待って再度試してください。")
    except Exception as e:
        return jsonify(text="予期しないエラーが発生しました。担当者に問い合わせてください。")
    else:
        response_text = result['choices'][0]['message']['content']
        # Assistantの応答内容をログに追加
        logs[username].append({'role': 'assistant', 'content': response_text})

    app.logger.info("Answering for,{},{}".format(username, response_text))

    # Encode the response audio to base64
    audio_base64 = base64.b64encode(synthesize_text(response_text)).decode('utf-8')

    return jsonify({
        'text': response_text,
        'audio': audio_base64
    })
    #return response_text


if __name__ == '__main__':
    app.run(port=8080)
    #app.run()