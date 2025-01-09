rm -rf build

# compile
cmake -S . -Bbuild
make -C ./build -j

# run
./main

exit 0