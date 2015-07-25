#!/usr/bin/env python3

import urllib.request
import json
import re
from datetime import datetime
import os.path
# from wand.image import Image
# from wand.api import library
# import ctypes

NRDB_URL = "http://netrunnerdb.com/api/cards/"
NRDB_IMG_URL = "http://netrunnerdb.com/"
NRDB_SETS_URL = "http://netrunnerdb.com/api/sets/"
EXISTING_CARDS_PATH = 'app/data/cards.json'

# Register C-type arguments
# library.MagickQuantizeImage.argtypes = [ctypes.c_void_p,
#                                        ctypes.c_size_t,
#                                        ctypes.c_int,
#                                        ctypes.c_size_t,
#                                        ctypes.c_int,
#                                        ctypes.c_int
#                                       ]   
# library.MagickQuantizeImage.restype = None


def main():
    # existing_cards_file = open(EXISTING_CARDS_PATH, encoding='utf-8')
    # existing_cards = json.load(existing_cards_file)
    # existing_cards_file.close()

    nrdb_json = urllib.request.urlopen(NRDB_URL).readall().decode('raw_unicode_escape')
    nrdb_cards = json.loads(nrdb_json)

    # Remove the Chronos Protocol cards
    # existing_cards['cards'] = remove_chronos_protocol(existing_cards['cards'])
    nrdb_cards = remove_problem_cards(nrdb_cards)

    # Remove the following unused attributes from nrdb cards
    attr_to_remove = ['code', 'set_code', 'side_code', 'faction_code', 'cyclenumber', 'limited', 'faction_letter',
                      'type_code', 'subtype_code', 'last-modified', 'url', 'nrdb_art', 'ancurLink']

    for card in nrdb_cards:
        card['nrdb_url'] = card['url']
        card['nrdb_art'] = card['imagesrc']
        card['imagesrc'] = "/images/cards/" + image_name(card['title']) + ".png"

        if 'icebreaker' in card['subtype_code']:
            card = calculate_breaker_info(card)            
        
        save_card_image(card['nrdb_art'], card['imagesrc'])

        if 'subtype' in card and card['subtype'] == "":
            del card['subtype']

        for attr in attr_to_remove:
            del card[attr]
            
    nrdb_sets_json = urllib.request.urlopen(NRDB_SETS_URL).readall().decode('utf-8')  # unicode_escape'?
    nrdb_sets = json.loads(nrdb_sets_json)
    
    # Remove the following unused attributes from the card sets
    sets_attr_to_remove = ['code', 'number', 'known', 'total', 'url', 'available', 'name', 'cyclenumber']
    for card_set in nrdb_sets:
        card_set['released'] = card_set['available'] if card_set['available'] != '' else None
        card_set['title'] = card_set['name']
        
        if card_set['cyclenumber'] == 2:
            card_set['cycle'] = "Genesis"
        elif card_set['cyclenumber'] == 4:
            card_set['cycle'] = "Spin"
        elif card_set['cyclenumber'] == 6:
            card_set['cycle'] = "Lunar"
        elif card_set['cyclenumber'] == 8:
            card_set['cycle'] = "SanSan"
        
        for attr in sets_attr_to_remove:
            del card_set[attr]
            
        if card_set['title'] == "Alternates" or card_set['title'] == 'Special':
            continue

    # Write the json to a file.
    data_set = {"last-modified": datetime.now().isoformat(), "cards": nrdb_cards, "sets": nrdb_sets}
    existing_cards_file2 = open(EXISTING_CARDS_PATH, 'w', encoding='utf-8')
    json_str = json.dumps(data_set, ensure_ascii=False, sort_keys=True, indent=4)
    existing_cards_file2.write(json_str)
    print("Finished!")
    
    
# Attempts to read the breakers text and calculate the amount it costs to break ice.
def calculate_breaker_info(card):
    text_matches = re.match(r".*(\d)\[Credits](\d*).+subroutine\D+(\d*)\[Credits].*\+(\d*).*", card['text'])
    break_credits = 1
    break_subs = 1
    strength_cost = 1
    strength_amount = 1
    
    if text_matches:
        if text_matches.group(1) != '':
            break_credits = int(text_matches.group(1))
            
        if text_matches.group(2) != '':
            break_subs = int(text_matches.group(2))
            
        if text_matches.group(3) != '':
            strength_cost = int(text_matches.group(3))
            
        if text_matches.group(4) != '':
            strength_amount = int(text_matches.group(4))
    else:
        print("Cannot parse breaker cost for - " + card['title'])
        
    if strength_amount == 1:
        card['strengthcost'] = strength_cost
    else:
        card['strengthcost'] = {'credits': strength_cost, 'strength': strength_amount}
    card['breakcost'] = {'credits': break_credits, 'subroutines': break_subs}
    
    return card


def save_card_image(url_to_card, path_to_save):
    if os.path.isfile('app' + path_to_save):
        print('Ignoring Card download for - app' + path_to_save)
    else:
        print("Saving - app" + path_to_save)
        with urllib.request.urlopen(NRDB_IMG_URL + url_to_card) as response, \
                open('app' + path_to_save, 'wb') as out_file:
            data = response.read()
            out_file.write(data)


def remove_problem_cards(cards):
    cards_to_remove = []

    for i in range(len(cards)):
        card = cards[i]
        # Card 00002 is a copy of Laramy Fisk from before his set was known. Duplicates cause errors.
        if ('Chronos Protocol' in card['title'] or
                ('url' in card and 'http://netrunnerdb.com/en/card/00002' in card['url'])):
            cards_to_remove.append(i)

    num_removed = 0
    for i in cards_to_remove:
        print("Removing: " + cards[i - num_removed]['title'])
        del cards[i - num_removed]
        num_removed += 1

    return cards


# Make card titles friendly for file names.
def image_name(title):
    title = title.replace(' ', '-')
    title = title.lower()
    # Replace all characters that aren't alphanumeric or -.
    title = re.sub('[^a-z0-9-]', '', title)

    return title


if __name__ == "__main__":
    main()
