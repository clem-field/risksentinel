This portion of the Repo is used for development testing of the User Interface (UI) of risksentinel.

Some python script files are pulled in to all easier calls to them without running a virtual environment or needing a server to handle the interactions.

To use:
1. Open the index.html file in a browser
2. Use the webpage / buttons to call functions in ui_script.js

To develop:
1. Update index.html with the appropriate UI updates
    - index.html uses the style guides from style.css
    - limit scripts and utilize calls to ui_script.js
2. add scripts to ui_script.js
    - add listeners and scripts to this file as scripting in index.html should be limited to avoid CSS activities
3. Share the updates and functions with other users and migrate them to the Node.js environment if needed.