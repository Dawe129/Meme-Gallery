from flask import Flask, render_template
import json

app = Flask(__name__)

with open("memes.json", encoding = "utf-8") as f:
    memes = json.load(f)

@app.route("/")
def index():
    return render_template("index.html", memes=memes)

if __name__ == "__main__":
    app.run(debug=True)