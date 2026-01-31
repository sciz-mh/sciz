/* vacuum */
SELECT
  schemaname, relname,
  last_vacuum, last_autovacuum,
  vacuum_count, autovacuum_count  -- not available on 9.0 and earlier
FROM pg_stat_user_tables
order by last_autovacuum desc;
-- */

--select * FROM pg_stat_user_tables;

/* analyse */
SELECT
  schemaname, relname
  , last_analyze, last_autoanalyze
FROM pg_stat_user_tables
order by last_autoanalyze desc;
-- */

/* both */
SELECT
  schemaname, relname
  , last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
order by case when last_autoanalyze is null then last_autovacuum when last_autovacuum  is null then last_autoanalyze  when last_autoanalyze > last_vacuum then last_autoanalyze else last_autovacuum end desc;
-- */

SELECT * FROM pg_settings WHERE name LIKE '%vacuum%' or name LIKE '%analy%' order by name;

-- trace
-- arrêt vacuum (dans postresql.conf) le 13/11/2023 matin
--alter schema public_save rename to public;

vacuum full being_mob_private;
