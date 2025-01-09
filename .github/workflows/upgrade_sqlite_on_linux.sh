# required to support UNIXEPOCH
# installing build: 3.45.0
wget https://www.sqlite.org/2024/sqlite-autoconf-3450000.tar.gz
# unzipping build
tar -xvzf sqlite-autoconf-3450000.tar.gz

# below steps are for installing the build in /usr/local/bin
cd sqlite-autoconf-3450000 || exit
./configure
make
sudo make install

# remove the previous version
sudo apt-get remove -y --auto-remove sqlite3
