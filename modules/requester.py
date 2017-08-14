#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Imports
import ConfigParser, sqlalchemy
from sqlalchemy import desc, or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from classes.troll import TROLL
from classes.user import USER
from classes.mob import MOB
from classes.cdm import CDM
from classes.battle_event import BATTLE_EVENT
from modules.sql_helper import SQLHelper
from modules.pretty_printer import PrettyPrinter
import modules.globals as sg

## Requester class for SCIZ
class Requester:

    # Constructor
    def __init__(self, config):
        self.config = config
        self.check_conf()
        self.sqlHelper = SQLHelper(config)
        self.pprinter = PrettyPrinter(config)
    
    # Configuration loader and checker
    def check_conf(self):
        # No conf needed yet
        pass

    # Dispatcher
    def request(self, ids, args):
        # Request on all trolls
        if ids.lower() == 'trolls':
            trolls = self.sqlHelper.session.query(TROLL).all()
            for troll in trolls:
                self.__request_troll(troll.id, args)
        # Request on all users trolls
        elif ids.lower() == 'users':
            trolls = self.sqlHelper.session.query(USER).all()
            for troll in trolls:
                self.__request_troll(troll.id, args)
        else:
            id_lst = ids.split(',')
            is_mob_lst = is_troll_lst = True
            for id in id_lst:
                is_troll_lst = is_troll_lst and (len(id) <= 6 and id.isdigit())
                is_mob_lst = is_mob_lst and (len(id) == 7 and id.isdigit())
            # Request on a specific list of mobs
            if is_mob_lst and not is_troll_lst:
                for id in id_lst:
                    self.__request_mob(id, args)
            # Request on a specific list of trolls
            elif is_troll_lst and not is_mob_lst:
                for id in id_lst:
                    self.__request_troll(id, args)
            # Request on an inconsitant list of ids
            else:
                print 'Inconsistant list of ids...'

    # Mob request
    def __request_mob(self, id, args):
        if len(args) > 0:
            limit = 1
            if len(args) > 1 and args[1].isdigit():
                limit = int(args[1])
            if args[0].lower() == 'cdm':
                self.__request_mob_cdm(id, limit)
            elif args[0].lower() == 'event':
                self.__request_mob_event(id, limit)
            else:
                caracs = args[0].split(',')
                self.__request_mob_caracs(id, caracs)
        else:
            self.__request_mob_caracs(id, None)

    def __request_mob_cdm(self, id, limit):
        try:        
            cdms = self.sqlHelper.session.query(CDM).filter(CDM.mob_id == id).order_by(desc(CDM.time)).limit(limit).all()
            for cdm in cdms:
                print self.pprinter.pretty_print(cdm, False, None)
        except NoResultFound:
            pass
    
    def __request_mob_event(self, id, limit):
        try:
            events = self.sqlHelper.session.query(BATTLE_EVENT).filter(or_(BATTLE_EVENT.att_mob_id == id, BATTLE_EVENT.def_mob_id == id)).order_by(desc(BATTLE_EVENT.time)).limit(limit).all()
            for event in events:
                print self.pprinter.pretty_print(event, False, None)
        except NoResultFound:
            pass
    
    def __request_mob_caracs(self, id, caracs):
        try:
            mob = self.sqlHelper.session.query(MOB).filter(MOB.id == id).one()
            print self.pprinter.pretty_print(mob, False, caracs)
        except NoResultFound:
            pass
    
    # Trol request        
    def __request_troll(self, id, args):
        if len(args) > 0:
            limit = 1
            if len(args) > 1 and args[1].isdigit():
                limit = int(args[1])
            if args[0].lower() == 'event':
                self.__request_troll_event(id, limit)
            else:
                caracs = args[0].split(',')
                self.__request_troll_caracs(id, caracs)
        else:
            self.__request_troll_caracs(id, None)
    
    def __request_troll_event(self, id, limit):
        try:
            events = self.sqlHelper.session.query(BATTLE_EVENT).filter(or_(BATTLE_EVENT.att_troll_id == id, BATTLE_EVENT.def_troll_id == id)).order_by(desc(BATTLE_EVENT.time)).limit(limit).all()
            for event in events:
                print self.pprinter.pretty_print(event, False, None)
        except NoResultFound:
            pass

    def __request_troll_caracs(self, id, caracs):
        try:
            troll = self.sqlHelper.session.query(TROLL).filter(TROLL.id == id).one()
            print self.pprinter.pretty_print(troll, False, caracs)
        except NoResultFound:
            pass

    # Destructor
    def __del__(self):
        pass