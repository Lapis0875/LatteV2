import logging
import sys

import discord
from discord.ext import commands

# import for type hint :
from app import LatteBot


class Language(commands.Cog, name="언어"):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("[cogs] Language 모듈이 준비되었습니다.")
        pass

    # Commands
    @commands.group(name="언어",
                    description="봇의 언어 설정 명령어들입니다.")
    async def lang(self, ctx: commands.Context):
        """
        manage language settings of bot
        """
        if ctx.invoked_subcommand is not None:
            pass
        else:
            lang_embed: discord.Embed = discord.Embed(
                title="언어 설정 모듈",
                description="라떼봇의 언어 설정을 관리하는 모듈입니다."
            )
            await ctx.send(embed=lang_embed)


def setup(bot):
    bot.logger.info('[cogs] Language 모듈의 셋업 단계입니다!')
    bot.add_cog(Language(bot))
