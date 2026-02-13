#!/usr/bin/env python3
#coding: utf-8

# needs "export PYTHONPATH=/sciz"

# IMPORTS
from modules.sql_helper import SqlHelper
import modules.globals as sg
from modules.requester import Requester
from modules.notifier import Notifier
from classes.coterie import Coterie
from classes.coterie_hook import Hook
from sqlalchemy import sql
import jwt

import sys, asyncio, aiohttp, json, re, yaml, codecs, datetime, traceback
from discord import Game, Intents
from discord.ext.tasks import loop
from discord.ext.commands import Bot

# CONSTS
DEFAULT_CHARSET = 'utf-8'
SCIZ_URL_BASE = 'https://newv6.sciz.fr/api/hook'
#SCIZ_URL_BASE = 'https://sciz.brion.fr/api/hook'
#SCIZ_URL_BASE = 'http://127.0.0.1/api/hook'
#SCIZ_URL_BASE = 'http://localhost/api/hook'
SCIZ_URL_EVENTS = SCIZ_URL_BASE + '/events'
SCIZ_URL_REQUEST = SCIZ_URL_BASE + '/request'
SCIZ_INTERVAL = 5
CONF_FILE = 'sciz_discord.yaml'
CONF_SCIZ = '../../confs/sciz_main.yaml'
CONF_DISCORD_SECTION = 'discord'
CONF_DISCORD_TOKEN = 'token'
CONF_DISCORD_PREFIX = 'prefix'
CONF_REDIS_HOST = 'host'
CONF_REDIS_PORT = 'port'
CONF_REDIS_DB = 'db'

class ScizBot(Bot):
    async def setup_hook(self):
        self.sciz_task = asyncio.create_task(
            _sciz_fetch_events(SCIZ_URL_EVENTS, SCIZ_INTERVAL)
        )

# MAIN
if __name__ == '__main__':
    # load config
    with codecs.open(CONF_FILE, 'r', DEFAULT_CHARSET) as fp:
        conf = yaml.safe_load(fp)
        sg.confDiscord = conf
    #print(conf)
    conf_discord = conf[CONF_DISCORD_SECTION]
    #conf_redis = conf[CONF_REDIS_SECTION]
    with codecs.open(CONF_SCIZ, 'r', DEFAULT_CHARSET) as fp:
        sg.conf = yaml.safe_load(fp)
    #print(conf_discord)
    #print(conf_redis)
    #exit()

    # Requester
    sg.req = Requester()

    # Notifier
    sg.no = Notifier()

    # DB
    sg.db = SqlHelper('botDiscord')

    # Create the bot
    intents = Intents.default()
    intents.message_content = True
    bot = ScizBot(
        command_prefix=conf_discord[CONF_DISCORD_PREFIX],
        intents=intents
    )

    # Define bot events
    @bot.event
    async def on_ready():
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' waiting for login ready...', flush=True)
        await bot.change_presence(activity=Game(name='Mountyhall'))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' Logged in as ' + bot.user.name, flush=True)

    # Define bot commands
    @bot.command(name='sciz', pass_context=True)
    async def _sciz_request(ctx, *args):
        # Get useful things
        args = ' '.join(args).strip()
        channel_id = ctx.message.channel.id
        #print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' command from discord ' + args, flush=True)
        # Handle ping
        if args == 'ping':
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' command PROCESSED from discord ' + args, flush=True)
            await ctx.send('pongV2')
            return
        # Handle unregister
        if args == 'unregister':
            #r.delete(channel_id)
            sqlu = "update hook set channel_id=null where channel_id=:c_id and type='Discord'"
            params = {'c_id': str(channel_id)}
            #print(params)
            res = sg.db.session.execute(sql.text(sqlu), params)
            sg.db.session.commit()
            if res.rowcount > 0:
                await ctx.send('HookV2 supprimé pour ce canal')
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' suppression channel', channel_id, flush=True);
            else:
                await ctx.send("Échec à la suppression du HookV2 (inexistant ?)")
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Échec à la suppression du Hook (mauvais code ?)", channel_id, flush=True);
            return
        # Handle register
        m = re.search('register (.*)', args)
        if m is not None:
            # decode jwt and check signature ('verify_sub': False because it must be a string and it is a number in our jwt)
            payload = jwt.decode(str(m.group(1)), sg.conf[sg.CONF_WEB_SECTION][sg.CONF_WEB_SECRET], algorithms=['HS256', 'RS256'], options={'verify_sub': False})
            #print(payload)
            hook_id = payload['identity']

            sqlu = "update hook set channel_id=:c_id where id=:h_id and type='Discord'"
            params = {'c_id':str(channel_id), 'h_id': hook_id}
            #print(params)
            #print(sqlu)
            res = sg.db.session.execute(sql.text(sqlu), params)
            sg.db.session.commit()
            if res.rowcount > 0:
                await ctx.send('Hook V2 enregistré pour le canal')
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") +  ' Hook V2 enregistré pour le canal ' + str(channel_id) + ', hook.id=' + str(hook_id), flush=True)
            else:
                await ctx.send("Échec à l'enregistrement du Hook (mauvais code ?)")
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Échec à l'enregistrement du Hook (mauvais code ?)", channel_id, flush=True);
            return
        # Handle request
        try:
            hooks = sg.db.session.query(Hook).filter(Hook.channel_id == str(channel_id))
            if hooks is None or hooks.count() == 0:
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' Pas de hook enregistré pour canal ' + str(channel_id) + ', cmde=' + args)
                await ctx.send('Pas de hook enregistré pour ce canal')
                return
            for hook in hooks:
                if hook.coterie is None:
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' Pas de coterie associée au hook ' + str(channel_id) + ', hook.id=' + str(hook.id))
                    continue
                res = sg.req.request(hook.coterie, args)
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " cmde " + str(args) + "=>" + str(res))
                await ctx.send(res)
            pass
        except Exception as e:
            print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_request', file=sys.stderr, flush=True)
            print(e, file=sys.stderr, flush=True)
            traceback.print_exc()
            await ctx.send('Erreur au traitement de la commande ' + args)

    # Define bot routine (SCIZ events)
    async def _sciz_fetch_events(url, interval):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' waiting for bot ready...', flush=True)
        await bot.wait_until_ready()
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' got bot ready...', flush=True)
        while True:
            await asyncio.sleep(1)
            try:
                hooks = sg.db.session.query(Hook).filter(Hook.channel_id != None, Hook.type == 'Discord')
                #print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' après liste hooks, n=' + str(hooks.count()))
                for hook in hooks:
                    #print('coterie_id=' + str(hook.coterie_id) + ', channel_id=' + hook.channel_id)
                    coterie = sg.db.session.get(Coterie, hook.coterie_id)
                    if coterie is not None: # and coterie.has_partage(get_jwt_identity(), False):
                        #print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' coterie ' + str(hook.coterie_id) + ', hook id=' + str(hook.id) + ', avant trigger')
                        events = hook.trigger()
                        #print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' coterie ' + str(hook.coterie_id) + ', hook id=' + str(hook.id) + ', après trigger')
                        if events is not None and len(events) > 0:
                            channel = bot.get_channel(int(hook.channel_id))
                            if channel:
                                for event in events:
                                    await channel.send(event['message'])
                                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' coterie ' + str(hook.coterie_id) + ', ' + str(len(events)) + ' messages')
                            else:
                                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' incohérence sur le channel ' + str(hook.channel_id))
                    else:
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' incohérence sur la coterie ' + str(hook.coterie_id))
            except Exception as e:
                print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_fetch_events', file=sys.stderr)
                traceback.print_exc()
                print('', file=sys.stderr, flush=True)
            await asyncio.sleep(interval-1)

    # Start the bot
    try:
        bot.run(conf_discord[CONF_DISCORD_TOKEN])
    except Exception as e:
        print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash')
        print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash', file=sys.stderr)
        print(e, file=sys.stderr, flush=True)
        print(e, flush=True)

