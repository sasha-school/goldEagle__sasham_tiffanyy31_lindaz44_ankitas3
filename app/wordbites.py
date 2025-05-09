from flask import *


app = Flask(__name__)

@app.route("/")
def main():
    l = ['A', 'B', 'C']
    imgs = ['https://i.pinimg.com/474x/27/90/cd/2790cd967304e6cdc4267ae9a0d67b2b.jpg', 'https://pngimg.com/d/letter_b_PNG49.png', 'https://cdn3.iconfinder.com/data/icons/letters-and-numbers-1/32/letter_C_blue-512.png']
    letters = list(zip(l, imgs))
    return render_template("wordbites.html", letters = letters)

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
