# CHANGELOG

## 0.0.2 - 2021-10-04
ADDED: Windows 10 (x86) standalone binary. First binary release.
ADDED: Linux (x86) standalone binary. First binary release
ADDED: Multithreading with the **threading** module for actively handling flask startup
ADDED: URL requests for downloading current swap CLI with the **requests** module
ADDED: BeautifulSoup for parsing github for new swap CLI release with the **bs4** module
ADDED: PyQt5 support for showing a loading screen while determining version information
ADDED: Downloading Windows **qrcode.exe** for support with QR codes in swaps.
CHANGED: Resource path for templates and other files needed for binary release
CHANGED: Local directory in user's home directory for saving swap CLI database and command. ($HOME/AtomicSwaps/swap)
FIXED: Headers in HTML/CSS files to be uniform across interfaace
FIXED: No QR Code executable checks causing undisplayed QR code in swap interface


