mtgtool
=======

This is a primitive "Magic: The Gathering" card data viewer for the console. It
uses the card data from <http://mtgjson.com>.

basic usage
-----------

On the first run, `mtgtool.py` pulls the card data from <http://mtgjson.com/>,
and builds below `~/.mtgtool/` an sqlite DB from it.

This DB can be queried for card data by passing the precise original English
card name with the `-c` option:

    $ ./mtgtool.py -c 'Black Lotus'
    There are multiple printings of this card in different sets. Showing the printing of newest set: VMA
    NAME: Black Lotus
    NAMES: 
    LAYOUT: normal
    MANA COST: {0}
    CONVERTED MANA COST: 0
    CURRENT TYPE: Artifact
    PRINTED TYPE: Artifact
    POWER: None
    TOUGHNESS: None
    MAX HAND SIZE MODIFIER: None
    STARTING LIFE TOTAL MODIFIER: None
    FLAVOR:
    ORACLE TEXT:
      {T}, Sacrifice Black Lotus: Add three mana of any one color to your mana pool.
    PRINTED TEXT:
      {T}, Sacrifice Black Lotus: Add three mana of any one color to your mana pool.
    RARITY: Special
    COLOR: 
    COLOR IDENTITY: 
    SUPERTYPES: 
    TYPES: Artifact
    SUBTYPES: 
    PRINTINGS: LEA, LEB, 2ED, CED, CEI, VMA
    RULINGS:
    LEGALITIES:
      Commander: Banned
      Legacy: Banned
      Vintage: Restricted
    FOREIGN NAMES:

If a card is available in more than one set, then the printing from the newest
set is selected by default (see example above). A specific set can be selected
by its acronym via the `-p` option (in the example, note the differences in the
rarity and the printed types and texts):

    $ ./mtgtool.py -c 'Black Lotus' -p LEA
    NAME: Black Lotus
    NAMES: 
    LAYOUT: normal
    MANA COST: {0}
    CONVERTED MANA COST: 0
    CURRENT TYPE: Artifact
    PRINTED TYPE: Mono Artifact
    POWER: None
    TOUGHNESS: None
    MAX HAND SIZE MODIFIER: None
    STARTING LIFE TOTAL MODIFIER: None
    FLAVOR:
    ORACLE TEXT:
      {T}, Sacrifice Black Lotus: Add three mana of any one color to your mana pool.
    PRINTED TEXT:
      Adds 3 mana of any single color of your choice to your mana pool, then is discarded. Tapping this artifact can be played as an interrupt.
    RARITY: Rare
    COLOR: 
    COLOR IDENTITY: 
    SUPERTYPES: 
    TYPES: Artifact
    SUBTYPES: 
    PRINTINGS: LEA, LEB, 2ED, CED, CEI, VMA
    RULINGS:
    LEGALITIES:
      Commander: Banned
      Legacy: Banned
      Vintage: Restricted
    FOREIGN NAMES:

To identify the original name for translated cards, a translated name can be
passed to the `-t` option:

    $ ./mtgtool.py -t Seelenfeuer
    'Seelenfeuer' is the German name for: Soul Burn
    'Seelenfeuer' is the German name for: Soul's Fire

deck browser
------------

Text files that contain deck descriptions in a specific format can be opened for
browsing in an ncurses interface with the `-d` option.

The deck file parser ignores lines that contain only whitespace, or where the
first non-whitespace characters are '//'. On non-ignored lines, whitespace
sequences on the start and the end of the line are ignored. The first
non-whitespace token per line must be either 'SB:' (which marks the entry as
cards belonging to a sideboard), or an integer; if the first token is 'SB:', it
must be followed by any (or no) amount of whitespace, and an integer as the
second token. The integer describes the amount of cards described by the line.
After the integer, a positive number of whitespace characters must follow, and
after those a positive number of characters (the first of which must be
non-whitespace) that ought to match an English MTG card name.

In short, each line must match this regex: `^\s*(//.*|(SB:)?\s*\d+\s+\S.*)?$`

As an example, the following is valid to the parser:

    4 Act of Treason
    1 Advice from the Fae
    //in the browser, the upper and lower line will be combined to "3 Advice from the Fae"
    2 Advice from the Fae
      // another comment followed by an empty line
    
    3    Altar's Reap
      2 Ancient Crab
    // the following line is not empty, but only contains whitespace
                              
    SB:2 Ancient Crab
      SB:    1 Assassinate
      SB:1  Assassinate
    // the following line contains lots of trailing whitespace
    999 Cinder Glade      

In the browser, cards are sorted alphabetically, and multiple lines counting
the same card are combined into single lines with the card sums added together,
except where they differ in their belonging to the sideboard or not.

testing
-------

Just run `./test.sh`.

updating
--------

When a new set is released, the card data retrieved from <http://mtgjson.com/>
should be updated. To do so, just trigger a rebuild of the database by deleting
`~/.mtgtool/db.sqlite`.

bugs
----

As of 2017-01-16, the data from <http://mtgjson.com/> is somewhat incomplete in
regards to translated names. Some examples: German "Zwang" should not only be
"Duress", but also "Coercion"; German "Sturmgeist" should be "Storm Spirit";
German "Dominieren" should not only be "Domineer", but also "Dominate".

todo
----

Make DB updating a command line option.

Make card name search more tolerant (case-insensitive?).

Broaden support for deck file formats.

Extend tests.
