#!/usr/bin/python3


mtgjson_url = 'http://mtgjson.com/json/AllSets-x.json.zip'


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Plom\'s MTG tool')
    parser.add_argument('-c', dest='card_name', action='store',
                        help='specify (original english) name of a card for '
                        'which to view data')
    parser.add_argument('-p', dest='card_set', action='store',
                        help='specify a card set by acronym; in combination '
                        'with -c, selects a specific printing for cards '
                        'available in more than one printing')
    parser.add_argument('-t', dest='card_translation', action='store',
                        help='translated name of a card for which to retrieve'
                        ' english original name')
    return parser, parser.parse_args()


def init_db():

    def get_mtg_dict(db_dir):
        print('Retrieving JSON of all MTG card sets …')
        import urllib.request
        json_file_path = db_dir + 'AllSets-x.json'
        json_zipped_file_path = json_file_path + '.zip'
        urllib.request.urlretrieve(mtgjson_url, json_zipped_file_path)
        print('Unzipping JSON …')
        import zipfile
        zip_ref = zipfile.ZipFile(json_zipped_file_path, 'r')
        zip_ref.extract('AllSets-x.json', db_dir)
        zip_ref.close()
        mtgjson_file = open(json_file_path, 'r')
        import json
        print('Creating sqlite DB …')
        mtgjson_dict = json.load(mtgjson_file)
        mtgjson_file.close()
        os.remove(json_file_path)
        os.remove(json_zipped_file_path)
        return mtgjson_dict

    def create_tables(cursor):
        cursor.execute('CREATE TABLE sets ('
                       'name PRIMARY KEY UNIQUE, '
                       'date TEXT)')
        cursor.execute('CREATE TABLE cards ('
                       'id PRIMARY KEY UNIQUE, '
                       'set_name, '
                       'name, '
                       'layout, '
                       'mana_cost, '
                       'type, '
                       'rarity, '
                       'text, '
                       'flavor, '
                       'power, '
                       'toughness TEXT, '
                       'use_multinames, '
                       'cmc, '
                       'loyalty, '
                       'hand, '
                       'life INTEGER, '
                       'FOREIGN KEY (set_name) REFERENCES sets(name))')
        cursor.execute('CREATE TABLE card_multinames ('
                       'id, '
                       'name TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_sets ('
                       'id, '
                       'set_name TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_colors ('
                       'id, '
                       'color TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_color_identities ('
                       'id, '
                       'color_identity TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_supertypes ('
                       'id, '
                       'supertype TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_types ('
                       'id, '
                       'type TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_subtypes ('
                       'id, '
                       'subtype TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_rulings ('
                       'id, '
                       'date, '
                       'text TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_foreign_names ('
                       'id, '
                       'language, '
                       'name TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')
        cursor.execute('CREATE TABLE card_legalities ('
                       'id, '
                       'format, '
                       'legality TEXT, '
                       'FOREIGN KEY(id) REFERENCES cards(id))')

    def ensure_split_entry(cursor, split_cards, card, set_name):
        import hashlib
        split_name = card['names'][0] + ' // ' + card['names'][1]
        if split_name not in split_cards:
            split_cards += [split_name]
            h = hashlib.sha1()
            # How the hash is constructed according to some reverse engineering
            # and <http://mtgjson.com/documentation.html>
            to_hash = set_name + split_name + card['imageName']
            h.update(to_hash.encode())
            hex_hash = h.hexdigest()
            cursor.execute('INSERT INTO cards '
                           '(id, name, set_name, use_multinames) '
                           'VALUES (?, ?, ?, ?)',
                           (hex_hash, split_name, set_name, 1))
            cursor.execute('INSERT INTO card_multinames (id, name) '
                           'VALUES (?, ?)', (hex_hash, card['names'][0]))
            cursor.execute('INSERT INTO card_multinames (id, name) '
                           'VALUES (?, ?)', (hex_hash, card['names'][1]))

    def add_card_entry(card):

        def insert_into_array_table(table_name, col_name, key):
            if key in card:
                for element in card[key]:
                    cursor.execute('INSERT INTO ' + table_name+' (id, ' +
                                   col_name + ') VALUES (?,?)',
                                   (card['id'], element))

        for key in ('manaCost', 'text', 'flavor', 'power', 'toughness', 'cmc',
                    'loyalty', 'hand', 'life'):
            if key not in card:
                card[key] = None
        cursor.execute('INSERT INTO cards ('
                       'id, set_name, name, layout, mana_cost, type, rarity, '
                       'text, flavor, power, toughness, cmc, loyalty, hand, '
                       'life, use_multinames) '
                       'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (card['id'], set_name, card['name'], card['layout'],
                        card['manaCost'], card['type'], card['rarity'],
                        card['text'], card['flavor'], card['power'],
                        card['toughness'], card['cmc'], card['loyalty'],
                        card['hand'], card['life'], 0))
        insert_into_array_table('card_multinames', 'name', 'names')
        insert_into_array_table('card_sets', 'set_name', 'printings')
        insert_into_array_table('card_colors', 'color', 'colors')
        insert_into_array_table('card_color_identities', 'color_identity',
                                'colors')
        insert_into_array_table('card_supertypes', 'supertype', 'supertypes')
        insert_into_array_table('card_types', 'type', 'types')
        insert_into_array_table('card_subtypes', 'subtype', 'subtypes')
        if 'rulings' in card:
            for ruling in card['rulings']:
                cursor.execute('INSERT INTO card_rulings (id, date, text) '
                               'VALUES (?,?,?)',
                               (card['id'], ruling['date'], ruling['text']))
        if 'foreignNames' in card:
            for foreign_name in card['foreignNames']:
                cursor.execute('INSERT INTO card_foreign_names '
                               '(id, language, name) VALUES (?,?,?)',
                               (card['id'], foreign_name['language'],
                                foreign_name['name']))
        if 'legalities' in card:
            for legality in card['legalities']:
                cursor.execute('INSERT INTO card_legalities '
                               '(id, format, legality) VALUES (?,?,?)',
                               (card['id'], legality['format'],
                                legality['legality']))

    import os
    db_dir = os.getenv('HOME') + '/.mtgtool/'
    import os.path
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    sql_file = db_dir + 'db.sqlite'
    import sqlite3
    if not (os.path.isfile(sql_file)):
        print('No MTG card sets DB found, constructing it in ' + db_dir + ' …')
        mtgjson_dict = get_mtg_dict(db_dir)
        conn = sqlite3.connect(sql_file)
        cursor = conn.cursor()
        create_tables(cursor)
        cards = []
        set_dates = {}
        for set_name in mtgjson_dict:
            set_dates[set_name] = mtgjson_dict[set_name]['releaseDate']
            cursor.execute('INSERT INTO sets (name, date) VALUES (?, ?)',
                           (set_name, mtgjson_dict[set_name]['releaseDate']))
            split_cards = []
            for card in mtgjson_dict[set_name]['cards']:
                if card['layout'] == 'split':
                    ensure_split_entry(cursor, split_cards, card, set_name)
                add_card_entry(card)
        conn.commit()
    else:
        conn = sqlite3.connect(sql_file)
        cursor = conn.cursor()
    return cursor, conn


def get_translated_original_name(cursor, conn, translation):
    results = []
    for row in cursor.execute('SELECT id, language FROM card_foreign_names '
                              'WHERE name = ?', (translation,)):
        results += [(row[0], row[1])]
    if len(results) == 0:
        print('Found no card translated to:', translation)
    else:
        used_name_language_combos = []
        for result in results:
            selected_id = result[0]
            language = result[1]
            cursor.execute('SELECT name FROM cards WHERE id = ?',
                           (selected_id,))
            name = cursor.fetchone()[0]
            name_language_combo = language + ':' + name
            if name_language_combo not in used_name_language_combos:
                print('\'' + translation + '\' is the', language,
                      'name for:', name)
                used_name_language_combos += [name_language_combo]


def get_card(cursor, conn, card_name, card_set):

    def print_card(card_id):

        def print_array_field(table, key, label):
            collection = [row[0] for row in
                          cursor.execute('SELECT ' + key + ' FROM ' + table +
                          ' WHERE id = ?', (card_id,))]
            print(label, ', '.join(collection))

        cursor.execute('SELECT name, layout, mana_cost, cmc, type, power, '
                       'toughness, hand, life, flavor, text, rarity, id '
                       'FROM cards WHERE id=?', (card_id,))
        result = cursor.fetchone()
        print('NAME:', result[0])
        print_array_field('card_multinames', 'name', 'NAMES:')
        print('LAYOUT:', result[1])
        print('MANA COST:', result[2])
        print('CONVERTED MANA COST:', result[3])
        print('TYPE:', result[4])
        print('POWER:', result[5])
        print('TOUGHNESS:', result[6])
        print('MAX HAND SIZE MODIFIER:', result[7])
        print('STARTING LIFE TOTAL MODIFIER:', result[8])
        print('FLAVOR:')
        flavor = []
        if result[9] is not None:
            flavor = result[9].split('\n')
            for line in flavor:
                print(' ', line)
        print('TEXT:')
        text = []
        if result[10] is not None:
            text = result[10].split('\n')
            for line in text:
                print(' ', line)
        print('RARITY:', result[11])
        print_array_field('card_colors', 'color', 'COLOR:')
        print_array_field('card_color_identities', 'color_identity',
                          'COLOR IDENTITY:')
        print_array_field('card_supertypes', 'supertype', 'SUPERTYPES:')
        print_array_field('card_types', 'type', 'TYPES:')
        print_array_field('card_subtypes', 'subtype', 'SUBTYPES:')
        print_array_field('card_sets', 'set_name', 'PRINTINGS:')
        print('RULINGS:')
        for row in cursor.execute('SELECT date, text FROM card_rulings '
                                  'WHERE id = ?', (card_id,)):
            print(' ', row[0] + ':', row[1])
        print('LEGALITIES:')
        for row in cursor.execute('SELECT format, legality '
                                  'FROM card_legalities '
                                  'WHERE id = ?', (card_id,)):
            print(' ', row[0] + ':', row[1])
        print('FOREIGN NAMES:')
        for row in cursor.execute('SELECT language, name '
                                  'FROM card_foreign_names '
                                  'WHERE id = ?', (card_id,)):
            print(' ', row[0] + ':', row[1])

    sorted_sets = [row[0] for row in
                   cursor.execute('SELECT name FROM sets ORDER BY date')]
    results = [{'set': row[0], 'id': row[1], 'use_multinames': row[2]}
               for row in
               cursor.execute('SELECT set_name, id, use_multinames '
               'FROM cards WHERE name=?', (card_name,))]
    if 0 == len(results):
        print('Unknown card:', card_name)
        return
    set_name = results[0]['set']
    sets_of_card = [result['set'] for result in results]
    card_choice = 0
    if card_set is not None:
        if card_set not in sets_of_card:
            print('Set', card_set,
                  'not among sets this card is featured in.')
            return
        set_name = card_set
        card_choice = sets_of_card.index(set_name)
    elif len(results) > 1:
        for set_name_i in sorted_sets:
            if set_name_i in sets_of_card:
                set_name = set_name_i
        card_choice = sets_of_card.index(set_name)
        print('There are multiple printings of this card in different sets. '
              'Showing the printing of set:', set_name)
    selected_id = results[card_choice]['id']
    use_multinames = results[card_choice]['use_multinames']
    if 1 == use_multinames:
        names = [row[0] for row in
                 cursor.execute('SELECT name FROM card_multinames '
                                'WHERE id=?', (selected_id,))]
        print('Card is split:')
        for name in names:
            print('//')
            cursor.execute('SELECT id FROM cards '
                           'WHERE name=? AND set_name=?', (name, set_name))
            result = cursor.fetchone()
            print_card(result[0])
    else:
        print_card(selected_id)


argparser, args = parse_args()
cursor, conn = init_db()
if args.card_translation:
    get_translated_original_name(cursor, conn, args.card_translation)
elif args.card_name:
    get_card(cursor, conn, args.card_name, args.card_set)
else:
    argparser.print_help()
conn.close()