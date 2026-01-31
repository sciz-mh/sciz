CREATE INDEX being_mob_private_last_event_update_id_idx ON public.being_mob_private (last_event_update_id);
CREATE INDEX being_mob_private_last_event_update_by_idx ON public.being_mob_private (last_event_update_by);
CREATE INDEX being_mob_private_last_reconciliation_by_idx ON public.being_mob_private (last_reconciliation_by);
CREATE INDEX being_mob_private_last_seen_by_idx ON public.being_mob_private (last_seen_by);
CREATE INDEX being_mob_private_mob_id_idx ON public.being_mob_private (mob_id);
CREATE INDEX being_mob_private_owner_id_idx ON public.being_mob_private (owner_id);
CREATE INDEX being_mob_private_viewer_id_idx ON public.being_mob_private (viewer_id);

CREATE INDEX event_aa_troll_id_idx ON public.event_aa (troll_id);

CREATE INDEX being_troll_guilde_id_idx ON public.being_troll (guilde_id);
CREATE INDEX being_troll_maisonnee_id_idx ON public.being_troll (maisonnee_id);

CREATE INDEX being_troll_private_viewer_id_idx ON public.being_troll_private (viewer_id);
CREATE INDEX being_troll_private_last_sp4_update_by_idx ON public.being_troll_private (last_sp4_update_by);
CREATE INDEX being_troll_private_last_seen_by_idx ON public.being_troll_private (last_seen_by);
CREATE INDEX being_troll_private_last_reconciliation_by_idx ON public.being_troll_private (last_reconciliation_by);

CREATE INDEX being_troll_private_capa_viewer_id_idx ON public.being_troll_private_capa (viewer_id);
CREATE INDEX being_troll_private_capa_metacapa_id_idx ON public.being_troll_private_capa (metacapa_id);

CREATE INDEX champi_private_viewer_id_idx ON public.champi_private (viewer_id);
CREATE INDEX champi_private_owner_id_idx ON public.champi_private (owner_id);
CREATE INDEX champi_private_picker_id_idx ON public.champi_private (picker_id);
CREATE INDEX champi_private_last_seen_by_idx ON public.champi_private (last_seen_by);
CREATE INDEX champi_private_last_event_update_by_idx ON public.champi_private (last_event_update_by);
CREATE INDEX champi_private_last_event_update_id_idx ON public.champi_private (last_event_update_id);
CREATE INDEX champi_private_last_reconciliation_by_idx ON public.champi_private (last_reconciliation_by);

CREATE INDEX event_battle_att_id_idx ON public.event_battle (att_id);
CREATE INDEX event_battle_def_id_idx ON public.event_battle (def_id);
CREATE INDEX event_battle_autre_id_idx ON public.event_battle (autre_id);
CREATE INDEX event_battle_lieu_id_idx ON public.event_battle (lieu_id);
CREATE INDEX event_battle_tresor_id_idx ON public.event_battle (tresor_id);
CREATE INDEX event_battle_champi_id_idx ON public.event_battle (champi_id);
CREATE INDEX event_battle_capa_meta_id_idx ON public.event_battle (capa_meta_id);

CREATE INDEX event_cdm_mob_id_idx ON public.event_cdm (mob_id);

CREATE INDEX event_champi_champi_id_idx ON public.event_champi (champi_id);

CREATE INDEX event_cp_piege_id_idx ON public.event_cp (piege_id);

CREATE INDEX event_follower_follower_id_idx ON public.event_follower (follower_id);

CREATE INDEX event_tp_portail_id_idx ON public.event_tp (portail_id);

CREATE INDEX event_tresor_tresor_id_idx ON public.event_tresor (tresor_id);

CREATE INDEX hook_coterie_id_idx ON public.hook (coterie_id);
CREATE INDEX hook_last_event_id_idx ON public.hook (last_event_id);

CREATE INDEX lieu_owner_id_idx ON public.lieu (owner_id);
CREATE INDEX lieu_last_seen_by_idx ON public.lieu (last_seen_by);

CREATE INDEX tresor_private_viewer_id_idx ON public.tresor_private (viewer_id);
CREATE INDEX tresor_private_owner_id_idx ON public.tresor_private (owner_id);
CREATE INDEX tresor_private_metatresor_id_idx ON public.tresor_private (metatresor_id);
CREATE INDEX tresor_private_last_seen_by_idx ON public.tresor_private (last_seen_by);
CREATE INDEX tresor_private_last_event_update_by_idx ON public.tresor_private (last_event_update_by);
CREATE INDEX tresor_private_last_reconciliation_by_idx ON public.tresor_private (last_reconciliation_by);

CREATE INDEX user_mail_idx ON public."user" (mail);

CREATE INDEX user_partage_coterie_id_idx ON public.user_partage (coterie_id);
CREATE INDEX user_partage_user_id_idx ON public.user_partage (user_id);

-- time
CREATE INDEX event_time_idx ON public."event" ("time");
CREATE INDEX being_mob_private_last_seen_at_idx ON public.being_mob_private (last_seen_at);

-- optimisation pour suppression
CREATE INDEX being_mob_private_pos_x_idx ON public.being_mob_private (pos_x,niv_min);

-- comptes
select count(*) from being_mob_private;

--
-- cleanup
--

-- event

delete from event where "time" < '01/01/2021';

CREATE INDEX CONCURRENTLY being_mob_private_niv_x_idx ON public.being_mob_private (niv_min,pos_x);
delete FROM being_mob_private 
where (last_event_update_at is null or last_event_update_at < (CURRENT_DATE - interval '6 MONTH'))
and (last_seen_at is null or last_seen_at < (CURRENT_DATE - interval '6 MONTH'))
and (last_reconciliation_at is null or last_reconciliation_at < (CURRENT_DATE - interval '6 MONTH'))
and pos_x is null and pos_y is null and pos_n is null and blessure is null and niv_min is null and niv_max is null and pdv_min is null and pdv_max is null and att_min is null and att_max is null and esq_min is null and esq_max is null and deg_min is null and deg_max is null and reg_min is null and reg_max is null and arm_phy_min is null and arm_phy_max is null and arm_mag_min is null and arm_mag_max is null and vue_min is null and vue_max is null and capa_desc is null and capa_effet is null and capa_tour is null and capa_portee is null and mm_min is null and mm_max is null and rm_min is null and rm_max is null and nb_att_tour is null and vit_dep is null and vlc is null and vole is null and att_dist is null and att_mag is null and dla is null and sang_froid is null and tour_min is null and tour_max is null and chargement is null and bonus_malus is null and arm_max is null and arm_min is null;

delete FROM being_mob_private 
where (last_event_update_at is null or last_event_update_at < (CURRENT_DATE - interval '1 YEAR'))
and (last_seen_at is null or last_seen_at < (CURRENT_DATE - interval '1 YEAR'))
and (last_reconciliation_at is null or last_reconciliation_at < (CURRENT_DATE - interval '1 YEAR'))
and blessure is null and niv_min is null and niv_max is null and pdv_min is null and pdv_max is null and att_min is null and att_max is null and esq_min is null and esq_max is null and deg_min is null and deg_max is null and reg_min is null and reg_max is null and arm_phy_min is null and arm_phy_max is null and arm_mag_min is null and arm_mag_max is null and vue_min is null and vue_max is null and capa_desc is null and capa_effet is null and capa_tour is null and capa_portee is null and mm_min is null and mm_max is null and rm_min is null and rm_max is null and nb_att_tour is null and vit_dep is null and vlc is null and vole is null and att_dist is null and att_mag is null and dla is null and sang_froid is null and tour_min is null and tour_max is null and chargement is null and bonus_malus is null and arm_max is null and arm_min is null;

select case when pos_x is null then null else 'X' end has_x
, case when niv_min is null then null else 'X' end has_niv_min
, count(*) c from public.being_mob_private group by 
case when pos_x is null then null else 'X' end 
, case when niv_min is null then null else 'X' end;
-- 15/11/2025
--X	X	646114
--X		12037647
--	X	656428
--		480810

-- champi
CREATE INDEX champi_private_last_seen_at_idx ON public.champi_private (last_seen_at);

delete from public.champi_private where nom is null and last_seen_at < (CURRENT_DATE - interval '6 MONTH');

-- tresor
select count(*)  from tresor_private;
vacuum being_mob_private;
vacuum full being_mob_private;
select count(*)  from tresor_private where tresor_id=13180651 and viewer_id=99377;
delete  from tresor_private where tresor_id=13180651 and viewer_id=99377;
select count(*)  from tresor_private where metatresor_id is null and effet is null and last_seen_at < (CURRENT_DATE - interval '60 MONTH');
delete  from tresor_private where metatresor_id is null and effet is null and last_seen_at < (CURRENT_DATE - interval '6 MONTH');
-- last_seen_with, last_event_update_at, last_event_update_by, last_event_update_id, last_reconciliation_at, last_reconciliation_by FROM public.tresor_private;;
