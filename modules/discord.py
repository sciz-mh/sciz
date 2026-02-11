#! /usr/bin/env python3
#coding: utf-8

# IMPORTS
import modules.globals as sg
import sys, asyncio, aiohttp, json, redis, re, yaml, codecs, datetime, traceback
from discord import Game, Intents
from discord.ext.tasks import loop
from discord.ext.commands import Bot
from classes.coterie_hook import Hook
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt, get_jwt_identity

# CONSTS
DEFAULT_CHARSET = 'utf-8'
SCIZ_URL_BASE = 'https://newv6.sciz.fr/api/hook'
#SCIZ_URL_BASE = 'https://sciz.brion.fr/api/hook'
#SCIZ_URL_BASE = 'http://127.0.0.1/api/hook'
#SCIZ_URL_BASE = 'http://localhost/api/hook'
SCIZ_URL_EVENTS = SCIZ_URL_BASE + '/events'
SCIZ_URL_REQUEST = SCIZ_URL_BASE + '/request'
SCIZ_INTERVAL = 5
CONF_FILE = 'bots/discord/sciz_discord.yaml'
#CONF_SCIZ = '../../confs/sciz_main.yaml'
CONF_DISCORD_SECTION = 'discord'
CONF_DISCORD_TOKEN = 'token'
CONF_DISCORD_PREFIX = 'prefix'
CONF_REDIS_SECTION = 'redis'
CONF_REDIS_HOST = 'host'
CONF_REDIS_PORT = 'port'
CONF_REDIS_DB = 'db'

class ScizBot(Bot):
    def initDiscord(self, discord):
        self.discord = discord

    async def setup_hook(self):
        self.sciz_task = asyncio.create_task(
            _sciz_fetch_events(SCIZ_URL_EVENTS, SCIZ_INTERVAL)
        )

class Discord:
    # Constructor
    def __init__(self):
        with codecs.open(CONF_FILE, 'r', DEFAULT_CHARSET) as fp:
            conf = yaml.safe_load(fp)
        #print(conf)
        self.conf_discord = conf[CONF_DISCORD_SECTION]
        self.conf_redis = conf[CONF_REDIS_SECTION]

    def run(self):
        # Connect to REDIS
        self.r = redis.Redis(host=self.conf_redis[CONF_REDIS_HOST], port=self.conf_redis[CONF_REDIS_PORT], db=self.conf_redis[CONF_REDIS_DB])

        # Create the bot
        #bot = Bot(command_prefix=DISCORD_PREFIX, intents=Intents.all())
        #bot = Bot(command_prefix=conf_discord[CONF_DISCORD_PREFIX])
        intents = Intents.default()
        intents.message_content = True

        sg.discordBot = ScizBot(
            command_prefix=self.conf_discord[CONF_DISCORD_PREFIX],
            intents=intents
        )
        sg.discordBot.initDiscord(self)

        # Start the bot
        #task = bot.loop.create_task(_sciz_fetch_events(SCIZ_URL_EVENTS, SCIZ_INTERVAL))
        print('Discord.run start')
        sg.logger.info('Discord.run start')
        try:
            sg.discordBot.run(self.conf_discord[CONF_DISCORD_TOKEN])
        except Exception as e:
            print('*** Discord.run ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash')
            print('*** Discord.run ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash', file=sys.stderr)
            print(e, file=sys.stderr, flush=True)
            print(e, flush=True)
            #task.cancel()


        # Define bot events
        @sg.discordBot.event
        async def on_ready():
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' waiting for discord login...', flush=True)
            await sg.discordBot.change_presence(activity=Game(name='Mountyhall'))
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' Logged in as ' + sg.discordBot.user.name, flush=True)

        # Define bot commands
        @sg.discordBot.command(name='sciz', pass_context=True)
        async def _sciz_request(self, ctx, *args):
            # Get useful things
            args = ' '.join(args).strip()
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' command from discord ' + args, flush=True)
            channel_id = ctx.message.channel.id
            #jwt = self.r.get(channel_id)
            # Handle ping
            if args == 'ping':
                await ctx.send('pongV2')
                return
            # Handle unregister
            if args == 'unregister':
                self.r.delete(channel_id)
                self.r.save()
                await ctx.send('Hook supprimé pour ce canal')
                return
            # Handle register
            m = re.search('register (.*)', args)
            if m is not None:
                #self.r.set(channel_id, m.group(1))
                #self.r.save()
                sql = """ update hook set channel_id='%(_id)s' where jwt='%(_jwt)s' and type='Discord'"""
                params = {'_id': channel_id.decode(), '_jwt':  m.group(1)}
                #print(params)
                res = sg.db.session.execute(sql % params)
                if res > 0:
                    await ctx.send('Hook enregistré pour ce canal')
                    print('Hook enregistré', channel_id, flush=True)
                else:
                    await ctx.send("Échec à l'enregistrement, jwt inconnu")
                    print("Échec à l'enregistrement, jwt inconnu", channel_id, m.group(1), flush=True)
                return
            # Handle no JWT
            if jwt is None:
                await ctx.send('Pas de hook enregistré pour ce canal')
                return
            # Handle request
            try:
                async with aiohttp.ClientSession(headers = {'Authorization': jwt.decode(DEFAULT_CHARSET)}) as session:
                    raw_response = await session.post(SCIZ_URL_REQUEST, json={'req': args})
                    if raw_response.status == 200:
                        response = await raw_response.text()
                        response = json.loads(response)
                        if 'message' in response:
                            i, l = 0, len(response['message'])
                            for m in response['message']:
                                if i < l - 1:
                                    m += "\n-\n"
                                message = ''
                                for part in m.split('\n'):
                                    if len(message) + len(part) > 2000:
                                        await ctx.send(message)
                                        message = part
                                    else:
                                        message += '\n' + part
                                if message != '':
                                    await ctx.send(message)
                                i += 1
                    raw_response.release()
            except Exception as e:
                print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_request', file=sys.stderr, flush=True)
                print(e, file=sys.stderr, flush=True)
                pass

# Define bot routine (SCIZ events)
async def _sciz_fetch_events(url, interval):
    sg.logger.info('Discord._sciz_fetch_events waiting bot ready')
    await sg.discordBot.wait_until_ready()
    sg.logger.info('Discord._sciz_fetch_events got bot ready')
    while True:
        await asyncio.sleep(interval)
        #try:
        #    hook = sg.db.session.query(Hook).get(get_jwt_identity())
        #    if hook is not None:
        #        #return jsonify(events=hook.trigger()), 200
        #        for evt in hooks:
        #            if 'message' in evt:
        #                channel = sg.discordBot.get_channel(int(channel_id))
        #                if channel:
        #                    ret = await channel.send(evt['message'])
        #                    if jwt.decode(DEFAULT_CHARSET) == 'xx' + 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTc4OTMxNDIsIm5iZiI6MTYxNzg5MzE0MiwianRpIjoiNzdmZDFjNmQtNGFkNS00ZDUyLThiYzMtYzI0YjZmYjJlZTM5IiwiaWRlbnRpdHkiOjkyNywiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIiwidXNlcl9jbGFpbXMiOnsiaG9va190eXBlIjoiSE9PSyIsImlkIjo5MjcsInR5cGUiOiJEaXNjb3JkIn19.ZTLMS9uT_kqARvF0yEYBIhAzb5YKxvw81WXhiosKld4': # discord cotterie Beromont
        #                        print(ret, flush=True);
        #                        print('_sciz_fetch_events', evt['message'], flush=True)
        #                else:
        #                    sg.looger.info('*** _sciz_fetch_events no channel ' + evt['message'])
        #                    print('*** _sciz_fetch_events no channel ', jwt, evt['message'], flush=True)
        #                    pass
        #except Exception as e:
        #    sg.logger.info('exception in _sciz_fetch_events')
        #    sg.logger.exception(e)
        #    print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_fetch_events, url=' + url, flush=True)


