from flask import *
import random
import csv

wordbites_letter_positions = {}
wordbites_words = []
wordbites_board = []
app = Flask(__name__)

all_words = []
with open('letters7.txt', 'r') as text:
    for word in text:
        all_words += [word[:-1]]

@app.route("/")
def main():
    global wordbites_letter_positions
    global wordbites_words
    global wordbites_board
    wordbites_letter_positions = {} #reset letter positions (for every game)
    wordbites_words = [] #reset words (for every game)
    wordbites_board = [['' for _ in range(8)] for _ in range(9)] #reset board (for every game)
    all_letters = []
    with open('letters_w.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            all_letters.extend(row)
    all_letters = [l for l in all_letters if l]

    letters = []
    i=0
    while i<10:
        temp = random.choice(all_letters)
        if temp not in letters:
            letters += [temp]
            i+=1

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

    wordbites_letter_positions[letter] = to_box
    #print(wordbites_letter_positions)

#future: check for words
    wordbites_board = [['' for _ in range(8)] for _ in range(9)]
    for letter, pos in wordbites_letter_positions.items():
        row, col = (pos-1) // 8, (pos-1) % 9
        wordbites_board[row][col] = letter
    for row in wordbites_board:
        i = 0
        while i < len(row):
            if line[i] != '':
                start = i
                while i < len(row) and row[i] != '':
                    i += 1
                end = i
                if (start == 0 or row[start - 1] == '') and (end == len(row) or row[end] == ''):
                    if end - start >= 3:
                        word = ''.join(row[start:end])
                        if word in all_words: #WORDS
                            wordbites_words += [word]
            else:
                i += 1
    #do cols too
    print(wordbites_words)


    return jsonify({"status": "received"})

if __name__ == "__main__":
    app.run(debug=True)
