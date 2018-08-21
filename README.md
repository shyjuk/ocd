# OCD

A basic application for automatic call distribution based on a uploaded call distribution list.
Based on Asterisk PBX and it's ARI functionality, Flask and MySQL.

Basic functionalities:
- Upload a CSV list. (Fields: Name, Phone)
- Upload sound files.
- Start a outbound call campain using the uploaded list & sound files.
- Current call status
- Report. (Fields: Phone, Status, Reason,Call Duration)
- Settings. (Asterisk & ARI settings)

## Install dependencies

Clone the repo and run the below command from the repo
- sudo pip install -r requirements.txt

## MySQL Commands
- create database ocd;
- use ocd;
- create table users(id INT(10) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), email VARCHAR(100), username VARCHAR(30), password VARCHAR(100), register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
- create table articles ( id  INT(11) AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), author VARCHAR(100), body TEXT, create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

- CREATE USER 'ocduser'@'localhost' IDENTIFIED BY 'ocdpass';
- GRANT ALL PRIVILEGES ON ocd.* TO 'ocduser'@'localhost';
- 
## Configure app.py
- Edit app.py and add the MySQL credentials created above.

### Running the app

```bash
python app.py
```

