-- mail
SELECT mail || '/' FROM public.user WHERE mail='91305.iab6sf7r@sciz.brion.fr' or mail='91305.iab6sf7r@sciz.fr'  LIMIT 1;

select * from public.user where id=91305;

select CURRENT_DATE - interval '6 MONTH';

select count(*) from being_mob_private;

select * from being_mob where id=4950376;
select * from being_mob_private where mob_id=4950376 order by last_seen_at desc;
select * from being where id=4950376;

-- tests dump
SELECT last_value, is_called FROM public.being_id_seq;

-- copy DB, change Schema
create schema toto;

-- tmp
select count(*) from event;
EXPLAIN (ANALYZE, BUFFERS, TIMING) select * from event where time < (CURRENT_DATE - interval '60 MONTH');
EXPLAIN (ANALYZE, BUFFERS, TIMING) delete from event where id=613825;