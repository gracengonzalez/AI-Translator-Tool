from deep_translator import GoogleTranslator
from flask import Flask, request, render_template

app = Flask(__name__)



@app.route("/", methods=["GET", "POST"])
def index():
    translated_text = None
    if request.method == "POST":
        user_text = request.form["sentence"]
        translated_text = GoogleTranslator(source="es", target="en").translate(user_text)  
    return render_template("index.html", translated_text=translated_text)

if __name__ == "__main__":
    app.run(debug=True)
