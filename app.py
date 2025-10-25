from deep_translator import GoogleTranslator
from flask import Flask, request, render_template

app = Flask(__name__)

def englishToSpanish(text):
    return GoogleTranslator(source="en", target="es").translate(text)

def spanishToEnglish(text):
    return GoogleTranslator(source="es", target="en").translate(text)

@app.route("/", methods=["GET", "POST"])
def index():
    translated_text = None
    if request.method == "POST":
        user_text = request.form["sentence"]
        selected_lang = request.form["languages"]

        if selected_lang == "en_to_es":
            translated_text = englishToSpanish(user_text)
        elif selected_lang == "es_to_en":
            translated_text = spanishToEnglish(user_text)

    return render_template("index.html", translated_text=translated_text)

if __name__ == "__main__":
    app.run(debug=True)
