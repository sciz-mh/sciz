/* xxx *
explain 
SELECT event_cdm.id AS event_cdm_id, event.id AS event_id, event.owner_id AS event_owner_id, event.owner_nom AS event_owner_nom, event.time AS event_time, event.mh_type AS event_mh_type, event.sciz_type AS event_sciz_type, event.mail_subject AS event_mail_subject, event.mail_body AS event_mail_body, event.rm AS event_rm, event.mm AS event_mm, event.px AS event_px, event.fatigue AS event_fatigue, event_cdm.mob_id AS event_cdm_mob_id, event_cdm.mob_nom AS event_cdm_mob_nom, event_cdm.mob_tag AS event_cdm_mob_tag, event_cdm.mob_age AS event_cdm_mob_age, event_cdm.mob_race AS event_cdm_mob_race, event_cdm.cdm_niv AS event_cdm_cdm_niv, event_cdm.blessure AS event_cdm_blessure, event_cdm.niv_min AS event_cdm_niv_min, event_cdm.niv_max AS event_cdm_niv_max, event_cdm.pdv_min AS event_cdm_pdv_min, event_cdm.pdv_max AS event_cdm_pdv_max, event_cdm.att_min AS event_cdm_att_min, event_cdm.att_max AS event_cdm_att_max, event_cdm.esq_min AS event_cdm_esq_min, event_cdm.esq_max AS event_cdm_esq_max, event_cdm.deg_min AS event_cdm_deg_min, event_cdm.deg_max AS event_cdm_deg_max, event_cdm.reg_min AS event_cdm_reg_min, event_cdm.reg_max AS event_cdm_reg_max, event_cdm.arm_min AS event_cdm_arm_min, event_cdm.arm_max AS event_cdm_arm_max, event_cdm.arm_phy_min AS event_cdm_arm_phy_min, event_cdm.arm_phy_max AS event_cdm_arm_phy_max, event_cdm.arm_mag_min AS event_cdm_arm_mag_min, event_cdm.arm_mag_max AS event_cdm_arm_mag_max, event_cdm.vue_min AS event_cdm_vue_min, event_cdm.vue_max AS event_cdm_vue_max, event_cdm.capa_desc AS event_cdm_capa_desc, event_cdm.capa_effet AS event_cdm_capa_effet, event_cdm.capa_tour AS event_cdm_capa_tour, event_cdm.capa_portee AS event_cdm_capa_portee, event_cdm.mm_min AS event_cdm_mm_min, event_cdm.mm_max AS event_cdm_mm_max, event_cdm.rm_min AS event_cdm_rm_min, event_cdm.rm_max AS event_cdm_rm_max, event_cdm.nb_att_tour AS event_cdm_nb_att_tour, event_cdm.vit_dep AS event_cdm_vit_dep, event_cdm.vlc AS event_cdm_vlc, event_cdm.vole AS event_cdm_vole, event_cdm.att_dist AS event_cdm_att_dist, event_cdm.att_mag AS event_cdm_att_mag, event_cdm.dla AS event_cdm_dla, event_cdm.sang_froid AS event_cdm_sang_froid, event_cdm.tour_min AS event_cdm_tour_min, event_cdm.tour_max AS event_cdm_tour_max, event_cdm.chargement AS event_cdm_chargement, event_cdm.bonus_malus AS event_cdm_bonus_malus
        FROM event JOIN event_cdm ON event_cdm.id = event.id
        WHERE event_cdm.mob_nom = 'Diablotin' AND event_cdm.mob_age = 'Mineur' ORDER BY event.time DESC
-- */

/* coterie *
--select * from user_partage where coterie_id=332 or user_id=91305;
select coterie_id, count(*) from user_partage group by coterie_id order by count(*) desc;
-- */

/* WEB *
--explain
SELECT event.id AS event_id, event.owner_id AS event_owner_id, event.owner_nom AS event_owner_nom, event.time AS event_time, event.mh_type AS event_mh_type, event.sciz_type AS event_sciz_type, event.mail_subject AS event_mail_subject, event.mail_body AS event_mail_body, event.rm AS event_rm, event.mm AS event_mm, event.px AS event_px, event.fatigue AS event_fatigue 
FROM event 
WHERE event.owner_id IN (68481, 109092, 80117, 109308, 91305, 112780, 112895) AND event.time > '1970-01-01T01:00:00'::timestamp ORDER BY event.time DESC, event.id DESC 
 LIMIT 25 OFFSET 0
-- */
 
 /* WEB Unitaire *
--explain
SELECT event.id AS event_id, event.owner_id AS event_owner_id, event.owner_nom AS event_owner_nom
, event.time AS event_time, event.mh_type AS event_mh_type, event.sciz_type AS event_sciz_type
, event.mail_subject AS event_mail_subject
, event.mail_body AS event_mail_body
, event.rm AS event_rm, event.mm AS event_mm, event.px AS event_px, event.fatigue AS event_fatigue 
FROM event 
WHERE event.owner_id = 111145 
AND event.time > '1970-01-01T01:00:00'::timestamp 
ORDER BY event.time ASC 
 LIMIT 25 OFFSET 0
 -- */
 
 /* WEB indirect *
SELECT event.id AS event_id, event.owner_id AS event_owner_id, event.owner_nom AS event_owner_nom, event.time AS event_time, event.mh_type AS event_mh_type, event.sciz_type AS event_sciz_type, event.mail_subject AS event_mail_subject, event.mail_body AS event_mail_body, event.rm AS event_rm, event.mm AS event_mm, event.px AS event_px, event.fatigue AS event_fatigue 
FROM event
where id in
(
SELECT event.id  
FROM event
WHERE event.owner_id = 112898 ORDER BY event.time DESC, event.id DESC 
 LIMIT 25 OFFSET 0
 )
 ORDER BY event.time DESC, event.id DESC 
--  */

-- analyse event

/* WEB sous requête *
explain
SELECT event.id  
FROM event
WHERE event.owner_id = 108942 ORDER BY event.time DESC, event.id DESC 
 LIMIT 25 OFFSET 0
-- */

/* *
SELECT count(*) 
FROM event 
WHERE event.owner_id IN (68481, 109092, 80117, 109308, 91305, 112780, 112895) AND event.time > '1970-01-01T01:00:00'::timestamp
-- */

/* index *
--CREATE INDEX lieu_pos_idx ON public.lieu (pos_x,pos_y,pos_n);
analyse public.lieu; 
-- */

-- ALTER ROLE sciz SET log_statement TO 'all'; -- 'none'
-- ALTER ROLE sciz SET log_duration TO 'on'; -- 'off'
--ALTER ROLE sciz SET synchronous_commit TO off; -- 'off'
--start transaction;
--SET LOCAL synchronous_commit TO off;
--commit;
select usename,useconfig from pg_shadow ;

