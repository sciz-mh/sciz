--select * from user_partage limit 10;

/* coterie *
select * from user_partage where user_id=113023
union 
select * from user_partage where user_id=113020
order by coterie_id, user_id 
;
-- */

--select user_id, count(*) from user_partage where coterie_id = 309 group by user_id order by user_id;
--select * from user_partage where coterie_id = 309 order by user_id;
--select * from user_partage where user_id=113275 order by user_id;
--select troll_id, viewer_id, pdv, base_pdv_min, base_pdv_max, bonus_pdv_phy, bonus_pdv_mag, last_event_update_at, last_event_update_by from being_troll_private where viewer_id=112991 and troll_id in (113270, 113275, 113271, 113137) order by troll_id;
--select troll_id, viewer_id, pdv, base_pdv_min, base_pdv_max, bonus_pdv_phy, bonus_pdv_mag, last_event_update_at, last_event_update_id , last_event_update_by from being_troll_private where troll_id = 91305 order by troll_id, viewer_id;
--select * from event_user where next_dla is not null order by next_dla desc;
--select max(id) from event_user where next_dla is null and old_dla is null;
--select * from event_user where id >= 4287727 order by id asc;
select * from "being" where id=3750 ;
--select * from hook where coterie_id=309;
--select * from hook where jwt='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODA2MzE0NzMsIm5iZiI6MTU4MDYzMTQ3MywianRpIjoiNGFjNTlmY2EtYTQ4Ny00OTFiLTg2ZWEtNmU1ODY3NjRmYTYwIiwiaWRlbnRpdHkiOjE2OTUsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyIsInVzZXJfY2xhaW1zIjp7Imhvb2tfdHlwZSI6IkhPT0siLCJpZCI6MTY5NSwidHlwZSI6IkRpc2NvcmQifX0.Rkdf7Q6VL_N26d3SwOmDi4hd_JnHtKi2Izt6Br6cci4';
--select user_id, coterie_id, count(*) from user_partage where "start" < now() and ("end" > now() or "end" is null) group by user_id, coterie_id having count(*) > 1 order by coterie_id, user_id;

--select * from event where owner_id=113023 order by time desc limit 10;

--select count(*) from event_tresor et left outer join ""event"" e on e.id=et.id where e.id is null;

--select sciz_type, count(*) from event group by sciz_type ;

--select e.id from event e left outer join event_tresor et on et.id=e.id and e.sciz_type='Trésor' where et.id is null;

--select * from event where id=11192;
--select * from event where id=176;
--select * from public.user where id=113087 ;

--select * from public.user where id=91305;
--rollback;
--start transaction;
--update public.user set max_mh_sp_static=4 where id=91305;
--SET LOCAL synchronous_commit TO off;
--commit;