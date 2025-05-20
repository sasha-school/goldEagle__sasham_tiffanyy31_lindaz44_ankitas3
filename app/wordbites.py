from flask import *
import random
import csv


app = Flask(__name__)

all_words = []
with open('letters7.txt', 'r') as text:
    for word in text:
        all_words += [word[:-1]]

@app.route("/")
def wordbites_main(wordbites_letter_positions, wordbites_words, wordbites_board, wordbites_score):
    all_letters = []
    with open('letters_w.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            all_letters.extend(row)
    all_letters = [l for l in all_letters if l]

    letters = []
    i=0
    while i<16:
        temp = random.choice(all_letters)
        if temp not in letters:
            letters += [temp]
            i+=1

    for i, letter in enumerate(letters):
        if letter not in wordbites_letter_positions:
            wordbites_letter_positions[letter] = i + 1
    return letters, wordbites_words, wordbites_words, wordbites_letter_positions, wordbites_words, wordbites_board, wordbites_score

@app.route("/wordbites_helper", methods=["POST"]) #happens in the background and ensures that it doesnt need to refresh
def wordbites_helper_aux():

    data = request.get_json()
    print(data)
    letter = data.get("letter")
    from_box = data.get("from_box")
    to_box = data.get("to_box")
    wordbites_letter_positions = data.get("wordbites_letter_positions")
    wordbites_words = data.get("wordbites_words")
    wordbites_board = data.get("wordbites_board")
    wordbites_score = data.get("wordbites_score")

    wordbites_letter_positions[letter] = to_box

    wordbites_board = [['' for _ in range(8)] for _ in range(9)]
    for letter, pos in wordbites_letter_positions.items():
        row, col = (pos-1) // 8, (pos-1) % 8
        wordbites_board[row][col] = letter
    for row in wordbites_board:
        i = 0
        while i < len(row):
            if row[i] != '':
                start = i
                while i < len(row) and row[i] != '':
                    i += 1
                end = i
                if (start == 0 or row[start - 1] == '') and (end == len(row) or row[end] == ''):
                    if end - start >= 3:
                        word = ''.join(row[start:end])
                        if word.lower() in all_words:
                            if word not in wordbites_words.keys():
                                wordbites_score += wordbites_score_calc(len(word))
                                wordbites_words[word] = wordbites_score_calc(len(word))
            else:
                i += 1
    for col in range(8):
        col_mod = [wordbites_board[row][col] for row in range(9)]
        i = 0
        while i < len(col_mod):
            if col_mod[i] != '':
                start = i
                while i < len(col_mod) and col_mod[i] != '':
                    i += 1
                end = i
                if (start == 0 or col_mod[start - 1] == '') and (end == len(col_mod) or col_mod[end] == ''):
                    if end - start >= 3:
                        word = ''.join(col_mod[start:end])
                        if word.lower() in all_words:
                            if word not in wordbites_words.keys():
                                wordbites_score += wordbites_score_calc(len(word))
                                wordbites_words[word] = wordbites_score_calc(len(word))
            else:
                i += 1

    return jsonify({"status": "received", "found_words": wordbites_words, "score": wordbites_score})

def wordbites_score_calc(len):
    key = {3: 100, 4: 400, 5: 800, 6:1400, 7:1800, 8:2200, 9:2600} #from actual game
    if len in key:
        return key[len]
    return 100

if __name__ == "__main__":
    app.run(debug=True)
