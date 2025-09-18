# Get the binary build of Cbc solver on Windows
curl -OL https://github.com/coin-or/Cbc/releases/download/releases%2F2.10.12/Cbc-releases.2.10.12-w64-msvc17-md.zip
# Make directory for Cbc
mkdir cbc
# Unzipping binary
tar -xf Cbc-releases.2.10.12-w64-msvc17-md.zip -C ./cbc --strip-components 1

# Check if we got it for now
cd cbc
dir
