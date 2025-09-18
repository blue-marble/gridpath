# Get the binary build of Cbc solver on Windows
curl -OL https://github.com/coin-or/Cbc/releases/download/releases%2F2.10.12/Cbc-releases.2.10.12-w64-msvc17-md.zip
# Make directory for Cbc
mkdir cbc
# Unzipping binary
unzip Cbc-releases.2.10.12-w64-msvc17-md.zip -d ./cbc

# Check if we got it for now
pwd
cd cbc/bin
pwd
dir
D:/a/gridpath/gridpath/cbc/bin/cbc.exe --version

echo "D:\a\gridpath\gridpath\cbc\bin" >> $GITHUB_PATH
