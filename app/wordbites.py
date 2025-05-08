from flask import *


app = Flask(__name__)

@app.route("/")
def main():
    return render_template("wordbites.html")

@app.route("/box_dropped", methods=["POST"]) #happens in the background and ensures that it doesnt need to refresh
def box_dropped():
    data = request.get_json()
    box_number = data.get("box_number")
    letter = data.get("letter")
    print(f"Letter '{letter}' dropped in box number: {box_number}")
    return jsonify({"status": "received", "box_number": box_number, "letter": letter})

if __name__ == "__main__":
    app.run(debug=True)
