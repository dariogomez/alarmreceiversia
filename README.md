# alarmreceiversia
A python script to manage and dispatch SIA-IP messages originated from security systems

## Requiered packs
```
pip install requests pycryptodome
```

## config file
In /etc/alarmReceiver.conf
```
[DEFAULT]
telegram_message_url = https://api.telegram.org/botXXXXX:XXXX/sendMessage?chat_id=-XXXXX
server_port = 5002

post_send = True
post_send_url = http://127.0.0.1:8000/post/
```
