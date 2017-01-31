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
    parser.add_argument('-d', dest='deck_file_name', action='store',
                        help='card deck file to browse in curses interface')
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
                       'oracle_type, '
                       'original_type, '
                       'rarity, '
                       'oracle_text, '
                       'original_text, '
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
                    'loyalty', 'hand', 'life', 'originalType', 'originalText'):
            if key not in card:
                card[key] = None
        cursor.execute('INSERT INTO cards ('
                       'id, set_name, name, layout, mana_cost, oracle_type, '
                       'original_type, rarity, oracle_text, original_text, '
                       'flavor, power, toughness, cmc, loyalty, hand, life, '
                       'use_multinames) '
                       'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (card['id'], set_name, card['name'], card['layout'],
                        card['manaCost'], card['type'], card['originalType'],
                        card['rarity'], card['text'], card['originalText'],
                        card['flavor'], card['power'], card['toughness'],
                        card['cmc'], card['loyalty'], card['hand'],
                        card['life'], 0))
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
    results = [(row[0], row[1]) for row in cursor.execute(
               'SELECT id, language FROM card_foreign_names WHERE name = ?',
               (translation,))]
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


def get_card(cursor, conn, card_name, card_set=None):

    def print_card(card_id):

        def print_array_field(table, key, label):
            nonlocal output
            collection = [row[0] for row in
                          cursor.execute('SELECT ' + key + ' FROM ' + table +
                          ' WHERE id = ?', (card_id,))]
            output += [label + ' ' + ', '.join(collection)]

        def print_multiline_text(text, label):
            nonlocal output
            output += [label]
            if text is not None:
                for line in text.split('\n'):
                    output += ['  ' + line]

        nonlocal output
        cursor.execute('SELECT name, layout, mana_cost, cmc, oracle_type, '
                       'original_type, power, toughness, hand, life, flavor, '
                       'oracle_text, original_text, rarity, id '
                       'FROM cards WHERE id=?', (card_id,))
        result = cursor.fetchone()
        output += ['NAME: ' + result[0]]
        print_array_field('card_multinames', 'name', 'NAMES:')
        output += ['LAYOUT: ' + result[1]]
        output += ['MANA COST: ' + str(result[2])]
        output += ['CONVERTED MANA COST: ' + str(result[3])]
        output += ['CURRENT TYPE: ' + result[4]]
        output += ['PRINTED TYPE: ' + result[5]]
        output += ['POWER: ' + str(result[6])]
        output += ['TOUGHNESS: ' + str(result[7])]
        output += ['MAX HAND SIZE MODIFIER: ' + str(result[8])]
        output += ['STARTING LIFE TOTAL MODIFIER: ' + str(result[9])]
        print_multiline_text(result[10], 'FLAVOR:')
        print_multiline_text(result[11], 'ORACLE TEXT:')
        print_multiline_text(result[12], 'PRINTED TEXT:')
        output += ['RARITY: ' + result[13]]
        print_array_field('card_colors', 'color', 'COLOR:')
        print_array_field('card_color_identities', 'color_identity',
                          'COLOR IDENTITY:')
        print_array_field('card_supertypes', 'supertype', 'SUPERTYPES:')
        print_array_field('card_types', 'type', 'TYPES:')
        print_array_field('card_subtypes', 'subtype', 'SUBTYPES:')
        print_array_field('card_sets', 'set_name', 'PRINTINGS:')
        output += ['RULINGS:']
        for row in cursor.execute('SELECT date, text FROM card_rulings '
                                  'WHERE id = ?', (card_id,)):
            output += ['  ' + row[0] + ': ' + row[1]]
        output += ['LEGALITIES:']
        for row in cursor.execute('SELECT format, legality '
                                  'FROM card_legalities '
                                  'WHERE id = ?', (card_id,)):
            output += ['  ' + row[0] + ': ' + row[1]]
        output += ['FOREIGN NAMES:']
        for row in cursor.execute('SELECT language, name '
                                  'FROM card_foreign_names '
                                  'WHERE id = ?', (card_id,)):
            output += ['  ' + row[0] + ': ' + row[1]]

    sorted_sets = [row[0] for row in
                   cursor.execute('SELECT name FROM sets ORDER BY date')]
    results = [{'set': row[0], 'id': row[1], 'use_multinames': row[2]}
               for row in
               cursor.execute('SELECT set_name, id, use_multinames '
               'FROM cards WHERE name=?', (card_name,))]
    if 0 == len(results):
        return ['Unknown card: ' + card_name]
    set_name = results[0]['set']
    sets_of_card = [result['set'] for result in results]
    card_choice = 0
    output = []
    if card_set is not None:
        if card_set not in sets_of_card:
            return ['Set ' + card_set +
                    'not among sets this card is featured in.']
        set_name = card_set
        card_choice = sets_of_card.index(set_name)
    elif len(results) > 1:
        for set_name_i in sorted_sets:
            if set_name_i in sets_of_card:
                set_name = set_name_i
        card_choice = sets_of_card.index(set_name)
        output += ['There are multiple printings of this card in different '
                   'sets. Showing the printing of newest set: ' + set_name]
    selected_id = results[card_choice]['id']
    use_multinames = results[card_choice]['use_multinames']
    if 1 == use_multinames:
        names = [row[0] for row in
                 cursor.execute('SELECT name FROM card_multinames '
                                'WHERE id=?', (selected_id,))]
        output += ['Card is split:']
        for name in names:
            output += ['//']
            cursor.execute('SELECT id FROM cards '
                           'WHERE name=? AND set_name=?', (name, set_name))
            result = cursor.fetchone()
            print_card(result[0])
    else:
        print_card(selected_id)
    return output


def browse_cards(stdscr, cursor, conn, card_count):

    class Pane:

        def __init__(self, win_height):
            self.start_x = 0
            self.win_height = win_height - 1
            self.scroll_offset = 0

        def draw(self, *args):
            self.pad.clear()
            self.draw_content(args)
            if self.scroll_offset != 0:
                self.pad.addstr(self.scroll_offset, 0,
                                '^'*self.pad_width, curses.A_REVERSE)
            if self.pad_height - self.win_height > self.scroll_offset:
                self.pad.addstr(self.scroll_offset + self.win_height - 1, 0,
                                self.pad_width*'v', curses.A_REVERSE)
            self.pad.noutrefresh(self.scroll_offset, 0,
                                 0, self.start_x + 1,
                                 self.win_height - 1,
                                 self.start_x + self.pad_width - 1)

    class CardList(Pane):

        def __init__(self, card_count, pad_width, win_height):
            super().__init__(win_height)
            self.card_count = card_count
            self.pad_width = pad_width
            self.pad_height = len(self.card_count)
            self.count_width = max([len(str(self.card_count[key]))
                                    for key in self.card_count])
            self.pad = curses.newpad(self.pad_height + 1, self.pad_width)
            self.names = [key for key in self.card_count]
            self.names.sort()
            self.line_focus = 0
            self.selected_card = self.names[self.line_focus]
            self.scroll_start = self.win_height // 2
            self.scroll_end = self.pad_height - (self.win_height // 2)

        def scroll_up(self):
            if self.line_focus > 0:
                self.line_focus -= 1
                self.selected_card = self.names[self.line_focus]
                if self.line_focus >= self.scroll_start and \
                        self.line_focus < self.scroll_end:
                    self.scroll_offset -= 1

        def scroll_down(self):
            if self.line_focus < self.pad_height - 1:
                self.line_focus += 1
                self.selected_card = self.names[self.line_focus]
                if self.line_focus > self.scroll_start and \
                        self.line_focus <= self.scroll_end:
                    self.scroll_offset = self.scroll_offset + 1

        def draw_content(self, *args):
            for i in range(self.pad_height):
                if i == self.line_focus:
                    attr = curses.A_REVERSE
                else:
                    attr = curses.A_NORMAL
                card_name = self.names[i]
                count_str = str(self.card_count[card_name])
                count_pad = self.count_width - len(count_str)
                line = ' ' * count_pad + str(self.card_count[card_name]) + \
                       ' ' + card_name
                if len(line) > self.pad_width:
                    line = line[0:self.pad_width - 1] + '…'
                self.pad.addstr(i, 0, line, attr)

    class CardDescription(Pane):

        def __init__(self, start_x, win_width, win_height):
            super().__init__(win_height)
            self.start_x = start_x
            self.pad_width = win_width - self.start_x
            self.pad_height = 1
            self.pad = curses.newpad(self.pad_height, self.pad_width)
            self.descriptions = {}

        def scroll_up(self):
            if self.scroll_offset > 0:
                self.scroll_offset -= 1

        def scroll_down(self):
            if self.scroll_offset < self.pad_height - self.win_height:
                self.scroll_offset += 1

        def get_content(self, card_name):
            import unicodedata
            card_desc_lines = get_card(cursor, conn, card_name)
            new_height = 0
            for i in range(len(card_desc_lines)):
                line = card_desc_lines[i]
                padding = 0
                len_line = 0
                for c in line:
                    if 'W' == unicodedata.east_asian_width(c):
                        len_line += 2
                    else:
                        len_line += 1
                padding = self.pad_width - (len_line % self.pad_width)
                line += ' ' * padding
                new_height += int((len_line + padding) / self.pad_width)
                card_desc_lines[i] = line
            description = {
                'content': ''.join(card_desc_lines),
                'pad_height': max(self.win_height, new_height)
            }
            self.descriptions[card_name] = description

        def draw_content(self, args):
            card_name = args[0]
            if card_name not in self.descriptions:
                self.get_content(card_name)
            self.pad_height = self.descriptions[card_name]['pad_height']
            content = self.descriptions[card_name]['content']
            self.pad.resize(self.pad_height + 1, self.pad_width)
            self.pad.addstr(0, 0, content)

    class Window:

        def __init__(self):
            curses.curs_set(False)
            stdscr.clear()
            stdscr.refresh()  # due to <http://stackoverflow.com/a/26305933>
            self.height = curses.LINES
            self.width = curses.COLS

        def draw_vertical_line(self, col):
            for line in range(self.height):
                stdscr.addch(line, col, '|')

        def draw_bottom_help(self, startcol, endcol, text):
            # Workaround for <http://stackoverflow.com/questions/7063128/>.
            if endcol == self.width - 1:
                endcol -= 1
                stdscr.addch(self.height - 1, self.width - 2, ' ',
                             curses.A_REVERSE)
                stdscr.insstr(self.height - 1, self.width - 2, ' ')
            width = endcol - startcol + 1
            if len(text) < width:
                text += ' '*(width - len(text))
            stdscr.addstr(self.height - 1, startcol, text, curses.A_REVERSE)

    window = Window()
    card_list_width = 30
    card_list = CardList(card_count, card_list_width, window.height)
    card_desc = CardDescription(card_list_width, window.width, window.height)
    window.draw_vertical_line(card_list_width)
    window.draw_bottom_help(0, card_list_width - 1,
                            'move up: "w"; move down: "s"')
    window.draw_bottom_help(card_list_width + 1, window.width - 1,
                            'move up: "k"; move down: "j"')
    key = ''
    while key != 'q':
        card_list.draw()
        card_desc.draw(card_list.selected_card)
        curses.doupdate()
        key = stdscr.getkey()
        if 'w' == key:
            card_list.scroll_up()
            card_desc.scroll_offset = 0
        elif 's' == key:
            card_list.scroll_down()
            card_desc.scroll_offset = 0
        elif 'k' == key:
            card_desc.scroll_up()
        elif 'j' == key:
            card_desc.scroll_down()


argparser, args = parse_args()
cursor, conn = init_db()
if args.deck_file_name:
    import os.path
    if not os.path.isfile(args.deck_file_name):
        print('No deck file:', args.deck_file_name)
    else:
        f = open(args.deck_file_name, 'r')
        deck_lines = [line.rstrip() for line in f.readlines()]
        card_count = {}
        for line in deck_lines:
            count, name = line.split(maxsplit=1)
            count = int(count)
            if name not in card_count:
                card_count[name] = 0
            card_count[name] += count
        import curses
        curses.wrapper(browse_cards, cursor, conn, card_count)
elif args.card_translation:
    get_translated_original_name(cursor, conn, args.card_translation)
elif args.card_name:
    [print(line) for line
     in get_card(cursor, conn, args.card_name, args.card_set)]
else:
    argparser.print_help()
conn.close()
