
# Linux/OS X
pyinstaller --onefile --add-data templates/:templates --add-data static/:static swapfe.py

# Windows
pyinstaller --icon swapfe.ico --onefile --add-data "templates;templates" --add-data "static;static" swapfe.py


