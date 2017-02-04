#!/bin/sh

diff_test()
{
  expected_file="$1"
  generated_file="$2"
  printf "== %s diff test ==\n" "$generated_file"
  diff "$expected_file" "$generated_file"
  if [ "$?" = "0" ]; then
    echo "== test SUCCESS =="
  else
    echo "== test FAILURE =="
  fi
}

# Remove DB, so its initialization/creation is checked.
rm -rf ~/.mtgtool/

# Set up test directory, run file creations.
generated_files_dir=./test/test_dir
expected_files_dir=./test/test_files
rm -rf "$generated_files_dir"
mkdir -p "$generated_files_dir"
./mtgtool.py > /dev/null
./mtgtool.py -c 'Raging Goblin' > "$generated_files_dir"/RagingGoblin
./mtgtool.py -c 'Valley Dasher' > "$generated_files_dir"/ValleyDasher
./mtgtool.py -c 'Research // Development' > "$generated_files_dir"/ResearchDevelopment
./mtgtool.py -t 'Sturmgeist' > "$generated_files_dir"/Sturmgeist
./mtgtool.py -t 'Wurmspiralmaschine' > "$generated_files_dir"/Wurmspiralmaschine
./mtgtool.py -c 'Volunteer Militia' -p 'PO2' > "$generated_files_dir"/VolunteerMilitia
./mtgtool.py -c 'Assassinate' -p 'PC1' > "$generated_files_dir"/Assassinate
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_good_1 > "$generated_files_dir"/testdeck_good_1
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_good_2 > "$generated_files_dir"/testdeck_good_2
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_empty > "$generated_files_dir"/testdeck_empty
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_1 > "$generated_files_dir"/testdeck_bad_1
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_2 > "$generated_files_dir"/testdeck_bad_2
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_3 > "$generated_files_dir"/testdeck_bad_3
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_4 > "$generated_files_dir"/testdeck_bad_4
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_5 > "$generated_files_dir"/testdeck_bad_5
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_6 > "$generated_files_dir"/testdeck_bad_6
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_7 > "$generated_files_dir"/testdeck_bad_7
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_8 > "$generated_files_dir"/testdeck_bad_8
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_9 > "$generated_files_dir"/testdeck_bad_9
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_bad_10 > "$generated_files_dir"/testdeck_bad_10

# Compare metadata files.
for file in "$expected_files_dir"/*; do
  if [ ! -d "$file" ]; then
    basename=$(basename "$file")
    cmp_file="$generated_files_dir/$basename"
    printf "== %s diff test ==\n" "$cmp_file"
    diff "$file" "$cmp_file"
    if [ "$?" = "0" ]; then
      echo "== test SUCCESS =="
    else
      echo "== test FAILURE =="
    fi
  fi
done
