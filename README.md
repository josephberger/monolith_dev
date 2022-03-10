# Monolith

Very early alpha of Monolith

## Dependencies

Use the components in the docker-compose folder to deploy the elastic components and redis

- nmap
- python
- docker
- docker-compose
```bash
apt install nmap
```
docker - https://docs.docker.com/engine/install/ubuntu/

docker-compose - https://docs.docker.com/compose/install/

python - make sure you are using python3.8 (it may work on older versions but why??)

## Setting up Docker-Compose

Use the components in the docker-compose folder to deploy the elastic components and redis

```bash
cd docker-compose
docker-compose up -d
```

## Setting up python
This has only been tested on python3.8, but it may work on older versions.

```bash
python3 -m venv venv
source venv/bin/activate

(venv) pip3 install -r requirements.txt
```

## Create the .credentials.yaml file in the root folder

This is an alpha way of providing credentials for the initial netmiko discovery and will be changed in the future.  The id must be an integer and cannot be zero.  in the root of the project (monolith_dev) create the .credentials.yaml file.
```bash
touch .credentials.yaml
nano .credentials.yaml

- id: 1
  username: python
  password: python
  secret: python
- id: 2
  username: whoever
  password: somepassword
  secret: somepassword
```

## Modify and start the test_run.py

Change the subnet in test_run.py to whatever you like (this is a test so of course the finaly product will be done in the GUI)
```python
#change this subnet to whatever your lab environment is running on
for ip in ipaddress.IPv4Network("172.31.10.0/24"):
    result = default_queue.enqueue(sweep.run,
                                   args=(str(ip),),
                                   description=f'Sweep {str(ip)}')
```
```bash
python3 test_run.py
```
## Run the high and default workers

These workers do not run in the background so start them in a separate terminal or run them as a service
```bash
python3 high_worker.py
python3 default_worker.py
```

## Run the web server

Basic flask web service for testing (port 5000)
```bash
python3 run.py
 * Running on all addresses.
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://172.31.10.27:5000/ (Press CTRL+C to quit)
 * Restarting with stat
```
##Ports to send syslog to:

- 9001/udp - cisco-asa
- 9002/udp - cisco-ios (includes xr)
- 9506/udp - cisco-nxos
- 9100/udp - panos (traffic, threat, userid, hip, globalprotect, system)
- 5044/tcp - beats
- 
## License
[MIT](https://choosealicense.com/licenses/mit/)