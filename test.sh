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
mkdir -p "$generated_files_dir"
./mtgtool.py > /dev/null
./mtgtool.py -c 'Raging Goblin' > "$generated_files_dir"/RagingGoblin
./mtgtool.py -c 'Valley Dasher' > "$generated_files_dir"/ValleyDasher
./mtgtool.py -c 'Research // Development' > "$generated_files_dir"/ResearchDevelopment
./mtgtool.py -t 'Sturmgeist' > "$generated_files_dir"/Sturmgeist
./mtgtool.py -t 'Wurmspiralmaschine' > "$generated_files_dir"/Wurmspiralmaschine
./mtgtool.py -c 'Volunteer Militia' -p 'PO2' > "$generated_files_dir"/VolunteerMilitia

# Compare metadata files.
for file in ./test/test_files/*; do
  basename=$(basename "$file")
  cmp_file="$generated_files_dir/$basename"
  printf "== %s diff test ==\n" "$cmp_file"
  diff "$file" "$cmp_file"
  if [ "$?" = "0" ]; then
    echo "== test SUCCESS =="
  else
    echo "== test FAILURE =="
  fi
done
