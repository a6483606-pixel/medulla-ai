Medulla AI — Web talking bot

1. Put these files inside a folder named MedullaAI:
   - app.py
   - requirements.txt
   - templates/index.html
   - static/style.css

2. Install Python 3.10+ and then from the project folder run:
   pip install -r requirements.txt

3. Set your OpenAI API key once (Windows PowerShell):
   setx OPENAI_API_KEY "sk-your_api_key_here"
   Then close and re-open your terminal.

   On Mac/Linux (temporary):
   export OPENAI_API_KEY="sk-your_api_key_here"

4. Run the app:
   python app.py

5. Open your browser and go to:
   http://127.0.0.1:5000

Type a message and press Enter or click Send.
Medulla's reply will appear and be read aloud using your browser's built-in speech synthesis.
