import json
import logging
import os
import sys
from typing import List

import discord
from discord.ext import commands

# import for type hint :
from core.LatteBot import loop_through_cogs, LatteBot


class Developer(commands.Cog):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("[cogs] Developer 모듈이 준비되었습니다.")
        pass

    # Commands
    @commands.group(name="dev",
                    description="개발자 기능들입니다.",
                    aliases=["개발자", "developer"])
    async def dev(self, ctx: commands.Context):
        """
        개발자 전용 명령어들입니다.
        """
        if ctx.invoked_subcommand is None:
            dev_embed: discord.Embed = discord.Embed(
                title="라떼봇 개발자 정보",
                description="라떼봇을 개발하는 사람들의 정보입니다.",
                color=self.bot.latte_color
            )
            dev_embed.set_footer(text=f"{ctx.author.name} 님이 요청하셨습니다!", icon_url=ctx.author.avatar_url)
            dev_embed.set_thumbnail(url=self.bot.user.avatar_url)

            dev_users: str = ''
            for dev_id in self.bot.dev_ids:
                dev_user: discord.User = discord.utils.find(lambda u: u.id == dev_id, self.bot.users)
                dev_users += f"{dev_user.name}#{dev_user.discriminator}\n"
            dev_embed.add_field(name="개발자", value=dev_users)
            
            dev_embed.add_field(name="라떼봇 공식 커뮤니티", value=f'[바로가기]({self.bot.discord_base_invite + self.bot.official_community_invite} "공식 커뮤니티로 가는 포탈이 생성되었습니다 - 삐릿")')

            await ctx.send(embed=dev_embed)
        else:
            pass

    @commands.is_owner()
    @dev.command(name="stop",
                 description="봇을 종료합니다. [WIP]",
                 aliases=["종료", "quit"])
    async def stop(self, ctx: commands.Context):
        """
        봇을 종료합니다.
        """
        self.bot.logger.info("봇 종료 명령어가 실행되었습니다!")
        await ctx.send("봇을 종료합니다!")
        self.bot.do_reboot = False
        await self.bot.close()

    @commands.is_owner()
    @dev.command(name="restart",
                 description="봇을 재시작합니다. [WIP]",
                 aliases=["재시작", "다시시작", "reboot"])
    async def restart(self, ctx: commands.Context):
        """
        봇을 종료합니다.
        """
        self.bot.logger.info("봇 재시작 명령어가 실행되었습니다!")
        await ctx.send("봇을 재시작합니다!")
        self.bot.do_reboot = True
        await self.bot.close()

    @commands.cooldown(rate=1, per=60)
    @dev.command(name="bot-notice",
                 description="봇이 접속해있는 모든 서버의 공지채널에 공지사항을 전송합니다.\n"
                             + "공지사항을 전달할 채널이 없다면, 해당 서버에는 공지사항이 전달되지 않습니다.",
                 aliases=["공지", "botnotice", "bn", "notice"])
    async def send_notice(self, ctx: discord.ext.commands.Context):
        print(f"{ctx.author}가 공지하기 명령어를 사용했습니다.")
        if ctx.author.id in self.bot.dev_ids:
            await ctx.send('소속된 서버에 해당 공지사항을 전송합니다!')
            for guild in self.bot.guilds:
                if guild.name in self.bot.guild_configs.keys():
                    notice_ch_id = self.bot.guild_configs[guild.name]["guild"]["ch_ids"]["notice"]
                    if notice_ch_id != 0:
                        await self.bot.get_channel(notice_ch_id).send(
                            f'봇 공지사항이 전달되었습니다! by {ctx.message.author}\n ' +
                            f'{ctx.message.content.replace(f"{self.bot.command_prefix}개발자 공지하기 ", "")}')
        else:
            await ctx.send(f'개발자만 사용 가능한 명령어입니다!')

    @commands.is_owner()
    @dev.command(name="create-config",
                 description="봇이 접속해있는 모든 서버의 컨피그를 확인 후, 존재하지 않을 시 새로 생성합니다.",
                 aliases=["서버컨피그생성", "createconfig", "cc"])
    async def config_check(self, ctx: commands.Context):
        for guild in self.bot.guilds:
            if not guild.name in os.listdir(self.bot.guild_configs_dir):
                await ctx.send(content=f"> {guild.name} 서버의 컨피그를 생성합니다...")
                os.mkdir(path=f"{self.bot.guild_configs_dir}/{guild.name}")
                with open(file=f"{self.bot.guild_configs_dir}/BASE-SERVER-CONFIG/server.json", mode="rt", encoding="utf-8") as base_config_file:
                    base_config: dict = json.load(fp=base_config_file)
                base_config["guild_info"]["name"] = guild.name
                base_config["guild_info"]["id"] = guild.id
                self.bot.guild_configs[guild.name] = base_config
                with open(file=f"{self.bot.guild_configs_dir}/{guild.name}/server.json", mode="wt", encoding="utf-8") as guild_config_file:
                    json.dump(obj=base_config, fp=guild_config_file, indent=4, ensure_ascii=False)
                await ctx.send(content=f"> {guild.name} 서버의 컨피그를 생성했습니다!")

        await ctx.send(content=f"> 모든 서버의 컨피그가 존재합니다!")

    @commands.is_owner()
    @dev.command(name="server-list",
                 description="봇이 접속해있는 서버의 목록을 DM으로 보여줍니다.",
                 aliases=["서버목록", "serverlist", "sl"])
    async def show_guilds(self, ctx: commands.Context):
        await ctx.author.send(content="> 봇이 접속해있는 서버들의 정보를 전송합니다!")
        for guild in self.bot.guilds:
            guild_embed = discord.Embed(
                title=f"**`{guild.name}`**",
                colour=self.bot.latte_color
            )
            guild_embed.add_field(name="서버 생성 일자", value=str(guild.created_at))

            guild_embed.add_field(name="서버 채널 개수", value=str(len(guild.channels)), inline=True)
            guild_embed.add_field(name="서버 멤버 수", value=str(len(guild.members)), inline=True)
            await ctx.author.send(embed=guild_embed)

    @commands.is_owner()
    @dev.command(name="server-channel-list",
                 description="봇이 접속해있는 서버의 목록을 DM으로 보여줍니다.",
                 aliases=["서버채널목록", "serverchannellist", "scl", "server-ch-list"])
    async def show_guild_channels(self, ctx: commands.Context, *, guild_name):
        guild: discord.Guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
        await ctx.author.send(content=f"```{guild}```\n> 서버의 정보를 전송합니다!")
        guild_embed = discord.Embed(
            title=f"**`{guild.name}`**",
            colour=self.bot.latte_color
        )

        guild_embed.add_field(name="서버 채널 목록", value="\u200b\n\u200b", inline=False)
        for channel in guild.channels:
            guild_embed.add_field(name=f"채널 이름", value=channel.name, inline=False)
            guild_embed.add_field(name=f"채널 유형", value=channel.type, inline=True)
        await ctx.author.send(embed=guild_embed)

    @commands.is_owner()
    @dev.command(name="server-member-list",
                 description="봇이 접속해있는 서버의 목록을 DM으로 보여줍니다.",
                 aliases=["서버유저목록", "servermemberlist", "sml", "server-m-list"])
    async def show_guild_members(self, ctx: commands.Context, *, guild_name):
        guild: discord.Guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
        await ctx.author.send(content=f"```{guild}```\n> 서버의 정보를 전송합니다!")
        guild_embed = discord.Embed(
            title=f"**`{guild.name}`**",
            colour=self.bot.latte_color
        )
        guild_embed.add_field(name="서버 멤버 목록", value="\u200b\n\u200b", inline=False)
        for member in guild.members:
            print(member)
            guild_embed.add_field(name=f"멤버 프로필 이름", value=member.name, inline=False)
            guild_embed.add_field(name=f"서버 내 멤버 이름", value=member.display_name, inline=False)
        await ctx.author.send(embed=guild_embed)

    @commands.is_owner()
    @dev.command(name="get-server-invite",
                 description="해당 서버의 초대링크를 얻습니다.",
                 aliases=["서버초대링크얻기", "getserverinvite", "gsi"])
    async def get_guild_invite(self, ctx: commands.Context, *, guild_name: str):
        guild: discord.Guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
        guild_invites: List[discord.Invite] = await guild.invites()
        await ctx.author.send(content=f"{guild_name} 서버의 활성화된 초대링크 개수 : {len(guild_invites)}")
        for invite in guild_invites:
            await ctx.author.send(content=f"{guild_name} 서버의 활성화된 초대링크 : {invite.url}")

    @commands.is_owner()
    @dev.command(name="create-server-invite",
                 description="해당 서버의 초대링크를 생성합니다.",
                 aliases=["서버초대링크생성", "createserverinvite", "csi"])
    async def get_guild_invite(self, ctx: commands.Context, period_sec=0, tries=0, *, guild_name: str):
        guild: discord.Guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
        import random
        random_channel: discord.TextChannel = random.choice(guild.text_channels)
        random_channel_invite: discord.Invite = await random_channel.create_invite(reason="라떼봇 개발자의 소속서버 점검", max_age=period_sec, max_uses=tries)
        await ctx.author.send(content=f"연결된 서버 : {guild.name} & 연결된 채널 : {random_channel.name} & 초대 링크 옵샨 : 기간 {period_sec}, {tries}회 이용가능")
        await ctx.author.send(content=f"> 초대링크 : {random_channel_invite.url}")

    @commands.is_owner()
    @dev.command(name="server-leave",
                 description="봇을 해당 서버에서 탈출시킵니다.",
                 aliases=["서버떠나기", "serverleave"])
    async def get_guild_invite(self, ctx: commands.Context, *, guild_name: str):
        guild: discord.Guild = discord.utils.find(lambda g: g.name == guild_name, self.bot.guilds)
        await ctx.send(content="서버에서 나갑니다...")
        await guild.leave()

    """
    [ Cogs Management ]
    Using discord.ext.commands.Cog, this bot manages several function per extension.
    """

    @commands.group(name="module",
                    description="해당 서버의 초대링크를 얻습니다.",
                    aliases=["모듈"],
                    invoke_without_command=True)
    async def manage_module(self, ctx: commands.Context):
        if ctx.author.id in self.bot.dev_ids:
            if ctx.invoked_subcommand is None:
                msg = ">>> **현재 불러와진 모듈**"
                for module in self.bot.extensions:
                    msg += f'\n \* {str(module).replace("cogs.", "")}'

                msg += "\n\n사용법: `모듈 (로드/언로드/리로드) [모듈이름]`"
                await ctx.send(msg)
            else:
                pass
        else:
            return await ctx.send("봇의 개발자가 아니므로 사용할 수 없습니다!")
            pass

    @manage_module.command(name="load",
                           description="모듈을 로드합니다.",
                           aliases=["로드"])
    async def cmd_cog_load(self, ctx: commands.Context, target_cog_name: str = "all"):
        if ctx.author.id in self.bot.dev_ids:
            self.target_cog_load(directory=self.bot.module_dir, target_cog_name=target_cog_name)
            return await ctx.send(f"> {target_cog_name} 모듈을 로드했습니다.")
        else:
            return await ctx.send("봇의 개발자가 아니므로 사용할 수 없습니다!")

    @loop_through_cogs()
    def target_cog_load(self, cog_name: str):
        self.bot.load_extension(cog_name)

    @manage_module.command(name="unload",
                           description="모듈을 언로드합니다.",
                           aliases=["언로드"])
    async def cmd_cog_unload(self, ctx: commands.Context, target_cog_name: str = "all"):
        if ctx.author.id in self.bot.dev_ids:
            self.target_cog_unload(directory=self.bot.module_dir, target_cog_name=target_cog_name)
            return await ctx.send(f"> {target_cog_name} 모듈을 언로드했습니다.")
        else:
            return await ctx.send("봇의 개발자가 아니므로 사용할 수 없습니다!")

    @loop_through_cogs()
    def target_cog_unload(self, cog_name: str):
        self.bot.unload_extension(cog_name)

    @manage_module.command(name="reload",
                           description="모듈을 리로드합니다.",
                           aliases=["리로드"])
    async def cmd_cog_reload(self, ctx: commands.Context, target_cog_name: str = "all"):
        if ctx.author.id in self.bot.dev_ids:
            self.target_cog_reload(directory=self.bot.module_dir, target_cog_name=target_cog_name)
            return await ctx.send(f"> {target_cog_name} 모듈을 리로드했습니다.")
        else:
            return await ctx.send("봇의 개발자가 아니므로 사용할 수 없습니다!")

    @loop_through_cogs()
    def target_cog_reload(self, cog_name: str):
        self.bot.reload_extension(cog_name)


def setup(bot):
    bot.logger.info("[cogs] Developer 모듈의 셋업 단계입니다!")
    bot.add_cog(Developer(bot))
