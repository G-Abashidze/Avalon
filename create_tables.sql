drop table if exists users;
create table users (
	id serial primary key,
	username varchar(100),
	password varchar(100),
	EventTime timestamp
);

drop table if exists AvalonSessions;
create table AvalonSessions (
	id serial primary key,
	guid varchar(36),
	SessionName varchar(100),
	EventTime timestamp
);


insert into users (username, password, EventTime ) values ('test', 'test', NOW());
insert into avalonSessions (guid, sessionname, eventtime) VALUES (gen_random_uuid (), 'testName', NOW() );
