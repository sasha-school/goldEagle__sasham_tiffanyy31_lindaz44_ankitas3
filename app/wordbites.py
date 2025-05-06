from flask import *


app = Flask(__name__)

@app.route("/")
def main():
    return render_template("wordbites.html")


if __name__ == "__main__":
    app.run(debug=True)
