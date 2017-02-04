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
    parser.add_argument('--test-parser',
                        dest='deck_file_name_debug', action='store',
                        help='run deck file through parser for debugging')
    return parser, parser.parse_args()


def get_db_paths():
    import os
    db_dir = os.getenv('HOME') + '/.mtgtool/'
    import os.path
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return db_dir, db_dir + 'db.sqlite'


def init_db(db_dir, sql_file):

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
        import os
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

    import sqlite3
    import os.path
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
                    ' not among sets this card is featured in.']
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


def browse_cards(stdscr, cursor, conn, entry_list, has_sideboard):

    class Pane:

        def __init__(self):
            self._start_x = 0
            self.scroll_offset = 0

        def draw(self):
            self._pad.clear()
            self._draw_content()
            if self.scroll_offset != 0:
                self._pad.addstr(self.scroll_offset, 0,
                                 '^'*self._win_width, curses.A_REVERSE)
            if self._pad_height - self._win_height > self.scroll_offset:
                self._pad.addstr(self.scroll_offset + self._win_height - 1, 0,
                                 self._win_width*'v', curses.A_REVERSE)
            self._pad.noutrefresh(self.scroll_offset, 0,
                                  0, self._start_x,
                                  self._win_height - 1,
                                  self._start_x + self._win_width - 1)

    class CardList(Pane):

        def __init__(self, entry_list, win_width, win_height, has_sideboard):
            super().__init__()
            self._has_sideboard = has_sideboard
            self._entry_list = entry_list
            self._win_width = win_width
            self._pad_height = len(self._entry_list)
            self._count_width = max([len(str(entry.count))
                                    for entry in self._entry_list])
            self._line_focus = 0
            self.set_geometry(win_height)
            self._pad = curses.newpad(self._pad_height, self._win_width)

        def set_geometry(self, win_height):
            self._win_height = win_height - 1
            self._scroll_start = self._win_height // 2
            self._scroll_end = max(0,
                                   self._pad_height - (self._win_height //
                                                       2) - 1)
            self.selected_card = self._entry_list[self._line_focus].name
            self._scroll()

        def _scroll(self):
            if self._win_height >= self._pad_height or \
                    self._line_focus < self._scroll_start:
                self.scroll_offset = 0
            elif self._line_focus > self._scroll_end:
                self.scroll_offset = self._pad_height - self._win_height
            else:
                self.scroll_offset = self._line_focus - (self._win_height // 2)

        def move_up(self):
            if self._line_focus > 0:
                self._line_focus -= 1
                self.selected_card = self._entry_list[self._line_focus].name
                self._scroll()

        def move_down(self):
            if self._line_focus < self._pad_height - 1:
                self._line_focus += 1
                self.selected_card = self._entry_list[self._line_focus].name
                self._scroll()

        def _draw_content(self, *args):
            for i in range(self._pad_height):
                if i == self._line_focus:
                    attr = curses.A_REVERSE
                else:
                    attr = curses.A_NORMAL
                card_name = self._entry_list[i].name
                count_str = str(self._entry_list[i].count)
                count_pad = self._count_width - len(count_str)
                sideboard_prefix = ''
                if self._has_sideboard:
                    sideboard_prefix = '    '
                    if self._entry_list[i].is_sideboard:
                        sideboard_prefix = 'SB: '
                line = sideboard_prefix + ' ' * count_pad + count_str + ' ' + \
                    card_name
                if len(line) > self._win_width:
                    line = line[0:self._win_width - 1] + '…'
                self._pad.addstr(i, 0, line, attr)

    class CardDescription(Pane):

        def __init__(self, start_x, win_width, win_height, card_names):
            super().__init__()
            self._start_x = start_x
            self._pad_height = 1
            self.set_geometry(win_height, win_width)
            self._descriptions = {}
            self._pad = curses.newpad(self._pad_height, self._win_width)
            self._card_names = card_names
            import threading

            class CardCollector(threading.Thread):

                def __init__(self, card_names, card_descriptions):
                    self._names = card_names
                    self._descs = card_descriptions
                    self._stopper = threading.Event()
                    super().__init__(group=None)

                def run(self):
                    import sqlite3
                    conn = sqlite3.connect(sql_file)
                    cursor = conn.cursor()
                    for name in self._names:
                        if self._stopper.isSet():
                            break
                        if name not in self._descs:
                            self._descs[name] = get_card(cursor, conn, name)
                    conn.close()

                def kill(self):
                    self._stopper.set()

            self._card_collector = CardCollector(self._card_names,
                                                 self._descriptions)
            self._card_collector.start()

        def set_geometry(self, win_height, win_width):
            self._win_height = win_height - 1
            self._win_width = win_width - self._start_x
            if hasattr(self, '_card_name'):
                self._draw_content()
            if self.scroll_offset != 0:
                if self._win_height >= self._pad_height:
                    self.scroll_offset = 0
                elif self.scroll_offset > self._pad_height - self._win_height:
                    self.scroll_offset = self._pad_height - self._win_height

        def set_card(self, card_name):
            self._card_name = card_name

        def scroll_up(self):
            if self.scroll_offset > 0:
                self.scroll_offset -= 1

        def scroll_down(self):
            if self.scroll_offset < self._pad_height - self._win_height:
                self.scroll_offset += 1

        def stop_card_collector(self):
            self._card_collector.kill()

        def _draw_content(self):
            if self._card_name not in self._descriptions:
                self._descriptions[self._card_name] = get_card(cursor, conn,
                                                               self._card_name)
            card_desc_lines = self._descriptions[self._card_name]
            height = 0
            fixed_lines = []
            import unicodedata
            for i in range(len(card_desc_lines)):
                line = card_desc_lines[i]
                padding = 0
                len_line = 0
                for c in line:
                    if 'W' == unicodedata.east_asian_width(c):
                        len_line += 2
                    else:
                        len_line += 1
                padding = self._win_width - (len_line % self._win_width)
                line += ' ' * padding
                height += int((len_line + padding) / self._win_width)
                fixed_lines += [line]
            content = ''.join(fixed_lines)
            self._pad_height = max(self._win_height, height)
            self._pad.resize(self._pad_height + 1, self._win_width)
            self._pad.addstr(0, 0, content)

    class Window:

        def __init__(self, x_separator, entry_list, has_sideboard):
            curses.curs_set(False)
            self._set_geometry()
            self._x_separator = x_separator
            entry_list.sort(key=lambda card: card.name)
            entry_list.sort(key=lambda card: card.is_sideboard)
            self._card_list = CardList(entry_list, self._x_separator,
                                       self._height, has_sideboard)
            card_names = [entry.name for entry in entry_list]
            self._card_desc = CardDescription(self._x_separator + 1,
                                              self._width, self._height,
                                              card_names)
            self._draw_frames()

        def _set_geometry(self):
            stdscr.clear()
            stdscr.refresh()  # due to <http://stackoverflow.com/a/26305933>
            self._height = curses.LINES
            self._width = curses.COLS

        def reset(self):
            import shutil
            size = shutil.get_terminal_size()
            curses.resizeterm(size.lines, size.columns)
            self._set_geometry()
            self._card_list.set_geometry(self._height)
            self._card_desc.set_geometry(self._height, self._width)
            self._draw_frames()
            self.draw_frame_insides()

        def _draw_frames(self):

            def draw_bottom_help(startcol, endcol, text):
                # Workaround for <http://stackoverflow.com/questions/7063128/>.
                if endcol == self._width - 1:
                    endcol -= 1
                    stdscr.addch(self._height - 1, self._width - 2, ' ',
                                 curses.A_REVERSE)
                    stdscr.insstr(self._height - 1, self._width - 2, ' ')
                width = endcol - startcol + 1
                if len(text) < width:
                    text += ' '*(width - len(text))
                stdscr.addstr(self._height - 1, startcol,
                              text, curses.A_REVERSE)

            for line in range(self._height):
                stdscr.addch(line, self._x_separator, '|')
            draw_bottom_help(0, self._x_separator - 1,
                             'move up: "w"; move down: "s"')
            draw_bottom_help(self._x_separator + 1, self._width - 1,
                             'scroll up: "k"; scroll down: "j"')

        def draw_frame_insides(self):
            self._card_list.draw()
            self._card_desc.set_card(self._card_list.selected_card)
            self._card_desc.draw()
            curses.doupdate()

        def move_card_index_up(self):
            self._card_list.move_up()
            self._card_desc.scroll_offset = 0

        def move_card_index_down(self):
            self._card_list.move_down()
            self._card_desc.scroll_offset = 0

        def scroll_desc_up(self):
            self._card_desc.scroll_up()

        def scroll_desc_down(self):
            self._card_desc.scroll_down()

        def quit(self):
            self._card_desc.stop_card_collector()

    card_list_width = 30
    window = Window(card_list_width, entry_list, has_sideboard)
    key = ''
    while key != 'q':
        window.draw_frame_insides()
        ch = stdscr.getch()
        if curses.KEY_RESIZE == ch:
            window.reset()
            # For some reason, terminal resizing fills the getch() input queue
            # with an endless amount of KEY_RESIZE, so flushinp to the rescue.
            curses.flushinp()
        else:
            key = chr(ch)
            if 'w' == key:
                window.move_card_index_up()
            elif 's' == key:
                window.move_card_index_down()
            elif 'k' == key:
                window.scroll_desc_up()
            elif 'j' == key:
                window.scroll_desc_down()
    window.quit()


class DeckEntry():

    def __init__(self, card_name, card_count, is_sideboard):
        self.name = card_name
        self.count = card_count
        self.is_sideboard = is_sideboard


def parse_deck_file(path):
    import re
    f = open(path, 'r')
    deck_lines = f.readlines()
    regex_correctness = r'^\s*(|//|(SB:)?\s*\d+\s*\S)'
    regex_capture = r'^\s*(//.*|(SB:)?\s*(\d+)\s*(\S.*?)\s*)?$'
    for i in range(len(deck_lines)):
        if re.match(regex_correctness, deck_lines[i]) is None:
            print('Deck file malformed on line ' + str(i + 1))
            return None, None
    entry_list = []
    has_sideboard = False
    for line in deck_lines:
        matches = re.match(regex_capture, line).group(2, 3, 4)
        if matches[1] is None:
            continue
        is_sideboard = matches[0] is not None
        has_sideboard = True if is_sideboard else has_sideboard
        count = int(matches[1])
        name = matches[2]
        is_new = True
        for i in range(len(entry_list)):
            entry = entry_list[i]
            if entry.name == name and entry.is_sideboard == is_sideboard:
                entry_list[i].count += count
                is_new = False
        if is_new:
            entry_list += [DeckEntry(name, count, is_sideboard)]
    return entry_list, has_sideboard


db_dir, sql_file = get_db_paths()
argparser, args = parse_args()
cursor, conn = init_db(db_dir, sql_file)
import os.path
if args.deck_file_name_debug:
    if not os.path.isfile(args.deck_file_name_debug):
        print('No deck file:', args.deck_file_name_debug)
    else:
        entry_list, _ = parse_deck_file(args.deck_file_name_debug)
    for entry in entry_list:
        print(entry.is_sideboard, entry.count, entry.name)
elif args.deck_file_name:
    if not os.path.isfile(args.deck_file_name):
        print('No deck file:', args.deck_file_name)
    else:
        entry_list, has_sideboard = parse_deck_file(args.deck_file_name)
        if entry_list:
            import curses
            import sys
            sys.stderr = open('error_log', 'w')
            curses.wrapper(browse_cards, cursor, conn, entry_list,
                           has_sideboard)
elif args.card_translation:
    get_translated_original_name(cursor, conn, args.card_translation)
elif args.card_name:
    [print(line) for line
     in get_card(cursor, conn, args.card_name, args.card_set)]
else:
    argparser.print_help()
conn.close()
exit()
