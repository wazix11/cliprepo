# ClipRepo
ClipRepo is a project intended to make searching/watching Twitch clips easier. The general concept is to automatically import clips from specified channels. These clips are then sorted by volunteers by adding metadata in the form of pre-defined options that are then made available for searching/sorting.

## Deployment on Linux
Check out [DEPLOY.md](DEPLOY.md) for instructions on deploying on an Ubuntu server.

### Deploying Application Updates
The typical process for deploying application updates:
```
(venv) $ git pull
(venv) $ sudo supervisorctl stop all
(venv) $ flask db upgrade
(venv) $ sudo supervisorctl start all
```
If no database changes have been made, the `flask db upgrade` command is not needed.