#!/usr/bin/env python3
#coding: utf-8

# IMPORTS
import sys, asyncio, aiohttp, json, redis, re, yaml, codecs, datetime, traceback
from discord import Game, Intents
from discord.ext.tasks import loop
from discord.ext.commands import Bot

# CONSTS
DEFAULT_CHARSET = 'utf-8'
SCIZ_URL_BASE = 'https://www.sciz.fr/api/hook'
#SCIZ_URL_BASE = 'http://127.0.0.1:8080/api/hook'
SCIZ_URL_EVENTS = SCIZ_URL_BASE + '/events'
SCIZ_URL_REQUEST = SCIZ_URL_BASE + '/request'
SCIZ_INTERVAL = 5
CONF_FILE = 'sciz_discord.yaml'
CONF_DISCORD_SECTION = 'discord'
CONF_DISCORD_TOKEN = 'token'
CONF_DISCORD_PREFIX = 'prefix'
CONF_REDIS_SECTION = 'redis'
CONF_REDIS_HOST = 'host'
CONF_REDIS_PORT = 'port'
CONF_REDIS_DB = 'db'

# MAIN
if __name__ == '__main__':
    # load config
    with codecs.open(CONF_FILE, 'r', DEFAULT_CHARSET) as fp:
        conf = yaml.safe_load(fp)
    #print(conf)
    conf_discord = conf[CONF_DISCORD_SECTION]
    conf_redis = conf[CONF_REDIS_SECTION]
    #print(conf_discord)
    #print(conf_redis)
    #exit()

    # Connect to REDIS
    r = redis.Redis(host=conf_redis[CONF_REDIS_HOST], port=conf_redis[CONF_REDIS_PORT], db=conf_redis[CONF_REDIS_DB])

    # Create the bot
    #bot = Bot(command_prefix=DISCORD_PREFIX, intents=Intents.all())
    bot = Bot(command_prefix=conf_discord[CONF_DISCORD_PREFIX])

    # Define bot events
    @bot.event
    async def on_ready():
        await bot.change_presence(activity=Game(name='Mountyhall'))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' Logged in as ' + bot.user.name, flush=True)

    # Define bot commands
    @bot.command(name='sciz', pass_context=True)
    async def _sciz_request(ctx, *args):
	# Get useful things
        args = ' '.join(args).strip()
        channel_id = ctx.message.channel.id
        jwt = r.get(channel_id)
	# Handle ping
        if args == 'ping':
            await ctx.send('pong')
            return
        # Handle unregister
        if args == 'unregister':
            r.delete(channel_id)
            r.save()
            await ctx.send('Hook supprimé pour ce canal')
            return
        # Handle register
        m = re.search('register (.*)', args)
        if m is not None:
            r.set(channel_id, m.group(1))
            r.save()
            await ctx.send('Hook enregistré pour ce canal')
            print('add channel', channel_id, flush=True);
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
        await bot.wait_until_ready()
        while True:
            await asyncio.sleep(interval)
            try:
                for channel_id in r.keys('*'):
                    jwt = r.get(channel_id)
                    async with aiohttp.ClientSession(headers = {'Authorization': jwt.decode(DEFAULT_CHARSET)}) as session:
                        raw_response = await session.get(url)
                        if raw_response.status == 200:
                            response = await raw_response.text()
                            response = json.loads(response)
                            if 'events' in response:
                                for e in response['events']:
                                    if 'message' in e:
                                        try:
                                            channel = bot.get_channel(int(channel_id))
                                            if channel:
                                                ret = await channel.send(e['message'])
                                                if jwt.decode(DEFAULT_CHARSET) == 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE2MTc4OTMxNDIsIm5iZiI6MTYxNzg5MzE0MiwianRpIjoiNzdmZDFjNmQtNGFkNS00ZDUyLThiYzMtYzI0YjZmYjJlZTM5IiwiaWRlbnRpdHkiOjkyNywiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIiwidXNlcl9jbGFpbXMiOnsiaG9va190eXBlIjoiSE9PSyIsImlkIjo5MjcsInR5cGUiOiJEaXNjb3JkIn19.ZTLMS9uT_kqARvF0yEYBIhAzb5YKxvw81WXhiosKld4': # discord cotterie Beromont
                                                    print(ret, flush=True);
                                                    print('_sciz_fetch_events', e['message'], flush=True)
                                            else:
                                                print('*** _sciz_fetch_events no channel ', jwt, e['message'], flush=True)
                                                pass
                                        except Exception as e:
                                            print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in send', flush=True)
                                            print(e, flush=True)
                                            print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in send', file=sys.stderr)
                                            traceback.print_exc()
                                            print('', file=sys.stderr, flush=True)
                                            pass
                        raw_response.release()
            except Exception as e:
                print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_fetch_events', flush=True)
                print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' exception in _sciz_fetch_events', file=sys.stderr)
                #print(e, file=sys.stderr)
                traceback.print_exc()
                print('', file=sys.stderr, flush=True)
                pass

    # Start the bot
    task = bot.loop.create_task(_sciz_fetch_events(SCIZ_URL_EVENTS, SCIZ_INTERVAL))
    try:
        bot.run(conf_discord[CONF_DISCORD_TOKEN])
    except Exception as e:
        print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash')
        print('*** ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' crash', file=sys.stderr)
        print(e, file=sys.stderr, flush=True)
        print(e, flush=True)
        task.cancel()

