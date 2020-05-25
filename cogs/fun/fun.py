import logging
import sys

import discord
from discord.ext import commands
from discord.utils import find

import random

# import for type hint :
from app import LatteBot


class Fun(commands.Cog):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info('[cogs] Fun 모듈이 준비되었습니다.')
        pass

    # Commands

    """
    @commands.command(name='아무말',
                      description='아무말이나 말하는 라테봇을 볼 수 있어요!')
    async def random_text(self, ctx: commands.Context):
        try:
            with open(file='./resources/fun/random_texts.txt', mode='rt', encoding='utf-8') as rand_txt_file:
                rand_txts: list = rand_txt_file.readlines()
                choice_txt: str = random.choice(rand_txts)
                await ctx.send(choice_txt)
        except Exception as e:
            error_embed: discord.Embed = discord.Embed(
                title='오류 발생!',
                description=f'{e.with_traceback(e.__traceback__)}'
                            f'\n명령어 실행 도중 문제가 발생했습니다! 라테봇 공식 커뮤니티에서 오류 제보를 해주시면 감사하겠습니다!'
                            f'\n[공식 커뮤니티 바로가기]({self.bot.official_community_invite})',
                color=discord.Colour.red()
            )
            error_embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
            error_embed.set_footer(text=f'{ctx.author.name} 님께서 요청하셨습니다!', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=error_embed)
    """

    @commands.command(name="dice",
                      description="6면짜리 주사위를 던져요!",
                      aliases=["주사위"])
    async def roll_the_dice(self, ctx: commands.Context):
        result = random.randint(1, 6)
        result_embed: discord.Embed = discord.Embed(
            title="🎲 주사위를 던졌어요!",
            description=f"결과 : {result}",
            color=self.bot.latte_color
        )
        result_embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)
        result_embed.set_footer(text=f"{ctx.author.name} 님께서 요청하셨습니다!", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=result_embed)


def setup(bot):
    bot.logger.info('[cogs] Fun 모듈의 셋업 단계입니다!')
    bot.add_cog(Fun(bot))
