-- droits 
alter user sciz set search_path to sciz;	-- nécessite d'être excétuté sous le compte sciz
alter user sciz_admin set search_path to sciz;
GRANT SELECT, update, insert, DELETE ON all tables in schema sciz TO sciz;
GRANT select, USAGE ON ALL SEQUENCES IN schema sciz to sciz;
ALTER DEFAULT PRIVILEGES IN SCHEMA sciz GRANT ALL PRIVILEGES ON TABLES TO sciz;
ALTER DEFAULT PRIVILEGES IN SCHEMA sciz GRANT SELECT, USAGE  ON SEQUENCES TO sciz;

-- schema
alter schema public rename to sciz;
create schema public;
