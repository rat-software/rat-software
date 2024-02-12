### Setting up flask locally

```
(tool) > python -m venv venv
(tool) > source venv/bin/activate

(venv) > pip install -r requirements.txt
(venv) > export FLASK_APP=rat.py
(venv) > flask run
```

### Starting flask after set up
```
(tool) > source venv/bin/activate
(venv) > flask run

(venv) >> Press CTRL+C to quit
(venv) > deactivate
(tool) >>
```

runs on `localhost:5000`

### Step by Step Troubleshooting on server

#### 1. connect to server
```
ssh root@85.214.110.132
2PwvU#NGYZf6
```

#### 2. restart service
```
sudo systemctl restart rat
```
-- if problem persists --

#### 3. run app in virtualenv to get error message(/s)
```
cd /home/www/rat/
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

#### 4. fix until no errors are displayed, then
<pre>
press <b>ctrl + c</b>

deactivate
</pre>

repeat step 2 🎉 
