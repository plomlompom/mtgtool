mtgtool
=======

This is a primitive "Magic: The Gathering" card data viewer for the console. It
uses the card data from <http://mtgjson.com>.

usage
-----

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

Deck files of the format "each line an integer followed by a space followed by
a card name" can be opened for browsing in an ncurses interface with the `-b`
option.

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

Fix slowness of ncurses card browser.
