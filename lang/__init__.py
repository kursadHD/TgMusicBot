import json

def load(lang):
    return json.load(open(f'./lang/{lang}.json', 'r'))