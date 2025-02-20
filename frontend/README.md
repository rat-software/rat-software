## Set up the web interface (Flaks Application / Frontend)
#### Access the documentation for the frontend at: https://searchstudies.org/rat-frontend-documentation/
- Create a virtual environment

```bash
python -m venv venv_rat_frontend
source venv_rat_frontend/bin/activate
```

- Install Python packages from the `/frontend/requirements.txt`
```
python -m pip install --no-cache-dir -r requirements.txt
```
- Add own data to config file `config.py`

| Setting | Example |
| ---- | ---- |
| SQLALCHEMY_DATABASE_URI | 'postgresql://USERNAME:PASSWORD@SERVER/DBNAME' |
| SECRET_KEY | [How to generate](https://flask-security-too.readthedocs.io/en/stable/quickstart.html#sqlalchemy-application) |
| SECURITY_PASSWORD_SALT | [How to generate](https://flask-security-too.readthedocs.io/en/stable/quickstart.html#sqlalchemy-application) |
| MAIL_SERVER | server.domain.de |
| MAIL_USERNAME | name@mail.de |
| MAIL_PASSWORD | password |

* Google Mail does no longer allow 3rd party apps to send mails, if there is no other mail adress you can use [Mailtrap](https://mailtrap.io/)
- Start Flask
```
export FLASK_APP=rat.py
flask run
```

