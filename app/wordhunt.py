import random
import requests
import urllib.request
import json

def board():
    test = ["AAEEGN", "ABBJOO", "ACHOPS", "AFFKPS",
    "AOOTTW", "CIMOTU", "DEILRX", "DELRVY",
    "DISTTY", "EEGHNW", "EEINSU", "EHRTVW",
    "EIOSST", "ELRTTY", "HIMNQU", "HLNNRZ"]

    new = []
    for i in test:
        new.append(i[random.randint(0,5)])

    return ''.join(new)

def api_solve(board_config):
    """
    data = urllib.request.urlopen(f'https://api.whsolver.ajayganesh.com/solve?board={board_config}')
    pata = data.read()
    bata = data.decode('utf-8')
    results = json.loads(bata)
    """
    data = requests.get(f'https://api.whsolver.ajayganesh.com/solve?board={board_config}')
    results = data.json()
    return results

def print_board(board):
    result = ""
    for i in range(0, len(board)):
        if((i)%4 == 0 and i!=0):
            result += "\n"

        result += board[i] + " "
    return result

def print_words(board):
    data = api_solve(board)
    #print (board)
    print (print_board(board))
    print ("\n")
    list_words = []
    list_dict = (data.get('data'))

    for i in list_dict:
        list_words.append(i.get('word'))
    return list_words
