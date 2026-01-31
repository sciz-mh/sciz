--alter schema public rename to public_save;

--alter schema sciz rename to public;

-- SET synchronous_commit TO off;
--alter database sciz SET synchronous_commit TO off;
--SHOW synchronous_commit;
--SELECT pg_size_pretty( pg_database_size('sciz') );
--select file_name, pg_column_size(lo_get(oid)) from files; -- files inconnu
--SELECT relfilenode, relpages FROM pg_class WHERE relname = 'being';
--ALTER DATABASE sciz SET search_path TO sciz;

SELECT mail FROM sciz.user WHERE mail='91305.iab6sf7r@sciz.fr' LIMIT 1;
