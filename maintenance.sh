#!/bin/bash
LOGS=/sciz/logs/maintenance.log
if [ $((`date +%e`%2)) -eq 0 ];
then
	sql="select now();vacuum sciz.public.event;select now();analyse;select now();"
else
	sql="select now();vacuum sciz.public.being;select now();vacuum sciz.public.being_mob;select now();vacuum sciz.public.being_mob_meta;select now();vacuum sciz.public.being_mob_private;select now();vacuum sciz.public.being_troll;select now();vacuum sciz.public.being_troll_private;select now();vacuum sciz.public.being_troll_private_capa;select now();vacuum sciz.public.capa_meta;select now();vacuum sciz.public.champi;select now();vacuum sciz.public.champi_private;select now();vacuum sciz.public.coterie;select now();vacuum sciz.public.event_aa;select now();vacuum sciz.public.event_battle;select now();vacuum sciz.public.event_cdm;select now();vacuum sciz.public.event_champi;select now();vacuum sciz.public.event_cp;select now();vacuum sciz.public.event_follower;select now();vacuum sciz.public.event_tp;select now();vacuum sciz.public.event_tresor;select now();vacuum sciz.public.event_user;select now();vacuum sciz.public.guilde;select now();vacuum sciz.public.hook;select now();vacuum sciz.public.lieu;select now();vacuum sciz.public.lieu_piege;select now();vacuum sciz.public.lieu_portail;select now();vacuum sciz.public.maisonnee;select now();vacuum sciz.public.tresor;select now();vacuum sciz.public.tresor_meta;select now();vacuum sciz.public.tresor_private;select now();vacuum sciz.public.user;select now();vacuum sciz.public.user_mh_call;select now();vacuum sciz.public.user_partage;select now();analyse;select now();"
fi
echo $sql >> ${LOGS}
psql sciz -t <<< $sql >> ${LOGS} 2>&1
