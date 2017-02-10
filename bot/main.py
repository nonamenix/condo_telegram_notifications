import os
from datetime import datetime

import aiohttp
from aiotg import Bot
import logging
from pprint import pformat

owner_id = int(os.environ['OWNER'])
host = os.environ['CONDO_HOST']
port = os.environ.get('CONDO_PORT', 8080)
scheme = os.environ.get('CONDO_SCHEME', 'http')
condo_state_url = "{scheme}://{host}:{port}/v1/state".format(
    host=host,
    port=port,
    scheme=scheme
)
# logging
logging.basicConfig(
    level=getattr(logging, os.environ.get('BOT_LOGGING_LEVEL', 'DEBUG')),
    format='%(asctime)s | %(name)s | %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
logger.addHandler(ch)

pid_file = os.environ.get('BOT_PIDFILE', '.pid')
bot = Bot(api_token=os.environ["BOT_TOKEN"])


@bot.command("/ping")
async def ping(chat, match):
    await chat.send_text('pong')


@bot.default
async def default(chat, match):
    pass


async def condo_state():
    async with aiohttp.ClientSession() as session:
        async with session.get(condo_state_url) as response:
            body = await response.json()

    return body


@bot.command('/state_verbose')
async def status(chat, match):
    if chat.message['from']['id'] == owner_id:
        state = await condo_state()
        await chat.send_text('``` {} ```'.format(pformat(state, compact=True)), parse_mode="Markdown")


@bot.command('/state')
async def status(chat, match):
    if chat.message['from']['id'] == owner_id:
        state = await condo_state()
        if state.items():
            for name, (status, info) in state.items():
                image = dict(info['spec']['spec'][1])['Image'][1]
                await chat.send_text('name: *{name}* \nimage: {image} \nstatus: {status} \nuptime: {uptime}'.format(
                    name=name,
                    status=status,
                    image=image,
                    uptime=datetime.now() - datetime.fromtimestamp(info['created_at'])
                ),
                    parse_mode="Markdown")
        else:
            await chat.send_text('Containers not found')


if __name__ == "__main__":
    logger.info("Running...")
    bot.run()
