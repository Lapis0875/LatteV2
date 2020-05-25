import json
from typing import Union

import discord
from discord.ext import commands

# import for type hint :
from discord.utils import get, find

from app import LatteBot


class Management(commands.Cog):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot
        self.bot.logger.info("[cogs] Management 모듈을 초기화합니다.")
        self.bot.guild_autorole_datas = self.bot.parse_guild_configs(storage=self.bot.guild_autorole_datas, filename="autorole_map.json")
        for guild_name, data_map in self.bot.guild_autorole_datas.items():
            if data_map == {}:
                self.bot.guild_autorole_datas[guild_name].update({"DEFAULT": {}})

    def cog_unload(self):
        self.bot.logger.info("[cogs] Management 모듈이 언로드됩니다...")
        for guild_name, data in self.bot.guild_autorole_datas.items():
            self.bot.logger.info(f"[cogs] {guild_name} 서버의 컨피그를 저장합니다")
            with open(file=f"./configs/{guild_name}/autorole_map.json", mode="wt", encoding="utf-8") as autorole_map_file:
                json.dump(obj=self.bot.guild_autorole_datas[guild_name], fp=autorole_map_file, indent=4, ensure_ascii=False)

            self.bot.logger.info(f"[cogs] {guild_name} 서버의 컨피그를 저장했습니다")

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        on_raw_reaction_add(payload):
            ...

        봇의 캐싱 여부와 무관하게 메세지에 반응이 추가되었을 때 실행되는 이벤트입니다.
        paylod는 discord.RawReactionActionEvent class로, 자세한 설명은

        on_raw_reaction_add() 이벤트 설명 : https://discordpy.readthedocs.io/en/latest/api.html#discord.on_raw_reaction_add
        payload 설명 : https://discordpy.readthedocs.io/en/latest/api.html#discord.RawReactionActionEvent

        에서 확인하실 수 있습니다.
        """

        # payload에서 필요한 정보를 저장한다.
        msg_id: int = payload.message_id  # 반응 추가 이벤트가 발생한 메세지 id
        guild_id: int = payload.guild_id  # 반응 추가 이벤트가 발생한 길드 id
        member: discord.Member = payload.member  # 반응 추가 이벤트를 발생시킨 사용자. REACTION_ADD 유형의 이벤트에서만 사용 가능하다.
        emoji: discord.PartialEmoji = payload.emoji # 반응 추가 이벤트에서 제거된 이모지

        guild: discord.Guild = find(lambda g: g.id == guild_id, self.bot.guilds)  # 반응 추가 이벤트가 발생한 길드
        self.bot.logger.info(f'[cogs] [Management] (on_raw_reaction_add) *{guild.name}* 서버에서 반응 추가 이벤트 발생!')

        if msg_id in self.bot.guild_configs[guild.name]["modules"]["management"]["features"]["auto-role"]["msg"]:
            target_role: discord.Role = None
            for data_map in self.bot.guild_autorole_datas[guild.name].values():
                for emoji_or_id, role_id in data_map.items():
                    # If the emoji is a unicode emoji
                    if emoji.name == emoji_or_id:
                        target_role = guild.get_role(role_id=role_id)
                        break
                    # If the emoji is a custom emoji
                    elif str(emoji.id) == emoji_or_id:
                        target_role = guild.get_role(role_id=role_id)
                        break
                if target_role != None:
                    break
            return await member.add_roles([target_role], reason="라떼봇의 역할 자동부여 기능")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        on_raw_reaction_remove(payload):
            ...

        봇의 캐싱 여부와 무관하게 메세지에 반응이 제거되었을 때 실행되는 이벤트입니다.
        paylod는 discord.RawReactionActionEvent class로, 자세한 설명은

        on_raw_reaction_add() 이벤트 설명 : https://discordpy.readthedocs.io/en/latest/api.html#discord.on_raw_reaction_remove
        payload 설명 : https://discordpy.readthedocs.io/en/latest/api.html#discord.RawReactionActionEvent

        에서 확인하실 수 있습니다.
        """
        # payload에서 필요한 정보를 저장한다.
        msg_id: int = payload.message_id  # 반응 제거 이벤트가 발생한 메세지 id
        guild_id: int = payload.guild_id  # 반응 제거 이벤트가 발생한 길드 id
        user_id: int = payload.user_id  # 반응 제거 이벤트를 발생시킨 유저 id
        emoji: discord.PartialEmoji = payload.emoji # 반응 제거 이벤트에서 제거된 이모지

        guild: discord.Guild = find(lambda g: g.id == guild_id, self.bot.guilds)  # 반응 추가 이벤트가 발생한 길드
        self.bot.logger.info(f'[cogs] [Management] (on_raw_reaction_add) *{guild.name}* 서버에서 반응 제거 이벤트 발생!')

        if msg_id in self.bot.guild_configs[guild.name]["modules"]["management"]["features"]["auto-role"]["msg"]:
            target_role: discord.Role = None
            for data_map in self.bot.guild_autorole_datas[guild.name].values():
                for emoji_or_id, role_id in data_map.items():
                    # If the emoji is a unicode emoji
                    if emoji.is_unicode_emoji() and emoji.name == emoji_or_id:
                        target_role = guild.get_role(role_id=role_id)
                        break
                    # If the emoji is a custom emoji
                    elif emoji.is_custom_emoji() and str(emoji.id) == emoji_or_id:
                        target_role = guild.get_role(role_id=role_id)
                        break
                if target_role != None:
                    break
            return await guild.get_member(user_id=user_id).remove_roles([target_role], reason="라떼봇의 역할 자동부여 기능")

    # Commands
    @commands.group(name="manage",
                    description="서버 관리 기능을 제공하는 명령어 그룹입니다.",
                    aliases=["관리", "management"])
    async def manage(self, ctx: commands.Context):
        """
        서버 관리 기능을 제공하는 명령어 그룹입니다.
        """
        self.bot.logger.info(f'[cogs] [management] {ctx.author} 유저가 {ctx.command} 명령어를 사용했습니다!')
        if ctx.invoked_subcommand is None:
            await ctx.send("서버 관리 명령어입니다. 사용 가능한 명령어들은 `라떼야 도움말 management` 명령어로 확인해주세요!")
        else:
            pass

    @commands.has_guild_permissions(administrator=True)
    @manage.command(name="kick",
                    description="멘션한 유저를 추방합니다.",
                    aliases=["추방"])
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        await member.kick(reason=reason)
        kick_embed = discord.Embed(title="**킥**", description=f"*{member.mention} 님이 킥 처리되었습니다.*")
        kick_embed.add_field(name="**사유**", value=f"*{reason}*", inline=False)

        await self.bot.send_log(ctx.guild.name, kick_embed)

    @commands.has_guild_permissions(administrator=True)
    @manage.command(name="ban",
                    description="멘션한 유저를 차단합니다.",
                    aliases=["차단"])
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        await member.ban(reason=reason)
        ban_embed = discord.Embed(title="**밴**", description=f"*{member.mention} 님이 밴 처리되었습니다.*")
        ban_embed.add_field(name="**사유**", value=f"*{reason}*", inline=False)

        await self.bot.send_log(ctx.guild.name, ban_embed)

    @commands.has_guild_permissions(administrator=True)
    @manage.command(name="pardon",
                    description="멘션한 유저의 차단을 해제합니다.",
                    aliases=["차단해제", "언밴", "unban"])
    async def pardon(self, ctx: commands.Context, id, *, reason: str = None):
        ban_entries: list = await ctx.guild.bans()
        target_ban_entry: discord.guild.BanEntry = discord.utils.find(lambda be: be.user.id == id, ban_entries)

        await ctx.guild.unban(target_ban_entry.user, reason=reason)
        unban_embed = discord.Embed(title="**언밴**", description=f"*{target_ban_entry.user.mention} 님이 밴 해제 처리되었습니다.*")
        unban_embed.add_field(name="**사유**", value=f"*{reason}*", inline=False)

        await self.bot.send_log(ctx.guild.name, unban_embed)

    @commands.has_guild_permissions(administrator=True)
    # @commands.has_guild_permissions(manage_messages=True)
    @manage.command(name="clean-message",
                    description="주어진 개수만큼 해당 채널에서 메세지를 삭제합니다.",
                    aliases=["채팅청소", "clean-msg", "cm"])
    async def clean_msg(self, ctx: commands.Context, amount: int = 5):
        if amount < 1:
            return await ctx.send(f"{amount} 는 너무 적습니다!")

        await ctx.send(content=f"> 🌀 {amount} 개의 메세지를 삭제합니다!")

        del_msgs: list = await ctx.channel.purge(limit=amount+1)
        count: int = len(del_msgs)
        purge_embed = discord.Embed(title="채팅 청소기 🌀", description=f"채팅창을 청소했습니다. {count}개의 메세지를 삭제했습니다.")
        await ctx.send(embed=purge_embed)

        await self.bot.send_log(ctx.guild.name, purge_embed)

    @commands.has_guild_permissions(administrator=True)
    @manage.group(name="auto-role",
                  description="역할을 자동으로 지급해주는 메세지를 생성합니다. __**[주의] 이 명령어는 역할 멘션을 포함합니다!**__",
                  aliases=["자동역할", "ar"])
    async def auto_role(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            print(f"{ctx.message.content}")
            registered_data_embed = discord.Embed(
                title="라떼봇 - [관리]자동역할",
                description="현재 등록되어있는 이모지와 역할의 목록입니다.",
                colour=self.bot.latte_color
            )
            for category, data_map in self.bot.guild_autorole_datas[ctx.guild.name].items():
                registered_data_str = ""
                print(f"category = {category}")
                print(f"data_map = {data_map}")
                if data_map == {}:
                    registered_data_str += "현재 등록된 데이터가 없습니다 :("
                else:
                    for emoji_id, role_id in data_map.items():
                        emoji = None
                        # If emoji is a custom emoji, then id(int) is saved.
                        if type(emoji_id) == int:
                            emoji = self.bot.get_emoji(emoji_id)
                        # If emoji is a unicode emoji, then emoji itself(str) is saved.
                        elif type(emoji_id) == str:
                            emoji = emoji_id

                        # Get a role by id(int)
                        role = ctx.guild.get_role(role_id=role_id)
                        registered_data_str += f"{str(emoji)} : {role.mention}\n"

                registered_data_embed.add_field(name=f"**{category}** 카테고리에 등록된 데이터", value=registered_data_str)

            registered_data_embed.set_author(name=ctx.guild.me.display_name, icon_url=self.bot.user.avatar_url)
            registered_data_embed.set_footer(text=f"{ctx.author.name}님이 요청하셨습니다!", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=registered_data_embed)

    @commands.has_guild_permissions(administrator=True)
    @auto_role.command(name="register-category",
                      description="자동역할 명령어에서 사용할 이모지에 대응하는 역할을 저장합니다. __**[주의] 이 명령어는 역할 멘션을 포함합니다!**__",
                      aliases=["카테고리등록", "rc"])
    async def autorole_register_category(self, ctx: commands.Context, category: str = ''):
        if category != '':
            self.bot.guild_autorole_datas[ctx.guild.name].update({category: {}})
            await ctx.send(content=f"> {category} 카테고리를 생성했습니다!")
        else:
            await ctx.send(content="> 생성할 카테고리 이름을 등록해 주세요!")

    @commands.has_guild_permissions(administrator=True)
    @auto_role.command(name="register-role",
                      description="자동역할 명령어에서 사용할 이모지에 대응하는 역할을 저장합니다. __**[주의] 이 명령어는 역할 멘션을 포함합니다!**__",
                      aliases=["역할등록", "reg-r"])
    async def autorole_register_data(self, ctx: commands.Context, emoji: Union[discord.Emoji, str], role: discord.Role, category: str = "DEFAULT"):
        if category in self.bot.guild_autorole_datas[ctx.guild.name].keys():
            if type(emoji) == discord.Emoji:
                self.bot.guild_autorole_datas[ctx.guild.name][category].update({str(emoji.id): role.id})
            elif type(emoji) == str:
                if ':' not in emoji:
                    self.bot.guild_autorole_datas[ctx.guild.name][category].update({emoji: role.id})
                else:
                    return await ctx.send(content=f"> 잘못된 이모지입니다!")
            await ctx.send(content=f"> `{category}` 카테고리에 [ {emoji} ☞ {role.mention} ] 데이터를 추가했습니다!")
        else:
            await ctx.send(content=f"> {category} 는 생성되지 않은 카테고리입니다! 우선 `라떼봇 관리 자동역할 카테고리등록 {category}` 명령어로 카테고리를 생성해 주세요.")

    @commands.has_guild_permissions(administrator=True)
    @auto_role.command(name="remove-role",
                      description="자동역할 명령어에서 사용할 이모지에 대응하는 역할을 제거합니다. __**[주의] 이 명령어는 역할 멘션을 포함합니다!**__",
                      aliases=["역할제거", "rm-r"])
    async def autorole_delete_data(self, ctx: commands.Context, emoji: Union[discord.Emoji, str], role: discord.Role,
                                     category: str = "DEFAULT"):
        if category in self.bot.guild_autorole_datas[ctx.guild.name].keys():
            if type(emoji) == discord.Emoji:
                self.bot.guild_autorole_datas[ctx.guild.name][category].pop(str(emoji.id))
            elif type(emoji) == str:
                if ':' not in emoji:
                    self.bot.guild_autorole_datas[ctx.guild.name][category].pop(emoji)
                else:
                    return await ctx.send(content=f"> 잘못된 이모지입니다!")
            await ctx.send(content=f"> `{category}` 카테고리에 [ {emoji} ☞ {role.mention} ] 데이터를 추가했습니다!")
        else:
            await ctx.send(
                content=f"> {category} 는 생성되지 않은 카테고리입니다!")

    @commands.has_guild_permissions(administrator=True)
    @auto_role.command(name="create",
                      description="이모지를 눌러 대응하는 역할을 자동으로 지급해주는 메세지를 생성합니다.",
                      aliases=["생성", "c"])
    async def autorole_create_message(self, ctx: commands.Context):
        autorole_info_embed = discord.Embed(
            title="역할 자동 지급용 메세지입니다!",
            description="이모지를 눌러 대응하는 역할을 자동으로 지급받을 수 있습니다!",
            colour=self.bot.latte_color
        )
        await ctx.send(embed=autorole_info_embed)
        for category_name, data_dict in self.bot.guild_autorole_datas[ctx.guild.name].items():
            autorole_category_embed = discord.Embed(
                title=f"< {category_name} >",
                description="이모지를 눌러 대응하는 역할을 자동으로 지급받을 수 있습니다!",
                colour=self.bot.latte_color
            )
            emojis = []
            for emoji_or_id, role_id in data_dict.items():
                if emoji_or_id.isdigit():
                    emoji = self.bot.get_emoji(int(emoji_or_id))
                else:
                    emoji = emoji_or_id
                emojis.append(emoji)
                role_mention: str = ctx.guild.get_role(role_id).mention
                autorole_category_embed.add_field(name=f"{str(emoji)} 이모지", value=f"→ {role_mention}")
            msg = await ctx.send(embed=autorole_category_embed)
            for emoji in emojis:
                await msg.add_reaction(emoji)
            self.bot.guild_configs[ctx.guild.name]["modules"]["management"]["features"]["auto-role"]["msg"].append(msg.id)

    @commands.has_guild_permissions(administrator=True)
    @auto_role.command(name="reset",
                      description="등록한 설정을 초기화합니다. 카테고리 인자를 추가할 시, 해당 카테고리만 초기화합니다.",
                      aliases=["초기화"])
    async def autorole_reset(self, ctx: commands.Context, category="all"):
        if category == "all":
            self.bot.guild_autorole_datas[ctx.guild.name] = {"DEFAULT": {}}
            await ctx.send(content="> 등록된 모든 데이터를 초기화했습니다!")
        else:
            if category in self.bot.guild_autorole_datas[ctx.guild.name].keys():
                self.bot.guild_autorole_datas[ctx.guild.name][category] = {}
                await ctx.send(content=f"> `{category}` 카테고리에 등록된 모든 데이터를 초기화했습니다!")
            else:
                await ctx.send(content=f"> `{category}` 는 등록되어있지 않은 카테고리이므로, 초기화 할 수 없습니다 :(")

    @commands.has_guild_permissions(administrator=True)
    @manage.group(name="log-channel",
                  description="로그 채널을 설정합니다.",
                  aliases=["로그", "log-ch", "lc"])
    async def log_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("> 로그 채널을 설정하는 명령어입니다.\n"
                           + "`라떼야 관리 로그 설정 #채널멘션` 으로 로그채널을 설정하고,\n"
                           + "`라떼야 관리 로그 보기` 로 설정된 로그채널을 확인합니다.")

    @commands.has_guild_permissions(administrator=True)
    @log_group.command(name="set",
                       description="멘션한 채널을 봇의 로그채널을 설정합니다.",
                       aliases=["설정"])
    async def log_set(self, ctx: commands.Context, channel: discord.TextChannel):
        self.bot.guild_configs[ctx.guild.name]["guild_info"]["log_ch"] = channel.id
        await ctx.send(content=f"{channel.mention} 채널을 라떼봇의 로그 채널로 설정했습니다!")


def setup(bot: LatteBot):
    bot.logger.info('[cogs] Management 모듈의 셋업 단계입니다!')
    bot.add_cog(Management(bot))
