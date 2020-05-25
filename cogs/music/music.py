# import for Discord
import discord
from discord.ext import commands

# import for Youtube
import youtube_dl

# import for type hint :
from app import LatteBot


class LatteMusic():
    __queue = []

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        pass


class Music(commands.Cog, name="음악"):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        # logger.info('[legacy_cogs] [minecraft] Minecraft 모듈이 준비되었습니다.')
        pass

    # Commands
    @commands.group(name="music",
                    description='음악 관련 기능들입니다.',
                    aliases=['m', "음악", "노래"])
    async def music(self, ctx: commands.Context):
        """
        음악 관련 기능을 제공하는 모듈입니다.
        음악 스트리밍 중심으로 디스코드의 음성 채팅방에서 음악 감상을 즐길 수 있도록 하는 기능들을 모아두었습니다.
        """
        pass

    @music.group(name='queue',
                 description='재생목록에 음악을 추가합니다.',
                 aliases=['q', "음악", "노래"])
    async def queue(self, ctx: commands.Context):
        """
        음악 재생목록에 음악을 추가합니다.
        """
        pass


def setup(bot):
    # logger.info('[legacy_cogs] [minecraft] Minecraft 모듈을 준비합니다.')
    bot.add_cog(Music(bot))