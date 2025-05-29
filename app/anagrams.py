import random
import csv

def getWordSelectionAnagrams():
    vowels = "aeiou"
    vowels = list(vowels)
    cons = "qwrtypsdfghjklzxcvbnm"
    cons = list(cons)
    bigV = []
    bigC = []

    try:
        with open('letters_w.csv', 'r') as file:
            csv_r = csv.reader(file)
            for row in csv_r:
                if row[0].lower() in vowels:
                    bigV.extend(row)
                else: 
                    bigC.extend(row)
                print(row)
   
    except Exception as e:
        print(f"An error occurred: {e}")

    
    vowelSet = random.sample(bigV, 3)
    conSet = random.sample(bigC, 3)

    letterSet = vowelSet + conSet
    random.shuffle(letterSet)
    return letterSet

print(getWordSelectionAnagrams())

#get 3 random vowels
#get 3 random consonants

