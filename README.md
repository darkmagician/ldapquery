# ldapquery

## Introduction

It is used for query ldap attributes based on the given sAMAccountName. 



## Usage



### Requirements

```
pip install -r requirements
```



### Run

export the environment and run

```shell
export LDAP_PASS=xxx
export LDAP_SERVER=ldap://xxx
export LDAP_USER=xxx
export LDAP_BASE=xxxx
```



```shell
python ldapquery.py
```



### Client Call

run curl or past the command in the browser

```shell
<server ip>:4084/account?sAMAccountName=xxxx
```



## Docker Run

build docker

```
docker build -t ldapquery .
```



create a env.txt with the following content

```
LDAP_PASS=xxx
LDAP_SERVER=ldap://xxx
LDAP_USER=xxx
LDAP_BASE=xxxx
```

start docker

```
docker run -d --restart always --net=host --name ldapquery --env-file=env.txt ldapquery
```



