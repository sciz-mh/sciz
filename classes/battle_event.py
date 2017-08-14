#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Imports
import re, datetime, ConfigParser
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import modules.globals as sg

# Class of a Battle Event (ATT / DEF / POUVOIR / HYPNO / ... ???)
class BATTLE_EVENT(sg.SqlAlchemyBase):

    # SQL Table Mapping
    __tablename__ = 'battle_events'
    id = Column(Integer, primary_key=True)                  # Identifiant unique de la CDM
    time = Column(DateTime)                                 # Horodatage de l'event
    att_troll_id = Column(Integer, ForeignKey('trolls.id')) # Identifiant du Troll ayant réalisé l'evenement
    def_troll_id = Column(Integer, ForeignKey('trolls.id')) # Identifiant du Troll ayant subi l'evenement
    att_mob_id = Column(Integer, ForeignKey('mobs.id'))     # Identifiant du Monstre ayant réalisé l'évènement
    def_mob_id = Column(Integer, ForeignKey('mobs.id'))     # Identifiant du Monstre ayant subi l'évènement
    notif_id = Column(Integer, ForeignKey('notifs.id'))     # Identifiant de la notifiction
    flag_type = Column(String(50))                          # FLAG (ATT, DEF, HYPNO...)
    type = Column(String(50))                               # Type d'évènement
    subtype = Column(String(50))                            # Sous type d'évènement
    att = Column(Integer)                                   # Jet d'attaque
    esq = Column(Integer)                                   # Jet d'esquive
    deg = Column(Integer)                                   # Jet de dégâts
    pv = Column(Integer)                                    # Points de vie perdu (avec armure)
    sr = Column(Integer)                                    # Seuil de résistance en %
    resi = Column(Integer)                                  # Jet de résistance en %
    capa_desc = Column (String(150))                        # Descritpion de la capacité spéciale
    capa_effet = Column (String(150))                       # Effet de la capacité spéciale
    capa_tour = Column (Integer)                            # Nombre de tours d'effet de la capacité spéciale

    # Relationships
    att_troll = relationship("TROLL", foreign_keys=[att_troll_id], back_populates="att_events")
    def_troll = relationship("TROLL", foreign_keys=[def_troll_id], back_populates="def_events")
    att_mob = relationship("MOB", foreign_keys=[att_mob_id], back_populates="att_events")
    def_mob = relationship("MOB", foreign_keys=[def_mob_id], back_populates="def_events")
    notif = relationship("NOTIF")

    # Constructor
    # Handled by SqlAlchemy, accept keywords names matching the mapped columns, do not override
    
    # Populate object from a mail and the dedicated regexp in the configuration file
    def populate_from_mail(self, subject, body, config, flag_type):
        
        # Load the regexp
        try:
            re_event_troll = config.get(sg.CONF_MAIL_SECTION, sg.CONF_EVENT_TROLL_RE)
            re_event_type = config.get(sg.CONF_MAIL_SECTION, sg.CONF_EVENT_TYPE_RE)
            re_event_time = config.get(sg.CONF_MAIL_SECTION, sg.CONF_EVENT_TIME_RE)
        except ConfigParser.Error as e:
            print("Fail to load config! (ConfigParser error:" + str(e) + ")")
            raise

        # FLAG
        self.flag_type = flag_type
        # Event Troll
        res = re.search(re_event_troll, body)
        if flag_type == 'ATT' or flag_type == 'HYPNO':
            self.att_troll_id = res.group(1)
            self.att_troll_nom = res.group(2)
        elif flag_type == 'DEF':
            self.def_troll_id = res.group(1)
            self.def_troll_nom = res.group(2)
        # Event time
        res = re.search(re_event_time, body)
        self.time = datetime.datetime.strptime(res.group(1), '%d/%m/%Y  %H:%M:%S')
        
        if flag_type == 'ATT':
            self.__populate_from_att_mail(subject, body, config)
        elif flag_type == 'DEF':
            self.__populate_from_def_mail(subject, body, config)
        elif flag_type == 'HYPNO':
            self.__populate_from_hypno_mail(subject, body, config)
        else:
            pass # Should never happen

    def __populate_from_att_mail(self, subject, body, config):   
        # Load config
        try:
            re_event_desc = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_DESC_RE)
            re_event_att = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_ATT_RE)
            re_event_esq = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_ESQ_RE)
            re_event_deg = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_DEG_RE)
            re_event_pv = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_PV_RE)
            re_event_sr = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_SR_RE)
            re_event_resi = config.get(sg.CONF_ATT_SECTION, sg.CONF_EVENT_RESI_RE)
        except ConfigParser.Error as e:
            print("Fail to load config! (ConfigParser error:" + str(e) + ")")
            raise
        # Event desc
        res = re.search(re_event_desc, subject)
        self.type = res.group(2)
        self.subtype = res.group(3)
        if res.group(4) == None: # Trick matching the det (only mobs have it)
            self.def_troll_nom = res.group(5)
            self.def_troll_id = res.group(10)
        else:
            self.def_mob_nom = res.group(5)
            self.def_mob_age = res.group(7)
            self.def_mob_tag = res.group(9)
            self.def_mob_id = res.group(10)
        # Jet d'attaque
        res = re.search(re_event_att, body)
        self.att = res.group(1) if res else None
        # Jet d'esquive
        res = re.search(re_event_esq, body)
        self.esq = res.group(1) if res else None
        # Seuil de résistance
        res = re.search(re_event_sr, body)
        self.sr = res.group(1) if res else None
        # Jet de résistance
        res = re.search(re_event_resi, body)
        self.resi = res.group(1) if res else None
        # Jet de dégâts
        res = re.search(re_event_deg, body)
        self.deg = res.group(1) if res else None
        # Points de vie perdus
        res = re.search(re_event_pv, body)
        self.pv = res.group(1) if res else self.deg # Pas d'armure
    
    def __populate_from_def_mail(self, subject, body, config):       
        # Load config
        try:
            re_event_desc = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_DESC_RE)
            re_event_att = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_ATT_RE)
            re_event_esq = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_ESQ_RE)
            re_event_deg = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_DEG_RE)
            re_event_pv = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_PV_RE)
            re_event_vie = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_VIE_RE)
            re_event_capa = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_CAPA_RE)
            re_event_capa_effet = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_CAPA_EFFET_RE)
            re_event_capa_tour = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_CAPA_TOUR_RE)
            re_event_sr = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_SR_RE)
            re_event_resi = config.get(sg.CONF_DEF_SECTION, sg.CONF_EVENT_RESI_RE)
        except ConfigParser.Error as e:
            print("Fail to load config! (ConfigParser error:" + str(e) + ")")
            raise
        # Event desc
        res = re.search(re_event_desc, subject)
        self.type = res.group(2)
        if res.group(3) == 'de': # Trick matching the det
            self.att_troll_nom = res.group(4)
            self.att_troll_id = res.group(9)
        else:
            self.att_mob_nom = res.group(4)
            self.att_mob_age = res.group(6)
            self.att_mob_tag = res.group(8)
            self.att_mob_id = res.group(9)
        # Jet d'attaque
        res = re.search(re_event_att, body)
        self.att = res.group(1) if res else None
        # Jet d'esquive
        res = re.search(re_event_esq, body)
        self.esq = res.group(1) if res else None
        # Seuil de résistance
        res = re.search(re_event_sr, body)
        self.sr = res.group(1) if res else None
        # Jet de résistance
        res = re.search(re_event_resi, body)
        self.resi = res.group(1) if res else None
        # Jet de dégâts
        res = re.search(re_event_deg, body)
        self.deg = res.group(1) if res else None
        # Points de vie perdus
        res = re.search(re_event_pv, body)
        self.pv = res.group(1) if res else self.deg # Pas d'armure
        # Points de vie restants
        res = re.search(re_event_vie, body)
        self.vie = res.group(1) if res else None
        # Capa desc
        res = re.search(re_event_capa, body)
        self.capa = res.group(1) if res else None
        # Capa effet
        res = re.search(re_event_capa_effet, body)
        self.capa_effet = res.group(1) if res else None
        # Capa tour
        res = re.search(re_event_capa_tour, body)
        self.capa_tour = res.group(1) if res else None
        
    def __populate_from_hypno_mail(self, subject, body, config):       
        # Load config
        try:
            re_event_desc = config.get(sg.CONF_HYPNO_SECTION, sg.CONF_EVENT_DESC_RE)
            re_event_sr = config.get(sg.CONF_HYPNO_SECTION, sg.CONF_EVENT_SR_RE)
            re_event_resi = config.get(sg.CONF_HYPNO_SECTION, sg.CONF_EVENT_RESI_RE)
        except ConfigParser.Error as e:
            print("Fail to load config! (ConfigParser error:" + str(e) + ")")
            raise
        # Event desc
        res = re.search(re_event_desc, body)
        self.type = 'Sortilège'
        self.subtype = res.group(1)
        if res.group(2) == None: # Trick matching the det (No det = Troll ?)
            self.def_troll_nom = res.group(3)
            self.def_troll_id = res.group(8)
        else:
            self.def_mob_nom = res.group(3)
            self.def_mob_age = res.group(5)
            self.def_mob_tag = res.group(7)
            self.def_mob_id = res.group(8)
        # Seuil de résistance
        res = re.search(re_event_sr, body)
        self.sr = res.group(1) if res else None
        # Jet de résistance
        res = re.search(re_event_resi, body)
        self.resi = res.group(1) if res else None

    def stringify(self):
        self.s_flag_type = self.flag_type
        # Attaquant
        if self.att_troll:
            self.s_att_nom = self.att_troll.nom + ' (' + str(self.att_troll.id) + ')'
            if self.att_troll.user:
                self.s_att_nom = self.att_troll.user.pseudo + ' (' + str(self.att_troll.id) + ')'
        else:
            self.s_att_nom = self.att_mob.nom + ' [' + self.att_mob.age + '] (' + str(self.att_mob.id) + ')'
        # Défenseur
        if self.def_troll:
            self.s_def_nom = self.def_troll.nom + ' (' + str(self.def_troll.id) + ')'
            if self.def_troll.user:
                self.s_def_nom = self.def_troll.user.pseudo + ' (' + str(self.def_troll.id) + ')'
        else:
            self.s_def_nom = self.def_mob.nom + ' [' + self.def_mob.age + '] (' + str(self.def_mob.id) + ')'
        # Stats
        self.s_pv = '-' + str(self.pv) if (self.pv != None) and (self.pv != 0) else ''
        self.s_def_stats = ''
        self.s_def_stats += ' esq ' + str(self.esq) if self.esq else ''
        self.s_def_stats += ' sr ' + str(self.sr) if self.sr else ''
        self.s_att_stats = ''
        self.s_att_stats += ' att ' + str(self.att) if self.att else ''
        self.s_att_stats += ' deg ' + str(self.deg) if self.deg else ''
        # Type desc
        self.s_type_short = ''
        self.s_type = ''
        if self.flag_type == 'ATT' or self.flag_type == 'DEF':
            self.s_type_short = ' (' + self.type + ')' if self.type != 'Attaque' else '' # N'afficher que si critique, réduit, esquivé, mortelle, etc.)
            self.s_type = self.type if self.type else ''
            self.s_type += ' ' + self.subtype if self.subtype else ''
            self.s_type = ' (' + self.s_type + ')' if self.s_type != '' else ''
        elif self.flag_type == 'HYPNO':
            if self.resi > self.sr:
                self.s_type_short = '(FULL)'
            else:
                self.s_type_short = '(REDUIT)'