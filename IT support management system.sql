create database it_support;
use it_support;
create table users(
    id int primary key AUTO_INCREMENT,
    name varchar(100) not null,
    username varchar(50) UNIQUE not null ,
    password varchar(100) not null,
    role varchar(20) not null,
    department varchar(100)
);
show tables;
desc users;

insert into users(name,username,password,role,department)
values('Mani','petta_mani','mani@123','Employee','Development');
insert into users(name,username,password,role,department)
values('Ajay','pavoor_ajay','ajay@03','IT Support','IT');
insert into users(name,username,password,role,department)
values('Admin','im_admin','admin@357','Admin','Management');

select * from users; 

create table categories(
    id int primary key AUTO_INCREMENT,
    category_name varchar(50) unique not null
);
insert into categories(category_name)
values
('Hardware'),
('Software'),
('Network'),
('Access'),
('Email'),
('Other');
select * from categories;


create table tickets (
    id int primary key AUTO_INCREMENT,
    user_id int not null,
    category_id int not null,
    title varchar(200) not null,
    description text not null,
    priority varchar(20) not null default 'Medium',
    status varchar(20) not null default 'Open',
    assigned_to int null,
    created_at datetime default CURRENT_TIMESTAMP,
    updated_at datetime default CURRENT_TIMESTAMP,
    resolved_at datetime null,

    foreign key (user_id) references users(id),
    foreign key (category_id) references categories(id),
    foreign key (assigned_to) references users(id)
);

select * from tickets;
desc tickets;
insert into tickets
(user_id,category_id,title,description,priority)values
( 1,3,
'wi-Fi is not working',
'My laptop is connected to Wi-Fi but I cannot access any websites.',
'High');


create table ticket_comments(
    id int primary key auto_increment,
    ticket_id int not null,
    user_id int not null,
    comment text not null,
    created_at datetime default CURRENT_TIMESTAMP,

    foreign key (ticket_id) references tickets(id),
    foreign key (user_id) references users(id)
);

select * from ticket_comments;

create table ticket_history(
    id int primary key auto_increment,
    ticket_id int not null,
    action varchar(100) not null,
    changed_by int not null,
    old_status varchar(20),
    new_status varchar(20),
    changed_at datetime default current_timestamp,

    foreign key (ticket_id) references tickets(id),
    foreign key (changed_by) references users(id)
);

select * from ticket_history;    

UPDATE tickets
SET assigned_to = 2,
    status = 'OPEN'
WHERE id = 3;
SELECT id,title,status
FROM tickets
WHERE id =3; 
USE it_support;

SELECT id, title, priority, status, assigned_to
FROM tickets
ORDER BY id DESC;

ALTER TABLE tickets
ADD COLUMN resolution_note TEXT NULL;

desc users;
insert into users(name,username,password,role,department)
values
('Basith','abdul_basith','basith@02','Employee','Sales'),
('Siva','siva_ganesh','siva@42','Employee','Finance'),
('Ragavan','e_ragav','ragavan@33','Employee','Marketing'), 
('Subickson','subi_son','subi@12','Employee','HR'),
('Salavudeen','salam_aarif','salam@37','IT Support','IT'),
('Suresh','g_suresh','suresh@44','IT Support','IT');

select * from users;

USE it_support;

START TRANSACTION;

UPDATE tickets
SET
    user_id = CASE id
        WHEN 1 THEN (SELECT id FROM users WHERE username = 'petta_mani')
        WHEN 2 THEN (SELECT id FROM users WHERE username = 'abdul_basith')
        WHEN 3 THEN (SELECT id FROM users WHERE username = 'siva_ganesh')
        WHEN 4 THEN (SELECT id FROM users WHERE username = 'e_ragav')
        WHEN 5 THEN (SELECT id FROM users WHERE username = 'subi_son')
        WHEN 6 THEN (SELECT id FROM users WHERE username = 'petta_mani')
        WHEN 7 THEN (SELECT id FROM users WHERE username = 'abdul_basith')
        WHEN 8 THEN (SELECT id FROM users WHERE username = 'siva_ganesh')
    END,

    assigned_to = CASE id
        WHEN 1 THEN (SELECT id FROM users WHERE username = 'payoor_ajay')
        WHEN 2 THEN NULL
        WHEN 3 THEN (SELECT id FROM users WHERE username = 'salam_aarif')
        WHEN 4 THEN (SELECT id FROM users WHERE username = 'g_suresh')
        WHEN 5 THEN (SELECT id FROM users WHERE username = 'payoor_ajay')
        WHEN 6 THEN (SELECT id FROM users WHERE username = 'salam_aarif')
        WHEN 7 THEN (SELECT id FROM users WHERE username = 'g_suresh')
        WHEN 8 THEN (SELECT id FROM users WHERE username = 'payoor_ajay')
    END

WHERE id BETWEEN 1 AND 8;

COMMIT;
SELECT
    t.id,
    t.title,
    u.name AS employee,
    s.name AS assigned_support,
    t.status,
    t.priority
FROM tickets t
JOIN users u ON t.user_id = u.id
LEFT JOIN users s ON t.assigned_to = s.id
ORDER BY t.id;

USE it_support;

SELECT id, name, username, role
FROM users
ORDER BY id;

USE it_support;

CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    ticket_id INT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);
desc notifications;

SELECT id, user_id, ticket_id, message, is_read
FROM notifications
ORDER BY id DESC;

UPDATE users
SET username = 'im_admin'
WHERE id = 3;

SELECT id, name, username, role, department
FROM users
WHERE id = 3;

UPDATE users
SET
    name = 'Admin',
    username = 'im_admin',
    password = 'admin@357',
    role = 'Admin',
    department = 'Management'
WHERE id = 3;

SELECT id, name, username, password, role, department
FROM users
WHERE id = 3;

ALTER TABLE users
ADD COLUMN photo VARCHAR(255) DEFAULT NULL;

desc users;

SELECT id, username, photo
FROM users
WHERE id = 3;

use it_support;
desc categories;
   