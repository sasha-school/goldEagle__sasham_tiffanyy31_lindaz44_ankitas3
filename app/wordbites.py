from flask import *


app = Flask(__name__)

@app.route("/")
def main():
    return render_template("wordbites.html")

@app.route("/box_dropped", methods=["POST"]) #happens in the background and ensures that it doesnt need to refresh
def box_dropped():
    data = request.get_json()
    letter = data.get("letter")
    from_box = data.get("from_box")
    to_box = data.get("to_box")

    print(f"Letter '{letter}' moved from box {from_box} to box {to_box}")
    return jsonify({"status": "received"})

if __name__ == "__main__":
    app.run(debug=True)
