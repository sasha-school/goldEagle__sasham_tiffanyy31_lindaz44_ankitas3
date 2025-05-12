import random


def getWordSelectionAnagrams():
    vowels = "aeiou"
    vowels = list(vowels)
    cons = "qwrtypsdfghjklzxcvbnm"
    cons = list(cons)
    
    vowelSet = random.sample(vowels, 3)
    conSet = random.sample(cons, 3)

    letterSet = vowelSet + conSet
    random.shuffle(letterSet)
    return letterSet

print(getWordSelectionAnagrams())

#get 3 random vowels
#get 3 random consonants
