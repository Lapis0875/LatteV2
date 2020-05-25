import json
import os

import discord
from discord.ext import commands
from app import LatteBot


class Config(commands.Cog):
    bot: LatteBot = None

    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("[cogs] Config 모듈이 준비되었습니다!")
        pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.logger.info(f"새로운 서버에 참여했습니다! : {guild.name}")
        await self.create_config(guild=guild)
        self.bot.logger.info(f"컨피그를 생성했습니다!")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.bot.logger.info(f"참여했던 서버에서 나갔습니다... : {guild.name}")
        await self.delete_config(guild=guild)
        self.bot.logger.info(f"컨피그를 삭제했습니다!")

    @commands.is_owner()
    @commands.group(name="config",
                    description="봇의 콘피그 파일을 조작합니다.",
                    aliases=["컨피그", "콘피그"])
    async def cmd_config(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.author.send(content="봇의 콘피그 조작 명령어입니다! 리로드/언로드 가 가능하며, 직접 작성하는것 또한 가능합니다.")

    @commands.is_owner()
    @cmd_config.command(name="reload",
                        description="봇의 컨피그 파일을 다시 읽어옵니다. 존재하지 않는다면, 새로 생성합니다.",
                        aliases=["리로드"])
    async def cmd_config_reload(self, ctx: commands.Context):
        await self.load_config(ctx.guild)
        await ctx.send("> 이 서버의 설정파일을 리로드했습니다!")

    @commands.is_owner()
    @cmd_config.command(name="reset",
                        description="봇의 컨피그 파일을 초기화합니다.",
                        aliases=["리셋", "초기화"])
    async def cmd_config_reset(self, ctx: commands.Context):
        await self.reset_config(ctx.guild)
        await ctx.send("> 이 서버의 설정파일을 초기화했습니다!")

    @commands.has_guild_permissions(administrator=True)
    @cmd_config.command(name="view",
                        description="이 서버의 컨피그 파일을 DM으로 보여줍니다.",
                        aliases=["보기"])
    async def cmd_config_view(self, ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id in self.bot.dev_ids:
            config_str: str = json.dumps(obj=self.bot.guild_configs[ctx.guild.name], indent=2, ensure_ascii=False)
            if len(config_str) > 2000:
                with open(file=f"{self.bot.guild_configs_dir}/{ctx.guild.name}/server.json", mode="wt", encoding="utf-8") as guild_config_file:
                    json.dump(obj=self.bot.guild_configs[ctx.guild.name], fp=guild_config_file, indent=4, ensure_ascii=False)
                config_file = discord.File(fp=open(file=f"{self.bot.guild_configs_dir}/{ctx.guild.name}/server.json", mode="rt", encoding="utf-8"), filename=f"{ctx.guild.name}_server_config.json")
                await ctx.author.send(content="컨피그가 2000자를 넘어 파일로 변환해 전송합니다!", file=config_file)
            else:
                await ctx.author.send(content=config_str)

    async def create_config(self, guild: discord.Guild):
        try:
            with open(
                    file=f"{self.bot.guild_configs_dir}/BASE-SERVER-CONFIG/server.json", mode="rt", encoding="utf-8"
            ) as sample_config_file:
                config: dict = json.load(fp=sample_config_file)
                config["guild_info"]["name"] = guild.name
                config["guild_info"]["id"] = guild.id
                print(json.dumps(obj=config, indent=4, ensure_ascii=False))
                self.bot.guild_configs[guild.name] = config
                return True
        except FileExistsError:
            self.bot.logger.error("이미 파일이 존재합니다!")
            return False
        except Exception as e:
            self.bot.logger.error(e.with_traceback(e.__traceback__))
            return False

    async def load_config(self, guild: discord.Guild):
        try:
            with open(
                    file=f"{self.bot.guild_configs_dir}/{guild.name}/server.json", mode="rt", encoding="utf-8"
            ) as config_file:
                config: dict = json.load(fp=config_file)
                self.bot.guild_configs[guild.name] = config
                return True
        except FileNotFoundError:
            self.bot.logger.error("컨피그 파일이 존재하지 않습니다!")
            return await self.create_config(guild)
        except Exception as e:
            self.bot.logger.error(e.with_traceback(e.__traceback__))
            return False

    async def delete_config(self, guild: discord.Guild):
        # 저장해두던 서버 설정에서 나간 서버의 설정파일 지우기
        del self.bot.guild_configs[guild.name]

        # 로컬에 저장된 서버 설정 파일 지우기
        guild_config_dir = f"{self.bot.guild_configs_dir}/{guild.name}"
        config_files: list = os.listdir(guild_config_dir)
        for file in config_files:
            try:
                os.remove(path=guild_config_dir)
            except Exception as e:
                self.bot.logger.error(e.with_traceback(e.__traceback__))

    async def reset_config(self, guild: discord.Guild):
        await self.delete_config(guild)
        await self.create_config(guild)


def setup(bot: LatteBot):
    bot.logger.info("[cogs] Config 모듈의 셋업 단계입니다!")
    bot.add_cog(Config(bot))