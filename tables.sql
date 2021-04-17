CREATE USER 'ubuntu'@'localhost' IDENTIFIED WITH mysql_native_password  BY '1234567890';
GRANT ALL PRIVILEGES ON * . * TO 'ubuntu'@'localhost';
SELECT @@"datadir";

-- mysql -u ubuntu -p

DROP DATABASE laserdb;
CREATE DATABASE laserdb;
USE laserdb;

-- delete table
SET FOREIGN_KEY_CHECKS=0; DROP TABLE machine; SET FOREIGN_KEY_CHECKS=1;

CREATE TABLE machine(
   id INT PRIMARY KEY AUTO_INCREMENT,
   name VARCHAR(50) NOT NULL,          -- laser name (SL200, SL3, SL4)
   ip VARCHAR(50) NOT NULL,            -- ip address (10.100.102.4)
   shared_folder VARCHAR(50) NOT NULL  -- lc.txt file location (my_shared_folder)
);

INSERT INTO machine (name,ip,shared_folder) VALUES ('SL200','10.100.102.4','test');
INSERT INTO machine (name,ip,shared_folder) VALUES ('SL3','10.100.102.4','test1');
INSERT INTO machine (name,ip,shared_folder) VALUES ('FR4','10.100.102.4','test2');

UPDATE machine SET shared_folder = 'test2' WHERE name = 'SL3'

TRUNCATE TABLE temperature;
TRUNCATE TABLE keyswitch;
TRUNCATE TABLE activity;
TRUNCATE TABLE error;

CREATE TABLE temperature(
   id BIGINT PRIMARY KEY AUTO_INCREMENT,
   machine_id INT NOT NULL,
   event_sequence INT NOT NULL,
   submission_date DATETIME(6),
   sensor_id INT NOT NULL,
   value FLOAT NOT NULL,
   FOREIGN KEY (machine_id) REFERENCES machine(id)
);

CREATE TABLE keyswitch(
   id BIGINT PRIMARY KEY AUTO_INCREMENT,
   machine_id INT NOT NULL,
   event_sequence INT NOT NULL,
   submission_date DATETIME(6),
   is_enabled BOOLEAN NOT NULL,
   FOREIGN KEY (machine_id) REFERENCES machine(id)
);

CREATE TABLE activity(
   id BIGINT PRIMARY KEY AUTO_INCREMENT,
   machine_id INT NOT NULL,
   event_sequence INT NOT NULL,
   submission_date DATETIME(6),
   is_active BOOLEAN NOT NULL,
   FOREIGN KEY (machine_id) REFERENCES machine(id)
);

CREATE TABLE error(
   id BIGINT PRIMARY KEY AUTO_INCREMENT,
   machine_id INT NOT NULL,
   event_sequence INT NOT NULL,
   submission_date DATETIME(6),
   is_error BOOLEAN NOT NULL,
   FOREIGN KEY (machine_id) REFERENCES machine(id)
);

USE laserdb;
ALTER TABLE machine
ADD COLUMN is_active BOOLEAN NOT NULL;

-- SELECT * FROM `laserdb`.`activity` LIMIT 100;
-- SELECT * FROM `laserdb`.`error` LIMIT 100;
-- SELECT * FROM `laserdb`.`keyswitch` LIMIT 100;
-- SELECT * FROM `laserdb`.`temperature` LIMIT 100;