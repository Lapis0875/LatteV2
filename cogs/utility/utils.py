import asyncio
import logging
import sys
from typing import List

import discord
from discord.ext import tasks, commands

# import for type hint :
from app import LatteBot


class Utils(commands.Cog):
    bot: LatteBot = None

    status_dict: dict = {discord.Status.online: "온라인",
                         discord.Status.offline: "오프라인",
                         discord.Status.idle: "자리비움",
                         discord.Status.do_not_disturb: "방해금지"}

    supported_report_types: list = ["건의", "버그"]

    num_unicode_emoji: list = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']  # 1~9

    alarms = {}

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot
        self.alarms: dict = {}
        self.bot.logger.info(f"alarms list : {self.alarms}")

    def cog_unload(self):
        self.bot.logger.info(f"alarms list : {self.alarms}")
        for key in self.alarms.keys():
            self.alarms.pop(key).cancel()
        self.bot.logger.info(f"alarms leftovers list : {self.alarms}")

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info('[cogs] Utils 모듈이 준비되었습니다.')
        pass

    # Commands
    @commands.command(name="ping",
                      description="봇의 응답 지연시간을 보여줍니다. 핑퐁!")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"퐁! ({round(self.bot.latency * 1000)}ms)")

    @commands.command(name="user-info",
                      description="호출한 유저의 정보를 보여줍니다. [Can be updated]",
                      aliases=["유저정보", "ui", "userinfo"])
    async def get_user_info(self, ctx: commands.Context, member: discord.Member):
        # Create an Embed which contains member's information
        info_embed: discord.Embed = discord.Embed(
            colour=discord.Colour.blue(),
            author=f'{self.bot.user.name}',
            title=f'{member.display_name}',
            description=f'{member.display_name} 님의 프로필 정보입니다!')
        info_embed.set_thumbnail(url=member.avatar_url)
        info_embed.set_footer(text=f'{ctx.author.name} 님이 요청하셨습니다!', icon_url=ctx.author.avatar_url)

        info_embed.add_field(name="이름", value=f"{member.name}#{member.discriminator}", inline=False)
        info_embed.add_field(name='유저 상태', value=self.status_dict[member.status], inline=True)

        info_embed.add_field(name='Discord 가입 년도', value=member.created_at, inline=False)
        info_embed.add_field(name='서버 참여 날짜', value=member.joined_at, inline=True)

        is_nitro: bool = bool(member.premium_since)
        info_embed.add_field(name='프리미엄(니트로) 여부', value=str(is_nitro), inline=False)
        if is_nitro:
            info_embed.add_field(name='프리미엄 사용 시작 날짜', value=member.premium_since, inline=True)
        """
        info_embed.add_field(name='Hypesquad 여부', value=user_profile.hypesquad, inline=False)
        if user_profile.hypesquad:
            info_embed.add_field(name='소속된 Hypesquad house', value=user_profile.hypesquad_houses, inline=True)
        
        info_embed.add_field(name='메일 인증 사용여부', value=member.verified, inline=False)
        info_embed.add_field(name='2단계 인증 사용여부', value=member.mfa_enabled, inline=True)
        """
        info_embed.add_field(name='모바일 여부', value=member.is_on_mobile(), inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name="user-activity-info",
                      description="호출한 유저의 현재 활동정보를 보여줍니다.",
                      aliases=["유저활동정보", "활동정보", "activityinfo", "uai", "ai", "useractivityinfo"])
    async def get_user_activity(self, ctx: commands.Context, member: discord.Member):
        # Create an Embed which contains member's information
        ac_embed: discord.Embed = discord.Embed(
            title=f"{member.display_name}",
            description=f"{member.display_name} 님의 활동 정보입니다!",
            colour=self.bot.latte_color,
            author=f"{self.bot.user.name}"
        )
        ac_embed.set_thumbnail(url=member.avatar_url)
        ac_embed.set_footer(text=f'{ctx.author.name} 님이 요청하셨습니다!', icon_url=ctx.author.avatar_url)

        if len(member.activities) == 0:
            ac_embed.add_field(name=f'활동 정보가 없습니다!', value='현재 진행중인 활동이 없습니다.', inline=False)
            return await ctx.send(embed=ac_embed)
        else:
            count: int = 1
            for ac in member.activities:
                ac_embed.add_field(name='\u200b', value='\u200b', inline=False)  # 공백 개행을 만든다.
                print(f'ac{count} = {type(ac)}')
                print(f'ac{count}.type = {ac.type}')
                try:
                    if ac.type == discord.ActivityType.playing:
                        ac_embed.add_field(name=f'활동 {count} 이름', value=ac.name, inline=False)
                        ac_embed.add_field(name=f'활동 {count} 유형', value='플레이 중', inline=False)
                        if type(ac) != discord.Game and ac.large_image_url is not None:
                            ac_embed.add_field(name='활동 이미지', value='\u200b', inline=False)
                            ac_embed.set_image(url=ac.large_image_url)
                    elif ac.type == discord.ActivityType.streaming:
                        ac_embed.add_field(name=f'활동 {count} 이름', value=ac.name, inline=False)
                        ac_embed.add_field(name=f'활동 {count} 유형', value='방송 중', inline=False)
                        if type(ac) == discord.Streaming:
                            ac_embed.add_field(name=f'**방송 정보**', value='\u200b', inline=False)
                            ac_embed.add_field(name=f'방송 플랫폼', value=ac.platform, inline=False)
                            if ac.twitch_name is not None:
                                ac_embed.add_field(name=f'트위치 이름', value=ac.twitch_name, inline=True)
                            ac_embed.add_field(name='방송 주소', value=ac.url, inline=False)
                            if ac.game is not None:
                                ac_embed.add_field(name='방송중인 게임', value=ac.game, inline=False)

                    elif ac.type == discord.ActivityType.listening:
                        ac_embed.add_field(name=f'활동 {count} 이름', value=ac.name, inline=False)
                        ac_embed.add_field(name=f'활동 {count} 유형', value='플레이 중', inline=False)

                        ac_embed.add_field(name=f'\u200b', value='WIP', inline=False)

                    elif ac.type == discord.ActivityType.watching:
                        ac_embed.add_field(name=f'활동 {count} 이름', value=ac.name, inline=False)
                        ac_embed.add_field(name=f'활동 {count} 유형', value='시청 중', inline=False)

                        ac_embed.add_field(name=f'\u200b', value='WIP', inline=False)

                    elif ac.type == discord.ActivityType.custom:
                        ac_extra = ''
                        if ac.emoji is not None:
                            ac_extra += ac.emoji.name
                        ac_embed.add_field(name=f'활동 {count} 이름', value=ac_extra + ac.name, inline=False)
                        ac_embed.add_field(name=f'활동 {count} 유형', value='사용자 지정 활동', inline=False)

                    elif ac.type == discord.ActivityType.unknown:
                        ac_embed.add_field(name=f'활동 {count} 이름', value='알 수 없는 활동입니다!', inline=False)
                    else:
                        ac_embed.add_field(name=f'요청하신 사용자의 활동을 파악하지 못했습니다!', value='유효한 활동 유형이 아닙니다 :(', inline=False)
                except Exception as e:
                    ac_embed.add_field(name=f'오류 발생!', value='활동 정보를 불러오지 못했습니다 :(', inline=False)
                    ac_embed.add_field(name=f'오류 내용', value=str(e.with_traceback(e.__traceback__)), inline=False)

                count += 1

        await ctx.send(embed=ac_embed)

    @commands.command(name='server-info',
                      description='명령어가 사용된 서버의 정보를 보여줍니다.',
                      aliases=["서버정보", "si", "serverinfo"])
    async def get_server_info(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        # Create an Embed which contains member's information
        info_embed: discord.Embed = discord.Embed(
            colour=discord.Colour.blue(),
            author=f'{self.bot.user.name}',
            title=f'{guild.name}',
            description=f'{guild.name} 서버 정보입니다!',
            type='rich')
        info_embed.set_thumbnail(url=guild.icon_url)
        info_embed.add_field(name='서버 주인', value=guild.owner.mention, inline=False)
        info_embed.add_field(name='서버 생성 날짜', value=guild.created_at, inline=True)

        await ctx.send(embed=info_embed)

    @commands.command(name='bot-info',
                      description='봇의 정보를 보여줍니다.',
                      aliases=["봇정보", "bi", "botinfo"])
    async def get_bot_info(self, ctx: commands.Context):
        # Create an Embed which contains member's information
        user_count = len(list(filter(lambda u: not u.bot, self.bot.user)))
        info_embed: discord.Embed = discord.Embed(
            colour=self.bot.latte_color,
            author=f'{self.bot.user.name}',
            title='라떼봇 정보',
            description=f'현재 {len(self.bot.guilds)}개의 서버에서 사용중이며,\n{user_count}명의 유저들과 소통중입니다.',
            type='rich')
        info_embed.set_thumbnail(url=self.bot.user.avatar_url)
        info_embed.set_footer(text=f'{ctx.author.name} 님이 요청하셨습니다!', icon_url=ctx.author.avatar_url)

        info_embed.add_field(name="**개발자**", value="sleepylapis#1608")

        import datetime
        bot_created_at: datetime = self.bot.user.created_at
        info_embed.add_field(name='봇 운영 기간',
                             value=f'{bot_created_at.year}년 {bot_created_at.month}월 {bot_created_at.day} ~ 현재')

        await ctx.send(embed=info_embed)

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="vote",
                      description="투표를 생성합니다. 사용 양식은 아래와 같습니다 :\n"
                                  f"`라떼야 관리 투표 투표 기간(~ 시간, 양의 실수) 제목, 투표설명, 항목1, 항목2(, 항목3, ... , 항목9)`\n"
                                  "투표 기간과 제목은 반드시 입력하셔야 하며, 선택지는 2개 이상 9개 이하로 입력하셔야 합니다.",
                      aliases=["투표", "v"])
    async def create_vote(self, ctx: commands.Context, duration: float, *, vote_content: str):
        if type(duration) != float:
            return await ctx.send(content=f"투표 기간은 숫자여야 합니다! 입력하신 투표 기간 : {duration}")
        elif duration <= 0:
            return await ctx.send(content=f"투표 기간은 0 이하의 수가 될 수 없습니다! 입력하신 투표 기간 : {duration}")
        # Process vote_content to title(str), choices(list[str])
        vote_datas: list = vote_content.split(',')
        title: str = vote_datas.pop(0)  # First content from vote_content must be the title
        desc: str = vote_datas.pop(0)  # Second content(which now moved to first) must be the description.
        # logger.info(f'title = {title}')
        # logger.info(f'vote_datas = {vote_datas}')
        choices = vote_datas
        del vote_datas

        choices_count: int = len(choices)

        # Check if the command is used properly
        # If vote has only one choice or no choice:
        if 2 > choices_count or choices_count > 9:
            return await ctx.send(f'투표는 2개 이상 9개 이하의 선택지로 구성되어야 합니다!')
        # If vote does not have a title:
        if title == '':
            return await ctx.send(f'투표 제목 없이는 투표를 진행할 수 없습니다.')

        # Create an Embed which contains informations of this vote:
        vote_embed = discord.Embed(title=f"[투표] {title}", description=desc, color=self.bot.latte_color)

        # Loops for add choices field in vote_embed:
        for num in range(choices_count):
            vote_embed.add_field(name=self.num_unicode_emoji[num], value=choices[num], inline=True)

        vote_embed.add_field(name='게시 일자', value=ctx.message.created_at, inline=False)
        vote_embed.add_field(name='주의사항', value='현재 봇은 투표 결과를 자동으로 집계해주진 않습니다.\n'
                                                '각 문항별 득표수는 해당 문항의 반응 개수 - 1(봇이 남긴 반응)입니다.', inline=False)

        vote_msg: discord.Message = await ctx.send(embed=vote_embed)
        vote_log_embed = discord.Embed(title="투표 게시됨 :", description=f"새 투표가 게시되었습니다!")
        vote_log_embed.add_field(name="**주제 :**", value=title)
        vote_log_embed.add_field(name="**바로가기**", value=vote_msg.jump_url)
        await self.bot.send_log(guild_name=ctx.guild.name, embed=vote_log_embed)

        # Loops for add number reaction in vote_msg:
        for num in range(choices_count):
            await vote_msg.add_reaction(self.num_unicode_emoji[num])

        await asyncio.create_task(self.async_vote_manager(vote_message=vote_msg, contents=choices, timeout=duration))

    async def async_vote_manager(self, vote_message: discord.Message, contents: List[str], timeout: float = 24.0):
        # transfer delay(hour-based, float) to task delay(second-base, int)
        delay: int = int(timeout * 60 * 60)

        vote_result_embed = discord.Embed(
            title=f"**{vote_message.embeds.pop(0).title}** 의 투표 결과입니다!"
        )

        vote_reactions: list = [reaction for reaction in vote_message.reactions if reaction.me]
        vote_result_counts: list = [reaction.count - 1 for reaction in vote_reactions]
        self.bot.logger.info(f"vote_result_counts = {vote_result_counts}")
        str_result = "\n".join(
            [f"{self.num_unicode_emoji[i]} : {vote_result_counts[i]}" for i in range(len(vote_reactions))])

        sorted_vote_counts: list = vote_reactions.copy()
        sorted_vote_counts.sort(reverse=True)
        self.bot.logger.info(f"sorted_vote_counts = {sorted_vote_counts}")
        winner: str = ""
        if sorted_vote_counts.count(sorted_vote_counts[0]) > 1:
            winner_reactions: list = [(reaction, vote_reactions.index(reaction)) for reaction in vote_reactions if
                                      reaction.count == sorted_vote_counts[0]]
            winner = "\n".join([f"{reaction.emoji} : {contents[index]}" for (reaction, index) in winner_reactions])
        else:
            index: int = vote_result_counts.index(sorted_vote_counts[0])
            winner = f"{vote_reactions[index].emoji} : {contents[index]}"

        vote_result_embed.add_field(name="결과", value=winner)

        vote_result_embed.add_field(name="세부 득표 결과", value=str_result)
        # sleep task during delay(seconds)
        await asyncio.sleep(delay)
        await vote_message.channel.send(embed=vote_result_embed)

    @commands.command(name="check-vote",
                      description="현재 진행중인 투표 목록을 확인합니다. [WIP] [NOT_WORKING]",
                      aliases=["vote-check", "cv"])
    async def check_vote(self, ctx: commands.Context):
        pass

    @commands.command(name="invite-url",
                      description="봇을 서버에 초대할 수 있는 링크를 생성합니다.",
                      aliases=["초대", "invite"])
    async def get_invite_url(self, ctx: commands.Context):
        """
        봇 초대링크를 생성, 전송합니다.
        """
        # bot_invite_url: str = discord.utils.oauth_url(client_id=str(self.bot.user.id)).replace("&scope=bot", "&permissions=8&scope=bot")
        bot_invite_url: str = discord.utils.oauth_url(client_id=str(self.bot.user.id)) + "&permissions=8"
        print(f"[test] [get_bot_invite_oauth] bot_invite_url : {bot_invite_url}")
        await ctx.send(f"> 초대 링크입니다! → {bot_invite_url}")

    @commands.command(name="starboard",
                      description="메세지 url을 받아 해당 메세지를 박제합니다.",
                      aliases=["스타보드", "star-board"])
    async def starboard(self, ctx: commands.Context, msg_link: str, channel: discord.TextChannel):
        if "https://discordapp.com/channels/" not in msg_link:
            return await ctx.send(
                "올바르지 않은 링크입니다! 박제하려는 메세지의 링크를 전달해 주세요!\n> 방법 : 박제하려는 메세지에 **우클릭** -> **메세지 링크 복사** 클릭")
        else:
            # https://discordapp.com/channels/server_id/channel_id/message_id -> server_id/channel_id/message_id
            # -> ['server_id','channel_id','message_id']
            msg_data: list = msg_link.replace("https://discordapp.com/channels/", '').split('/')
            captured_guild: discord.Guild = ctx.guild
            captured_ch: discord.TextChannel = captured_guild.get_channel(channel_id=int(msg_data[1]))
            captured_msg: discord.Message = await captured_ch.fetch_message(msg_data[2])

            captured_embed: discord.Embed = discord.Embed(
                title="메세지 박제됨 : ",
                description=captured_msg.content,
                color=self.bot.latte_color
            )
            captured_embed.set_author(name=captured_msg.author.name, icon_url=captured_msg.author.avatar_url)
            captured_embed.add_field(name="바로가기!", value=f"[원본 메세지]({msg_link} '박제된 메세지로 가는 포탈이 생성되었습니다 - 삐릿')")

            await channel.send(embed=captured_embed)

    @commands.command(name="report",
                      description="건의사항이나 버그 내용을 메세지로 받아 개발자들에게 전달합니다. 혹은 메세지 없이 사용해 공식 커뮤니티 제보 채널로 연결합니다.",
                      aliases=["제보"])
    async def report(self, ctx: commands.Context, report_type='', *, report_content: str = ''):
        print(f"{ctx.message.content}")
        print(f"report_type == {report_type}")
        print(f"report_content == {report_content}")

        if report_type=='' and report_content == '':
            await ctx.send(content=f"> 봇 공식 커뮤니티에서 버그를 제보해주세요!" +
                                   f"\n{self.bot.discord_base_invite + self.bot.bug_report_invite}")
        elif report_content != '' and report_type in self.supported_report_types:

            bug_embed = discord.Embed(
                title=f"{ctx.author.name} 님의 제보입니다!"
            )
            bug_embed.add_field(name="제보 유형", value=report_type)
            bug_embed.add_field(name="제보 내용", value=report_content)

            for dev_id in self.bot.dev_ids:
                developer_user: discord.User = self.bot.get_user(dev_id)
                await developer_user.send(embed=bug_embed)

            await ctx.send("> 개발자들에게 해당 사항을 제보했습니다!")
            await ctx.send(content=f"> 추가적인 버그 및 봇 업데이트는 봇 공식 커뮤니티에서 확인해주세요!" +
                                   f"\n{self.bot.discord_base_invite + self.bot.official_community_invite}")

        else:
            await ctx.send("> 잘못된 양식입니다!")


def setup(bot):
    bot.logger.info("[cogs] Utils 모듈의 셋업 단계입니다!")
    bot.add_cog(Utils(bot))
