# gerrit-quick-viewer

Web-based application to get quick access to administrative functions of Gerrit Code Review system through the REST APIs
([python-gerritclient](https://github.com/tivaliy/python-gerritclient) package).
Ability to perform *View*, *Modify*, *Delete* or *Create* actions depends on Gerrit user access rights.

## Quick start

1. Clone `gerrit-quick-viewer` project from repository: `git clone https://github.com/tivaliy/gerrit-quick-viewer.git`.
2. Change directory to project one `cd gerrit-quick-viewer`.
3. Create isolated Python environment `virtualenv gerritquickviewer_venv` and activate it `source gerritquickviewer_venv/bin/activate`.
4. Install `gerrit-quick-viewer` with all necessary dependencies: `pip install -r requirements.txt`.
5. Update `config.py` file to meet your requirements, e.g. `GERRIT_URL = 'http://ci.infra.local/gerrit`
6. Set `FLASK_APP` environment variable `export FLASK_APP=gerritviewer/gerrit-viewer.py`.
7. Run Flask `flask run`
8. Open Web-browser `http://127.0.0.1:5000/`. Some actions required authorization, so you have to be logged in with your Gerrit HTTP credentials.