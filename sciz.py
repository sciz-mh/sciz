#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTS
from classes.coterie_hook import Hook
from web.server import webapp as application
from modules.admin_helper import AdminHelper
from modules.requester import Requester
from modules.sql_helper import SqlHelper
from modules.notifier import Notifier
from modules.mh_caller import MhCaller
from classes.user import User
from classes.lieu_portail import Portail
from classes.lieu_piege import Piege
from classes.coterie import Coterie
from logging.handlers import RotatingFileHandler
from modules.mail_parser import MailParser
from modules.mail_helper import MailHelper
import email, mailbox, datetime
import sys, os, argparse, codecs, logging, traceback, yaml, re
import modules.globals as sg


# CLASS DEFINITION
class SCIZ:

    # Constructor
    def __init__(self, conf_file, logging_level):

        # Load the default conf
        with codecs.open(conf_file, 'r', sg.DEFAULT_CHARSET) as fp:
            sg.conf = yaml.safe_load(fp)

        # Load the regexs
        regex_file = os.path.dirname(conf_file) + os.sep + sg.conf[sg.CONF_INSTANCE_SECTION][sg.CONF_INSTANCE_REGEX_FILE]
        with codecs.open(regex_file, 'r', sg.DEFAULT_CHARSET) as fp:
            sg.regex = yaml.safe_load(fp)

        # Load the default format
        format_file = os.path.dirname(conf_file) + os.sep + sg.conf[sg.CONF_INSTANCE_SECTION][sg.CONF_INSTANCE_FORMAT_FILE]
        with codecs.open(format_file, 'r', sg.DEFAULT_CHARSET) as fp:
            sg.format = yaml.safe_load(fp)

        # Load the formulas
        format_file = os.path.dirname(conf_file) + os.sep + sg.conf[sg.CONF_INSTANCE_SECTION][sg.CONF_INSTANCE_FORMULA_FILE]
        with codecs.open(format_file, 'r', sg.DEFAULT_CHARSET) as fp:
            sg.formulas = yaml.safe_load(fp)

        # Set up the loggers and store them globally
        logger_file = sg.conf[sg.CONF_LOG_SECTION][sg.CONF_LOG_FILE]
        logger_file_max_size = sg.conf[sg.CONF_LOG_SECTION][sg.CONF_LOG_FILE_MAX_SIZE]
        logger_formatter = sg.conf[sg.CONF_LOG_SECTION][sg.CONF_LOG_FORMATTER]
        formatter = logging.Formatter(logger_formatter)
        sg.createDirName(logger_file)
        files = [('sciz', logger_file)]
        res = re.search(r'(.+)\.log', logger_file)
        if res is not None:
            for logger_name in ['walker', 'updater', 'server', 'cleaner']:
                files.append((logger_name, res.group(1) + '_' + logger_name + '.log'))
        for logger_name, file in files:
            log_file = RotatingFileHandler(file, 'a', logger_file_max_size, 1)
            log_file.setLevel(logging_level)
            log_file.setFormatter(formatter)
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging_level)
            logger.addHandler(log_file)
        sg.logger = logging.getLogger('sciz')

        # Set up the database connection and store it globally
        try:
            sg.db = SqlHelper('sciz' + sys.argv[1])
        except Exception as e:
            sg.db = SqlHelper('scizweb')

        # Set up the admin helper and store it globally
        print('init Admin')
        sg.ah = AdminHelper()

        # Set up the requester and store it globally
        print('init Requester')
        sg.req = Requester()

        # Set up the notifier and store it globally
        print('init Notifier')
        sg.no = Notifier()

        # Set up the mh caller and store it globally
        print('init MhCaller')
        sg.mc = MhCaller()

    # Test
    def test(self):
        ### Reset formats
        #hooks = sg.db.session.query(Hook).all()
        #for hook in hooks:
        #    hook.format = sg.format
        #    sg.db.upsert(hook)
        ### Fix mh_api_keys with whitespaces
        #users = sg.db.session.query(User).all()
        #for user in users:
        #    user.mh_api_key = user.mh_api_key.strip() if user.mh_api_key is not None else user.mh_api_key
        #    sg.db.upsert(user)
        ### Create a test user
        #user = User(id=1, pwd_hash='test', mh_api_key='TEST')
        #sg.db.upsert(user)
	###
        #portals = sg.db.session.query(Portail).all()
        #for p in portals:
        #    p.type = 'Portail'
        #    sg.db.upsert(p)
        ###
        #hook = sg.db.session.query(Hook).get(4049)
        #hook.trigger()
        
        ### time to get coterie 10 last events
        #coterie = sg.db.session.query(Coterie).get(705)
        #print(coterie.__class__.__name__)
        #l = coterie.get_events(50, 0, 0, False)
        #for e in l:
        #    print(e['event']['owner_id'], e['event']['time'])
            
        ### reproduce/fix issue when there is an empty file in maildir
        #print('test mailbox')
        #mbox = mailbox.Maildir('/sciz/logs/badmailbox', create=True)
        #mails = mbox.items()
        #print(mails)
        #for mail in mails:
        #    if mail[1].get('Date') is None:
        #        print('bad ' + mail[0])
        #        # not safe to remove while iterating !!!!!!
        #        mails.remove(mail)
        #sorted_mbox = sorted(mails, key=lambda x: email.utils.parsedate(x[1].get('Date')))

        #print('test session using "with"')
        #try:
        #    with sg.db.sessionMaker() as session:
        #        sql = """ select max_mh_sp_static from public.user where id= %(_id)s """
        #        params = {'_id': 91305}
        #        r = session.execute(sql % params)
        #        l = list(r)
        #        print('before', l[0][0])
        #        sql = """ update public.user set max_mh_sp_static=5 where id=%(_id)s """
        #        session.execute(sql % params)
        #        sql = """ select max_mh_sp_static from public.user where id= %(_id)s """
        #        r = session.execute(sql % params)
        #        l = list(r)
        #        print('after', l[0][0])
        #        # sql error to test auto rollback
        #        sql = """ select max_mh_sp_staticx from public.user where id= %(_id)s """
        #        #r = session.execute(sql % params)
        #        #session.commit()
        #except Exception as e:
        #    print(e)

        print('analyse pb mail')
        from operator import itemgetter
        self.mp = MailParser()
        self.re_time = re.compile('Il était alors (aux alentours de )?: (?P<time>.*)\.')
        self.re_vie = re.compile('(reste actuellement|avez maintenant)\s+(?P<vie>\d+)\s+(p|P)oints? de (v|V)ie')
        mbox = mailbox.Maildir("/tmp/mail.pb", create=True)
        # Build a sorted list of key-message by 'Date' header #RFC822
        sorted_mbox = sorted(mbox.iteritems(), key=lambda x: email.utils.parsedate(x[1].get('Date')))
        # Then get the actuals mails
        for item in sorted_mbox:
            #print(mbox.get_file(item[0])._file.name)
            try:
                s = mbox.get_string(item[0])
                #print(email.message_from_string(s))
                #print('OK')
            except Exception as e:
                print('execption', e, mbox.get_file(item[0])._file.name)

        print('end of test')
        pass


# MAIN
if __name__ == '__main__':

    print('process args')
    # Command line arguments handling
    parser = argparse.ArgumentParser(
            description='Système de Chauve-souris Interdimensionnel pour Zhumains',
            epilog='From Põm³ with love')

    parser.add_argument('-c', '--conf',
            metavar='CONFIG_FILE', type=str, default='confs/sciz_main.yaml',
            help='specify the .yaml configuration file')

    parser.add_argument('-l', '--logging-level',
            metavar='LOGGING_LEVEL', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='specify the level of logging')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--init',
            action='store_true',
            help='instruct SCIZ to setup the things like database structure and painting')

    group.add_argument('-w', '--walker',
            nargs='?', const=True, default=None,
            metavar='USER_ID',
            help='instruct SCIZ to start the mail walker, auto-magical-indefinitely or once for a specified user')

    group.add_argument('-u', '--updater',
            nargs='?', const=True, default=None,
            metavar='USER_ID',
            help='instruct SCIZ to start the MH updater, auto-magical-indefinitely or once for a specified user')

    group.add_argument('-s', '--server',
            nargs='?', const=True, default=None,
            help='instruct SCIZ to start the web server')

    group.add_argument('-v', '--vacuum',
            nargs='?', const=True, default=None,
            help='instruct SCIZ to start the vacuum cleaner')

    group.add_argument('-t', '--test',
            action='store_true',
            help='do a test you wrote')

    parser.add_argument('rargs', nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    args = parser.parse_args()

    # SCIZ startup
    sg.sciz = None
    try:
        sg.sciz = SCIZ(args.conf, args.logging_level)
        sg.logger.info('The bats woke up!')
        if any(arg not in [None, False, True] for arg in [args.walker, args.updater]):
            sg.user = sg.db.session.query(User).get(args.walker or args.updater)
            if sg.user is None:
                sg.logger.error('The specified user %s does not exist...' % (args.walker or args.updater))
                sys.exit(1)
        if args.init is not None and args.init:
            sg.logger.info('Initializing...')
            sg.ah.init()
        elif args.walker is not None:
            sg.logger.info('Starting the walker...')
            print('Creating the walker')
            sg.logger = logging.getLogger('walker')
            print('Starting the walker')
            sg.ah.walk()
        elif args.updater is not None:
            sg.logger.info('Starting the updater...')
            sg.logger = logging.getLogger('updater')
            sg.ah.update(args.rargs)
        elif args.server is not None:
            sg.logger.info('Starting the web server...')
            sg.logger = logging.getLogger('server')
            web_port = sg.conf[sg.CONF_WEB_SECTION][sg.CONF_WEB_PORT]
            web_domain = sg.conf[sg.CONF_WEB_SECTION][sg.CONF_WEB_DOMAIN]
            application.run(host=web_domain, port=web_port)
        elif args.vacuum is not None:
            sg.logger.info('Starting the vacuum cleaner...')
            sg.logger = logging.getLogger('cleaner')
            sg.ah.vacuum()
        elif args.test is not None:
            sg.logger.info('Testing SCIZ...')
            sg.sciz.test()
        else:
            parser.print_help()
    except Exception as e:
        print('The bats went sick. Check the log file?', file=sys.stderr)
        if sg.logger is not None:
            sg.logger.exception(e)
        traceback.print_exc()
        sys.exit(1)
    sg.logger.info('Nothing else to do. Bats went to sleep.')
