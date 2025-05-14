from flask import *

wordbites_letter_positions = {}
app = Flask(__name__)

@app.route("/")
def main():
    global wordbites_letter_positions
    wordbites_letter_positions = {} #reset letter positions (for every game)
    #future: select 5 random letters from all
    letters = ['A', 'B', 'C']

    for i, letter in enumerate(letters):
        if letter not in wordbites_letter_positions:
            wordbites_letter_positions[letter] = i + 1
    print(wordbites_letter_positions)

    return render_template("wordbites.html", letters = letters)

@app.route("/wordbites_helper", methods=["POST"]) #happens in the background and ensures that it doesnt need to refresh
def wordbites_helper():
    data = request.get_json()
    letter = data.get("letter")
    from_box = data.get("from_box")
    to_box = data.get("to_box")

    print(f"Letter '{letter}' moved from box {from_box} to box {to_box}")
    wordbites_letter_positions[letter] = to_box
    print(wordbites_letter_positions)
    #future: check for words
    return jsonify({"status": "received"})

if __name__ == "__main__":
    app.run(debug=True)
