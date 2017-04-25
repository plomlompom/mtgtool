#!/usr/bin/python3
import os
import os.path
import sqlite3


mtgjson_url = 'http://mtgjson.com/json/AllSets-x.json.zip'

template = """NAME: %name%
NAMES: %names%
LAYOUT: %layout%
MANA COST: %mana_cost%
CONVERTED MANA COST: %converted_mana_cost%
CURRENT TYPE: %current_type%
PRINTED TYPE: %printed_type%
POWER: %power%
TOUGHNESS: %toughness%
MAX HAND SIZE MODIFIER: %max_hand_size_mod%
STARTING LIFE TOTAL MODIFIER: %start_life_total_mod%
FLAVOR:
%flavor|indent%
ORACLE TEXT:
%oracle_text|indent%
PRINTED TEXT:
%printed_text|indent%
RARITY: %rarity%
COLOR: %color%
COLOR IDENTITY: %color_identity%
SUPERTYPES: %supertypes%
TYPES: %types%
SUBTYPES: %subtypes%
PRINTINGS: %sets%
RULINGS:
%rulings|indent%
LEGALITIES:
%legalities|indent%
FOREIGN NAMES:
%foreign_names|indent%"""


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
    parser.add_argument('-f', dest='template', action='store',
                        help='card data formatting template')
    parser.add_argument('-q', dest='quiet', action='store_true',
                        help='suppress non-essential messages')
    parser.add_argument('--test-parser',
                        dest='deck_file_name_debug', action='store',
                        help='run deck file through parser for debugging')
    return parser, parser.parse_args()


def print_verbose(msg):
    global args
    if not args.quiet:
        print(msg)


class DB:

    def __init__(self):
        self.db_dir = os.getenv('HOME') + '/.mtgtool/'
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        self.sql_file = self.db_dir + 'db.sqlite'
        if not (os.path.isfile(self.sql_file)):
            print_verbose('No MTG card sets DB found, constructing it in ' +
                          self.db_dir + ' …')
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.sql_file)
            self.cursor = self.conn.cursor()

    def insert(self, table, d):
        keys = []
        values = []
        for key in d:
            keys += [key]
            values += [d[key]]
        placeholders = ', '.join(len(keys) * ['?'])
        keys = ', '.join(keys)
        code = 'INSERT INTO %s (%s) VALUES (%s)' % (table, keys, placeholders)
        self.cursor.execute(code, values)

    def create_db(self):
        mtgjson_dict = self.get_mtg_dict()
        self.conn = sqlite3.connect(self.sql_file)
        self.cursor = self.conn.cursor()
        self.create_tables()
        cards = []
        set_dates = {}
        for set_name in mtgjson_dict:
            set_dates[set_name] = mtgjson_dict[set_name]['releaseDate']
            self.insert('sets',
                        {'name': set_name,
                         'date': mtgjson_dict[set_name]['releaseDate']})
            split_cards = []
            for card in mtgjson_dict[set_name]['cards']:
                if card['layout'] == 'split':
                    self.ensure_split_entry(split_cards, card, set_name)
                self.add_card_entry(set_name, card)
        self.conn.commit()

    def get_mtg_dict(self):
        import urllib.request
        import zipfile
        import json
        print_verbose('Retrieving JSON of all MTG card sets …')
        json_file_path = self.db_dir + 'AllSets-x.json'
        json_zipped_file_path = json_file_path + '.zip'
        urllib.request.urlretrieve(mtgjson_url, json_zipped_file_path)
        print_verbose('Unzipping JSON …')
        zip_ref = zipfile.ZipFile(json_zipped_file_path, 'r')
        zip_ref.extract('AllSets-x.json', self.db_dir)
        zip_ref.close()
        mtgjson_file = open(json_file_path, 'r')
        print_verbose('Creating sqlite DB …')
        mtgjson_dict = json.load(mtgjson_file)
        mtgjson_file.close()
        os.remove(json_file_path)
        os.remove(json_zipped_file_path)
        return mtgjson_dict

    def create_tables(self):
        self.cursor.execute('CREATE TABLE sets ('
                            'name PRIMARY KEY UNIQUE, '
                            'date TEXT)')
        self.cursor.execute('CREATE TABLE cards ('
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
        self.cursor.execute('CREATE TABLE card_multinames ('
                            'id, '
                            'name TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_sets ('
                            'id, '
                            'set_name TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_colors ('
                            'id, '
                            'color TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_color_identities ('
                            'id, '
                            'color_identity TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_supertypes ('
                            'id, '
                            'supertype TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_types ('
                            'id, '
                            'type TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_subtypes ('
                            'id, '
                            'subtype TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_rulings ('
                            'id, '
                            'date, '
                            'text TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_foreign_names ('
                            'id, '
                            'language, '
                            'name TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')
        self.cursor.execute('CREATE TABLE card_legalities ('
                            'id, '
                            'format, '
                            'legality TEXT, '
                            'FOREIGN KEY(id) REFERENCES cards(id))')

    def ensure_split_entry(self, split_cards, card, set_name):
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
            self.insert('cards', {'id': hex_hash, 'name': split_name,
                                  'set_name': set_name, 'use_multinames': 1})
            self.insert('card_multinames', {'id': hex_hash,
                                            'name': card['names'][0]})
            self.insert('card_multinames', {'id': hex_hash,
                                            'name': card['names'][1]})

    def add_card_entry(self, set_name, card):

        def insert_into_array_table(table, col, key):
            if key in card:
                for element in card[key]:
                    self.insert(table, {'id': card['id'], col: element})

        for key in ('manaCost', 'text', 'flavor', 'power', 'toughness', 'cmc',
                    'loyalty', 'hand', 'life', 'originalType', 'originalText'):
            if key not in card:
                card[key] = None
        self.insert('cards',
                    {'id': card['id'], 'set_name': set_name,
                     'name': card['name'], 'layout': card['layout'],
                     'mana_cost': card['manaCost'],
                     'oracle_type': card['type'],
                     'original_type': card['originalType'],
                     'rarity': card['rarity'], 'oracle_text': card['text'],
                     'original_text': card['originalText'],
                     'flavor': card['flavor'], 'power': card['power'],
                     'toughness': card['toughness'], 'cmc': card['cmc'],
                     'loyalty': card['loyalty'], 'hand': card['hand'],
                     'life': card['life'], 'use_multinames': 0})
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
                self.insert('card_rulings',
                            {'id': card['id'], 'date': ruling['date'],
                             'text': ruling['text']})
        if 'foreignNames' in card:
            for foreign_name in card['foreignNames']:
                self.insert('card_foreign_names',
                            {'id': card['id'],
                             'language': foreign_name['language'],
                             'name': foreign_name['name']})
        if 'legalities' in card:
            for legality in card['legalities']:
                self.insert('card_legalities',
                            {'id': card['id'], 'format': legality['format'],
                             'legality': legality['legality']})


def get_translated_original_name(cursor, translation):
    results = [(row[0], row[1]) for row in db.cursor.execute(
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


def get_card(cursor, card_name, card_set=None):
    global args

    def print_card(card_id):

        def multiline_text(text):
            # TODO: Instead, check None below in the val resolution, as other
            # fields may also be affected.
            if text is not None:
                return text.split('\n')
            return []

        def get_list(table, keys):
            nonlocal card_id
            rows = [row for row in cursor.execute(
                    'SELECT ' + ','.join(keys) + ' FROM card_' + table +
                    ' WHERE id=?', (card_id,))]
            if len(keys) == 1:
                return [row[0] for row in rows]
            else:
                return [row[0] + ': ' + row[1] for row in rows]

        def join_by_sep_rule(sep_rule, collection):
            if sep_filter == 'indent':
                return '\n'.join(['  ' + line for line in collection])
            elif sep_filter == 'comma':
                return ', '.join(collection)

        nonlocal output
        cursor.execute('SELECT name, layout, mana_cost, cmc, oracle_type, '
                       'original_type, power, toughness, hand, life, flavor, '
                       'oracle_text, original_text, rarity, id '
                       'FROM cards WHERE id=?', (card_id,))
        result = cursor.fetchone()
        d = {
            'name': result[0],
            'names': get_list('multinames', ['name']),
            'layout': result[1],
            'mana_cost': str(result[2]),
            'converted_mana_cost': str(result[3]),
            'current_type': result[4],
            'printed_type': result[5],
            'power': str(result[6]),
            'toughness': str(result[7]),
            'max_hand_size_mod': str(result[8]),
            'start_life_total_mod': str(result[9]),
            'flavor': multiline_text(result[10]),
            'oracle_text': multiline_text(result[11]),
            'printed_text': multiline_text(result[12]),
            'rarity': result[13],
            'color': get_list('colors', ['color']),
            'color_identity': get_list('color_identities', ['color_identity']),
            'supertypes': get_list('supertypes', ['supertype']),
            'types': get_list('types', ['type']),
            'subtypes': get_list('subtypes', ['subtype']),
            'sets': get_list('sets', ['set_name']),
            'rulings': get_list('rulings', ['date', 'text']),
            'legalities': get_list('legalities', ['format', 'legality']),
            'foreign_names': get_list('foreign_names', ['language', 'name'])
        }
        global template
        card_desc = template[:]
        i_end = -1
        while True:
            i_start = card_desc.find('%', i_end + 1)
            if i_start == -1:
                break
            i_end = card_desc.find('%', i_start + 1)
            if i_end == -1:
                break
            i_filter = card_desc.find('|', i_start + 1)
            sep_filter = 'comma'
            var_name = ''
            if i_filter > -1 and i_filter < i_end:
                var_name = card_desc[i_start + 1:i_filter]
                sep_filter = card_desc[i_filter + 1:i_end]
            else:
                var_name = card_desc[i_start + 1:i_end]
            if var_name == '':
                val = '%'
            else:
                val = d[var_name]
                if type(val) is list:
                    val = join_by_sep_rule(sep_filter, val)
            card_desc_start = card_desc[:i_start] + val
            card_desc = card_desc_start + card_desc[i_end+1:]
            i_end = len(card_desc_start) - 1
        output += card_desc.split('\n')

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
        if not args.quiet:
            output += ['There are multiple printings of this card in '
                       'different sets. Showing the printing of newest set: ' +
                       set_name]
    selected_id = results[card_choice]['id']
    use_multinames = results[card_choice]['use_multinames']
    if 1 == use_multinames:
        names = [row[0] for row in
                 cursor.execute('SELECT name FROM card_multinames '
                                'WHERE id=?', (selected_id,))]
        if not args.quiet:
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


def browse_cards(stdscr, db, entry_list, has_sideboard):

    class CardCollection:

        def __init__(self, db, entry_list, has_sideboard):
            import threading

            class CardCollector(threading.Thread):

                def __init__(self, db, entry_list, card_descriptions,
                             *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._db = db
                    self._names = [entry.name for entry in entry_list]
                    self._descs = card_descriptions

                def run(self):
                    conn = sqlite3.connect(self._db.sql_file)
                    cursor = conn.cursor()
                    for name in self._names:
                        if name not in self._descs:
                            self._descs[name] = get_card(cursor, name)
                    conn.close()

                def kill(self):
                    self._stopper.set()

            self.db = db
            self.have_sideboard = has_sideboard
            entry_list.sort(key=lambda card: card.name)
            entry_list.sort(key=lambda card: card.is_sideboard)
            self.entry_list = entry_list
            self.descriptions = {}
            self._card_collector = CardCollector(self.db, self.entry_list,
                                                 self.descriptions,
                                                 daemon=True)
            self._card_collector.start()

        def get_card_desc(self, name):
            if name not in self.descriptions:
                self.descriptions[name] = get_card(self.db.cursor, name)
            return self.descriptions[name]

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

    class CardListFrame(Pane):

        def __init__(self, win_width, win_height, entry_list, has_sideboard):
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

    class CardDescFrame(Pane):

        def __init__(self, start_x, win_width, win_height):
            super().__init__()
            self._start_x = start_x
            self._pad_height = 1
            self.set_geometry(win_height, win_width)
            self._pad = curses.newpad(self._pad_height, self._win_width)

        def set_geometry(self, win_height, win_width):
            self._win_height = win_height - 1
            self._win_width = win_width - self._start_x
            if hasattr(self, '_card_desc'):
                self._draw_content()
            if self.scroll_offset != 0:
                if self._win_height >= self._pad_height:
                    self.scroll_offset = 0
                elif self.scroll_offset > self._pad_height - self._win_height:
                    self.scroll_offset = self._pad_height - self._win_height

        def set_desc(self, card_desc):
            self._card_desc = card_desc

        def scroll_up(self):
            if self.scroll_offset > 0:
                self.scroll_offset -= 1

        def scroll_down(self):
            if self.scroll_offset < self._pad_height - self._win_height:
                self.scroll_offset += 1

        def _draw_content(self):
            import unicodedata
            card_desc_lines = self._card_desc[:]
            height = 0
            fixed_lines = []
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

        def __init__(self, x_separator, card_coll):
            self._card_coll = card_coll
            curses.curs_set(False)
            self._set_geometry()
            self._x_separator = x_separator
            self._card_list = CardListFrame(self._x_separator, self._height,
                                            self._card_coll.entry_list,
                                            self._card_coll.have_sideboard)
            self._card_desc = CardDescFrame(self._x_separator + 1,
                                            self._width, self._height)
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
            card_name = self._card_list.selected_card
            card_desc = self._card_coll.get_card_desc(card_name)
            self._card_desc.set_desc(card_desc)
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

    card_list_width = 30
    card_coll = CardCollection(db, entry_list, has_sideboard)
    window = Window(card_list_width, card_coll)
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


class DeckEntry():

    def __init__(self, card_name, card_count, is_sideboard):
        self.name = card_name
        self.count = card_count
        self.is_sideboard = is_sideboard


def parse_deck_file(path):
    import re

    def check_lines_by_regex(deck_lines, regex_correctness):
        for i in range(len(deck_lines)):
            if re.match(regex_correctness, deck_lines[i]) is None:
                return 'Deck file malformed on line ' + str(i + 1)
        return None

    def add_match_to_entry_list(entry_list, matches, is_sideboarded):
        count = int(matches[1])
        name = matches[2]
        is_new = True
        for i in range(len(entry_list)):
            entry = entry_list[i]
            if entry.name == name and entry.is_sideboard == is_sideboarded:
                entry_list[i].count += count
                is_new = False
        if is_new:
            entry_list += [DeckEntry(name, count, is_sideboarded)]

    def try_format_1():
        # Test correctness.
        regex_correctness = r'^\s*(//.*|(SB:)?\s*\d+\s+\S.*)?$'
        err = check_lines_by_regex(deck_lines, regex_correctness)
        if err:
            return None, None, 'Format 1: Error: ' + err
        # Parse.
        regex_capture = r'^\s*(//.*|(SB:)?\s*(\d+)\s+(\S.*?)\s*)?$'
        entry_list = []
        has_sideboard = False
        for line in deck_lines:
            matches = re.match(regex_capture, line).group(2, 3, 4)
            if matches[1] is None:
                continue
            is_sideboard = matches[0] is not None
            has_sideboard = True if is_sideboard else has_sideboard
            add_match_to_entry_list(entry_list, matches, is_sideboard)
        return entry_list, has_sideboard, ''

    def try_format_2():
        # Test correctness.
        err_prefix = 'Format 2: Error: '
        regex_correctness = r'^\s*(//.*|Sideboard\s*|\d+\s+\S.*)?$'
        err = check_lines_by_regex(deck_lines, regex_correctness)
        if err:
            return None, None, err_prefix + err
        regex_capture = r'^\s*(//.*|(Sideboard\s*)|(\d+)\s+(\S.*?)\s*)?$'
        has_sideboard = False
        sideboard_empty = True
        for line in deck_lines:
            matches = re.match(regex_capture, line).group(2, 3, 4)
            if matches[0] is not None:
                if has_sideboard:
                    return None, None, err_prefix +\
                           'More than one "Sideboard" line in deck file.'
                has_sideboard = True
            elif has_sideboard and matches[1] is not None:
                sideboard_empty = False
        if has_sideboard and sideboard_empty:
            return None, None, err_prefix + 'Sideboard defined, but empty.'
        # Parse.
        entry_list = []
        in_sideboard = False
        for line in deck_lines:
            matches = re.match(regex_capture, line).group(2, 3, 4)
            if matches[0]:
                in_sideboard = True
                continue
            if matches[1] is None:
                continue
            add_match_to_entry_list(entry_list, matches, in_sideboard)
        return entry_list, in_sideboard, ''

    if not os.path.isfile(path):
        print('No deck file:', path)
        return None, None
    f = open(path, 'r')
    deck_lines = f.readlines()
    entry_list, has_sideboard, err_format_1 = try_format_1()
    if entry_list is None:
        entry_list, has_sideboard, err_format_2 = try_format_2()
    if entry_list is None:
        print(err_format_1)
        print(err_format_2)
        return None, None
    if 0 == len(entry_list):
        print('Deck empty.')
        return None, None
    return entry_list, has_sideboard


def template_is_good(templ):

    def error(msg):
        nonlocal i_marker
        print('Template error in ' + str(i_marker) + '-th %%: ' + msg)
        print('Aborting due to bad card data formatting template.')
        exit()

    legal_names = {
        'name': 0,
        'names': 1,
        'layout': 0,
        'mana_cost': 0,
        'converted_mana_cost': 0,
        'current_type': 0,
        'printed_type': 0,
        'power': 0,
        'toughness': 0,
        'max_hand_size_mod': 0,
        'start_life_total_mod': 0,
        'flavor': 1,
        'oracle_text': 1,
        'printed_text': 1,
        'rarity': 0,
        'color': 1,
        'color_identity': 1,
        'supertypes': 1,
        'types': 1,
        'subtypes': 1,
        'sets': 1,
        'rulings': 1,
        'legalities': 1,
        'foreign_names': 1,
    }
    legal_filters = ['indent', 'comma']
    i_end = -1
    i_marker = 0
    while True:
        i_start = templ.find('%', i_end + 1)
        if i_start == -1:
            return True
        i_marker += 1
        i_end = templ.find('%', i_start + 1)
        if i_end == -1:
            error('Closing % missing.')
        i_filter = templ.find('|', i_start + 1)
        sep_filter = ''
        var_name = ''
        if i_filter > -1 and i_filter < i_end:
            var_name = templ[i_start + 1:i_filter]
            sep_filter = templ[i_filter + 1:i_end]
            if sep_filter not in legal_filters:
                error('Illegal filter name: ' + sep_filter)
        else:
            var_name = templ[i_start + 1:i_end]
        if var_name != '' and var_name not in legal_names:
            error('Illegal var name: ' + var_name)
        if sep_filter != '' and legal_names[var_name] != 1:
            error('Filter ' + sep_filter + ' illegal for ' + var_name + '.')


# Parse input.
argparser, args = parse_args()
if args.template:
    template = args.template
template_is_good(template)

# Execute user command.
if args.deck_file_name_debug:
    entry_list, _ = parse_deck_file(args.deck_file_name_debug)
    if entry_list:
        for entry in entry_list:
            print(entry.is_sideboard, entry.count, entry.name)
else:
    db = DB()
    if args.deck_file_name:
        entry_list, has_sideboard = parse_deck_file(args.deck_file_name)
        if entry_list:
            import curses
            import sys
            sys.stderr = open('error_log', 'w')
            curses.wrapper(browse_cards, db, entry_list, has_sideboard)
    elif args.card_translation:
        get_translated_original_name(db.cursor, args.card_translation)
    elif args.card_name:
        [print(line) for line
         in get_card(db.cursor, args.card_name, args.card_set)]
    else:
        argparser.print_help()
    db.conn.close()
