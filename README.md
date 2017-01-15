mtgtool
=======

This is a primitive "Magic: The Gathering" card data viewer that, on first run,
pulls the card data from <http://mtgjson.com/>, builds below ~/.mtgtool/ an
sqlite DB from it, and queries it for a card name when provided with the -c
option.

If a card is available in more than one set, a specific set can be specified by
its acronym via the -p option.

Card names are expected in English. A translated name can be specified with the
-t option, which will return the original card names to which the translation
belongs.

testing
-------

Just run ./test.sh
