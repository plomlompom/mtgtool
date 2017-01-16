mtgtool
=======

This is a primitive "Magic: The Gathering" card data viewer for the console
that, on first run, pulls the card data from <http://mtgjson.com/>, builds
below ~/.mtgtool/ an sqlite DB from it, and queries it for a card name when
provided with the -c option.

If a card is available in more than one set, a specific set can be selected by
its acronym via the -p option. Otherwise, the printing from the newest set is
selected.

Card names are expected in English. A translated name can be specified with the
-t option, which will return the original card names to which the translation
belongs.

testing
-------

Just run ./test.sh

updating
--------

When a new set is released, the card data retrieved from <http://mtgjson.com/>
should be updated. To do so, just trigger a rebuild of the database by deleting
~/.mtgtool/db.sqlite.

bugs
----

As of 2017-01-16, the data from <http://mtgjson.com/> is somewhat incomplete in
regards to translated names. Some examples: German "Zwang" should not only be
"Duress", but also "Coercion"; German "Sturmgeist" should be "Storm Spirit";
German "Dominieren" should not only be "Domineer", but also "Dominate".
