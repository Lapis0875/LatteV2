import sys
import traceback

import discord
from discord.ext import commands

import json

# global variables
from core.LatteBot import LatteBot

bot = LatteBot(
    command_prefix=("라떼야 ", "라떼봇 ", "라뗴야 ", "라뗴봇 "),
    description="카페라테를 좋아하는 개발자가 만든 디스코드 봇이에요!",
    help_command=None
)

"""
[ Discord.py Event Management ]
"""


@bot.event
async def on_ready():
    bot.logger.info("봇 온라인!")
    bot.logger.info(f"owner_id : {bot.owner_id}")
    bot.logger.info(f"dev_ids : {bot.dev_ids}")

    # 봇의 상태메세지를 지속적으로 변경합니다.
    bot.loop.create_task(bot.presence_loop())


@bot.event
async def on_command(ctx: commands.Context):
    pass


@bot.event
async def on_command_error(ctx: commands.Context, e: Exception):
    bot.logger.error(e)
    error_embed = discord.Embed(
        title=" 오류가 발생했습니다!",
        description=str(e),
        colour=discord.Colour.red()
    )
    error_embed.set_footer(text="오류를 개발자에게 제보해주세요! `라떼야 제보 버그 (오류 내용 및 상황설명)`")
    await ctx.send(embed=error_embed)
    bot.parse_traceback(exception=e)


def main():
    if __name__ == "__main__":
        if sys.argv[1] == "true":
            bot.test_mode = True
        else:
            bot.test_mode = False

        # print ASCII ART
        with open(file="resources/latte_ascii.txt", mode="rt", encoding="utf-8") as f:
            print(f.read())

        # init bot settings : loads config, server settings
        bot.settings_load()

        # run bot
        bot.run()

        # save datas before program stops
        result, error = bot.settings_save()
        print(f"save_datas() 실행결과 : {result}")
        if error is not None:
            print(f"save_datas() 실행결과 발생한 오류 : {error.with_traceback(error.__traceback__)}")

        result, error = bot.clear_datas("./resources/captcha/")
        if error is not None:
            print(f"save_datas() 실행결과 발생한 오류 : {error.with_traceback(error.__traceback__)}")

        # check if the bot need to be rebooted
        bot.check_reboot()


main()
