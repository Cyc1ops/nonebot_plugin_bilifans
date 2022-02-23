from nonebot.typing import T_State
from nonebot.params import State, CommandArg
from nonebot.rule import to_me
import random
import os
import re
import nonebot
from nonebot import logger
from nonebot import on_command, on_regex, on_keyword, require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GROUP, MessageSegment, Event, Message
import math
import httpx
import json
import urllib.parse
import aiohttp

scheduler = require("nonebot_plugin_apscheduler").scheduler

file = os.path.join(os.path.dirname(__file__), 'data.json')
fans_data = {}
fans_data=json.load(open(file, 'r', encoding='utf8'))

get_fans = on_command('查粉丝', aliases={'查粉'}, priority=52, block=True)

@get_fans.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    args = args.extract_plain_text().strip()
    if not args:
        await get_fans.finish("请输入你查询的UP主捏~")
    else:
        bili_UP = args
        mid = await get_mid(bili_UP)
        name, fans, pic = await get_fan(mid)
        if mid not in fans_data.keys():
            add_up(mid, name)

        fans_today = fans_data[mid]['fans_today']
        fans_yesterday = fans_data[mid]['fans_yesterday']

        msg = MessageSegment.image(pic) + f'{name}' + f'\n当前粉丝数：{fans}'

        if fans_today != '明天才能看到数据捏' and fans_yesterday != '明天才能看到数据捏':
            change = fans_today-fans_yesterday
            if change >= 0:
                msg = msg + f'\n昨日粉丝增加了：{change}'
            else:
                change = 0-change
                msg = msg + f'\n昨日粉丝减少了：{change}'
        else:
            msg = msg + f'\n昨日粉丝数变化要到明天才能看到数据捏~'
        await get_fans.finish(msg)




async def get_mid(bili_UP):
    search_url = f"http://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword={urllib.parse.quote(bili_UP)}"
    async with aiohttp.request(
            "GET", search_url, timeout=aiohttp.client.ClientTimeout(10)
    ) as resp:
        rd = await resp.json()

    try:
        mid = rd['data']['result'][0]['mid']
        return str(mid)
    except:
        await get_fans.finish("查不到这个UP主诶~")

async def get_fan(mid):
    search_url = f"http://api.bilibili.com/x/web-interface/card?mid={mid}"
    async with aiohttp.request(
            "GET", search_url, timeout=aiohttp.client.ClientTimeout(10)
    ) as resp:
        rd = await resp.json()
    name = rd['data']['card']['name']
    fans = rd['data']['card']['fans']
    pic = rd['data']['card']['face']
    return name, fans, pic

def add_up(mid, name):
    fans_data[mid]={}
    fans_data[mid]['name']=name
    fans_data[mid]['fans_today']='明天才能看到数据捏'
    fans_data[mid]['fans_yesterday'] = '明天才能看到数据捏'
    # fans_data[name]['fans_change'] = '明天才能看到数据捏'
    with open(file, 'w', encoding='utf8') as f:
        json.dump(fans_data, f, ensure_ascii=False, indent=4)

# 重置一天的数据
@scheduler.scheduled_job("cron", hour=0, minute=0)
async def _():
    for i in fans_data.keys():
        name, fans, pic = await get_fan(i)
        fans_data[i]['fans_yesterday']=fans_data[i]['fans_today']
        fans_data[i]['fans_today'] = fans
    with open(file, 'w', encoding='utf8') as f:
        json.dump(fans_data, f, ensure_ascii=False, indent=4)