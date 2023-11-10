# ChatGPT Conversation Training Tool
This tool is actively under development to enhance second-language conversation skills. We developed this project with **ChatGPT**. Consequently, it can be loaded into ChatGPT and remade.

## Features
- **Deployment Options:** Run the software either locally or deploy it on the cloud platform *Heroku* for convenient accessibility.

## How to Use

### Installation

**Prerequisites:**
 - Python 3.10.6
 - flask >= 2.3.2
 - flask_cors >= 3.0.10
 - openai >= 0.27.8
 - jsonify >= 0.5
 - google-cloud-texttospeech >= 2.14.1

To run the project locally, follow these steps:

1. Clone the repository to your local machine:
```
bash
cd your-repository
```

2. Ready OpenAI API key:
[OpenAI](https://platform.openai.com/api-keys)

3. Change the code in api_key.py:
```openai_key = "[add your OpenAI key]"```

4. Get the JSON file of Google Cloud API:
[Google Cloud](https://cloud.google.com/iam/docs/keys-create-delete?hl=en)

5. Rename the JSON file to *gtts.json* and put it into repository folder.

### Running Locally
If you want to use it in your local network, please ask the Network Administrator of your office.

1. Install Python3 into your PC:
[Python.org](https://www.python.org/downloads/)

2. Install the required dependencies:
```pip install -r requirements.txt```

3. Now that the Python environment is set up, you can run the project locally:
```python app.py```

4. If you see the following message, please open the URL in your browser:
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:8080
Press CTRL+C to quit
```

### Running in the Heroku
1. Prepare for *Heroku*
[Getting Started with Gradle on Heroku](https://devcenter.heroku.com/articles/getting-started-with-gradle-on-heroku)

2. Copy these files to your Heroku repository and deploy them.

3. Please open the URL in your browser.
https://[your Heroku app name].herokuapp.com/