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
mkdir -p "$generated_files_dir"
./mtgtool.py > /dev/null
./mtgtool.py -c 'Raging Goblin' > "$generated_files_dir"/RagingGoblin
./mtgtool.py -c 'Valley Dasher' > "$generated_files_dir"/ValleyDasher
./mtgtool.py -c 'Research // Development' > "$generated_files_dir"/ResearchDevelopment
./mtgtool.py -t 'Sturmgeist' > "$generated_files_dir"/Sturmgeist
./mtgtool.py -t 'Wurmspiralmaschine' > "$generated_files_dir"/Wurmspiralmaschine
./mtgtool.py -c 'Volunteer Militia' -p 'PO2' > "$generated_files_dir"/VolunteerMilitia
./mtgtool.py -c 'Assassinate' -p 'PC1' > "$generated_files_dir"/Assassinate
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_good > "$generated_files_dir"/testdeck_good
./mtgtool.py --test-parser "$expected_files_dir"/deckfiles/testdeck_empty > "$generated_files_dir"/testdeck_empty

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
