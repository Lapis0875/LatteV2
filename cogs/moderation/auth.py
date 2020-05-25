import asyncio

from discord.ext import commands
import discord
from captcha.image import ImageCaptcha
import random
from app import LatteBot


class Auth(commands.Cog):
    bot: LatteBot = None
    image_captcha: ImageCaptcha = ImageCaptcha()
    supported_modes: list = ["captcha-image"]

    captcha_chars: list = []
    base_captcha_dir: str = "./resources/captcha"

    def __init__(self, bot: LatteBot):
        self.bot = bot
        self.bot.logger.info("[cogs] Auth 모듈이 로드되었습니다!")
        self.captcha_chars = self.build_captcha_chars()

    def cog_unload(self):
        self.bot.logger.info("[cogs] Auth 모듈이 언로드됩니다...")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.bot.logger.info(f"[auth] 유저가 서버에 참여했습니다! : {member.name}")
        if member.bot:
            pass
        auth_enabled: bool = self.bot.guild_configs[member.guild.name]["bot_settings"]["modules"]["auth"][
            "enabled"]
        if not auth_enabled:
            return
        log_ch_id: int = self.bot.guild_configs[member.guild.name]["modules"]["auth"]["captcha"]["log-ch"]
        captcha_size: int = self.bot.guild_configs[member.guild.name]["modules"]["auth"]["captcha"]["text-size"]
        if captcha_size == 0:
            await member.guild.owner.send(f"당신의 서버 {member.guild}에 새로운 유저가 접속을 시도했으나, CAPTCHA 의 문자 개수가 0으로 설정되어 인증에"
                                          + f"실패했습니다! `라떼야 인증 캡차 문자길이 (양의 정수)` 명령어로 문자 개수를 설정해주세요!")
        if log_ch_id == 0:
            await member.guild.owner.send(f"당신의 서버 {member.guild}에 새로운 유저가 접속을 시도했으나, CAPTCHA 로그 채널이 설정되지 않아 인증에 "
                                          + f"실패했습니다! `라떼야 인증 캡차 로그채널 #채널` 명령어로 로그 채널을 설정해주세요!")

        captcha_tries: int = 0
        while not await self.process_auth_captcha(member=member, captcha_size=captcha_size):
            captcha_tries += 1
            if captcha_tries > 5:
                return await member.send(content="실패 횟수가 너무 많습니다!")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass

    @commands.has_guild_permissions(administrator=True)
    @commands.group(name="authorization",
                    description="디스코드 서버에 들어오는 유저들을 인증하기 위한 기능입니다.",
                    aliases=["auth", "authorize"])
    async def auth(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send("현재 지원하는 유저 인증 기능은 다음과 같습니다! : [ 이미지 CAPTCHA ]")
        pass

    @auth.command(name="enable",
                  description="라떼봇의 유저 인증 기능을 활성화합니다.",
                  aliases=["on", "activate"])
    async def activate_auth(self, ctx, *, mode: str = ''):
        if mode not in self.supported_modes:
            return await ctx.send(content=f"지원하지 않는 모드입니다! 사용 가능한 모드는 다음과 같습니다 : {self.supported_modes}")

        if mode == "captcha-image":
            if self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["log-ch"] == 0:
                return await ctx.send(content="캡차 로그 채널이 지정되지 않았습니다! `라떼야 인증 캡차 로그채널` 명령어로 로그채널을 설정해주세요.")
            if self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["text-size"] == 0:
                return await ctx.send(content="캡차의 문자 길이가 지정되지 않았습니다! `라떼야 인증 캡차 문자길이` 명령어로 캡차의 문자 길이를 설정해주세요.")

        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["enabled"] = True
        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["mode"] = mode
        return await ctx.send(content=f"{mode} 모드로 서버의 인증을 활성화했습니다!")

    @auth.command(name="disable",
                  description="라떼봇의 유저 인증 기능을 비활성화합니다.",
                  aliases=["off", "deactivate"])
    async def deactivate_auth(self, ctx: commands.Context):
        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["enabled"] = False
        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["mode"] = ""
        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["text-size"] = 0
        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["log-ch"] = 0
        return await ctx.send(content=f"지원하지 않는 모드입니다! 사용 가능한 모드는 다음과 같습니다 : {self.supported_modes}")

    @auth.group(name="CAPTCHA",
                description="CAPTCHA 인증과 관련된 명령어들입니다.",
                aliases=["captcha"])
    async def captcha(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send("CAPTCHA는 널리 사용되는 유저 인증 방식 중 하나로, 라떼봇은 이미지 기반 CAPTCHA 인증을 지원합니다.")
        pass

    @captcha.command(name="log-channel",
                     description="CAPTCHA 인증을 사용하기 위한 로그 채널을 설정합니다. 로그 채널에는 캡차로 생성된 이미지들이 캡차가 진행되는동안 업로드되며, "
                                 + "캡차가 완료된 이후에는 삭제됩니다.",
                     aliases=["logch", "log", "logchannel", "lc"])
    async def log_setting(self, ctx: commands.Context, log_channel: discord.TextChannel):
        if type(log_channel) != discord.TextChannel:
            return await ctx.send(content="잘못된 인자입니다! 로그 채널로는 서버 내의 텍스트 채널만 사용 가능합니다!")

        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["log-ch"] = log_channel.id
        return await ctx.send(content="서버의 CAPTCHA 로그 채널을 설정했습니다!")

    @captcha.command(name="text-length",
                     description="CAPTCHA 인증 이미지에 사용될 문자의 개수입니다. 문자의 개수는 양의 정수여야 합니다. 문자의 개수는 적어도 6개 이상을 권장합니다. ",
                     aliases=["length", "textlength", "tl"])
    async def text_size_setting(self, ctx: commands.Context, size: int):
        if size <= 0:
            return await ctx.send(content="잘못된 인자입니다! 문자의 개수는 양의 정수여야 합니다!")

        self.bot.guild_configs[ctx.guild.name]["modules"]["auth"]["captcha"]["text-size"] = size
        return await ctx.send(content="서버의 CAPTCHA 문자 길이를 설정했습니다!")

    async def process_auth_captcha(self, member: discord.Member, captcha_size: int):
        (answer, filename) = await self.create_captcha(member.id, captcha_size)
        with open(file=f"{self.base_captcha_dir}/{filename}", mode="rb") as captcha_image_file:
            await member.send(file=discord.File(fp=captcha_image_file, filename=filename))
            captcha_embed = discord.Embed(
                title="당신이 사람인지 확인해야 합니다!",
                description="위 이미지에 보이는 문자를 입력해주세요. 30초의 시간이 주어집니다.",
                colour=self.bot.latte_color
            )
            captcha_embed.set_thumbnail(url=f"attachment://{filename}")
            captcha_msg: discord.Message = await member.send(embed=captcha_embed)
            await captcha_msg.add_reaction('🔄')

        def check(message: discord.Message):
            return message.author.id == member.id and message.content == answer

        try:
            msg = await self.bot.wait_for(event="message", timeout=30, check=check)
            self.bot.logger.info(f"[auth] 유저가 인증에 성공했습니다! : {member.name}")
            await member.send(content="인증에 성공했습니다!")
            return True
        except asyncio.exceptions.TimeoutError:
            await member.send(content="시간초과입니다!")
            await member.send(content="서버에 다시 접속해 재시도해주세요!")
            await member.kick(reason="라떼봇 - 유저 인증 실패")
            self.bot.logger.info(f"[auth] 유저가 인증에 실패했습니다! : {member.name}")
            return False

    def build_captcha_chars(self):
        numbers: list = [chr(ascii) for ascii in range(48, 58)]
        big_alphabets: list = [chr(ascii) for ascii in range(65, 91)]
        small_alphabets: list = [chr(ascii) for ascii in range(97, 123)]
        special_chars: list = ['#', '$', '%', '&', '@', '!', '?']
        return numbers + big_alphabets + small_alphabets + special_chars

    async def create_captcha(self, user_id: int, length: int):
        filename: str = f"{user_id}.png"

        answer: str = ""
        for count in range(length):
            index: int = random.randint(0, len(self.captcha_chars) - 1)
            answer += self.captcha_chars[index]
        self.image_captcha.write(answer, f"{self.base_captcha_dir}/{filename}")
        return answer, filename

    async def log(self, guild: discord.Guild, channel_id, user_mention: str, captcha_image: discord.File):
        log_ch: discord.TextChannel = discord.utils.find(lambda ch: ch.id == channel_id, guild.text_channels)
        await log_ch.send(content=f"> {user_mention} 님의 인증 시도입니다!", file=captcha_image)


def setup(bot: LatteBot):
    bot.logger.info("[cogs] Auth 모듈의 셋업 단계입니다!")
    bot.add_cog(Auth(bot))
