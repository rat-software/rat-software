# Result Assessment Tool (RAT) backend application
- The backend application consists of of three sub applications which could be installed separately for a better resource management. However in most cases an installation of all apps on one server should be decent.
- The sub applications are:
  - 

#### Quick Links
- Kanban: https://github.com/yagci/rat/projects/1
- Online-Demo: http://85.214.110.132/

#### Server
OS: Debian 10 64bit (CPU vCores 8, RAM 32 GB, Speicherplatz 800 GB)

```
host: h2920015.stratoserver.net  
ip: 85.214.110.132
user: root  
pw: 2PwvU#NGYZf6
```
#### DB

Main:
```
ip: 85.214.110.132
port: 5432
database: rat
user: rat
pw: 6n9TYHN
```
Secondary (for app development)
```
ip: 85.214.110.132
port: 5432
database: rat_new
user: rat
pw: 6n9TYHN
```
