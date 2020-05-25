import asyncio
import json
import logging
import os
import sys
from typing import Type, List, Dict, Union, Generator, Any

import discord
from discord.ext import commands

# import for type hint :
from app import LatteBot


class Help(commands.Cog):
    bot: LatteBot = None
    cogs = []
    helpBuilder = None

    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot

        # Create HelpCommandBuilder object
        # During bot`s startup logic, this cogs list is not completed yet.
        # So, HelpBuilder object load Cogs again in `on_ready` event.
        # In case of module`s load after finishing bot`s startup, there is no need to load Cogs again.
        self.cogs = [c for c in self.bot.cogs.keys()]
        self.helpBuilder = HelpCommandBuilder(bot=self.bot)
        self.helpBuilder.load_cogs(self.cogs)

    def cog_unload(self):
        del self.helpBuilder

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        self.cogs = [c for c in self.bot.cogs.keys()]
        self.bot.logger.info("[cogs] Help 모듈이 준비되었습니다.")
        # Reload cogs in case of bot`s startup.
        # In startup logic, help command can`t collect some Cogs in it`s internal list.
        # So, it is imporatant to load bot`s cogs into HelpBuilder object in `on_ready`.
        # In case of module reload after bot`s startup, all Cogs are loaded and there is no need to load Cogs again.
        self.helpBuilder.load_cogs(self.cogs)
        pass

    # Commands
    @commands.command(
        name="help",
        description="봇의 도움말 명령어입니다.",
        aliases=["도움말"]
    )
    async def help_command(self, ctx: commands.Context, cog='all'):# Get a list of all legacy_cogs

        # If cog is not specified by the user, we list all cogs and commands
        if cog == 'all':
            await self.helpBuilder.paged_help(ctx=ctx)
            return
        else:
            # If the cog was specified
            # If the cog actually exists.
            if cog in self.cogs:
                await self.helpBuilder.single_help(ctx=ctx, cog_name=cog)
                return
            else:
                # Notify the user of invalid cog and finish the command
                await ctx.send(f'존재하지 않는 모듈입니다. `라떼야 도움말` 명령어로 사용 가능한 모듈과 명령어를 확인해주세요!')
                return


class HelpCommandBuilder:
    cog_names: List[str] = []
    bot: LatteBot = None
    HelpGenerators: Dict[str, Generator[dict, Any, None]] = {}
    logger = logging.getLogger("Latte.HelpCommandBuilder")

    def __init__(self, bot: LatteBot):
        self.bot = bot
        self.logger.setLevel(level=logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        )
        self.logger.addHandler(handler)

    def __del__(self):
        self.logger.info("Deleting HelpBuilder object...")
        pass

    def load_cogs(self, cog_names: List[str]) -> None:
        # DEVELOPER & TEST MODULE SHOULD NOT BE LISTED IN HELP COMMAND
        if "개발자" in cog_names:
            cog_names.pop(cog_names.index("개발자"))
        if "Test" in cog_names:
            cog_names.pop(cog_names.index("Test"))
        self.cog_names = cog_names
        self.collect_help_contents(target_cog='all')

    def collect_help_contents(self, target_cog: str = 'all'):
        if target_cog != 'all':
            self.logger.debug(f"target_cog = {target_cog}")
            try:
                # target_help_gen: Generator[dict, Any, None] = self.retrieve_help_gen(cog_name=target_cog)
                target_help_gen: Generator[dict, Any, None] = self.retrieve_help_gen(cog_name=target_cog)
                self.HelpGenerators.update({target_cog: target_help_gen})
                self.logger.debug(f"successfully collected generator of cog `{target_cog}`")
            except Exception as e:
                self.logger.error(str(e))
        else:
            try:
                self.HelpGenerators.clear()
                for cog in self.cog_names:
                    self.logger.debug(f"looping the cog `{cog}`")
                    target_help_gen: Generator[dict, Any, None] = self.retrieve_help_gen(cog_name=cog)
                    self.HelpGenerators.update({cog: self.retrieve_help_gen(cog_name=cog)})
                    self.logger.debug(f"loop success `{cog}`")
            except Exception as e:
                self.logger.error(str(e))

    async def build_help_embed(self, target_cog: str, author: discord.User) -> discord.Embed:
        print(f"Constructing Help embed for the Cog `{target_cog}`")
        # self.logger.debug(f"Constructing Help embed for the Cog `{target_cog}`")
        help_embed = discord.Embed(
            title='라떼봇',
            description='봇 도움말',
            color=self.bot.latte_color
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar_url)

        # Request Info
        help_embed.set_footer(
            text=f'{author.display_name} 님이 요청하셨어요!',
            icon_url=author.avatar_url
        )

        # Developer Info
        help_embed.add_field(name='개발자', value='Discord : sleepylapis#1608', inline=False)

        # Help content
        print(f"Adding Help content of the Cog `{target_cog}`")
        # self.logger.debug(f"Adding Help content of the Cog `{target_cog}`")
        target_cog_gen: Generator[dict, Any, None] = self.HelpGenerators[target_cog]
        help_embed.add_field(name=f"모듈 이름", value=f"**{target_cog}**")
        print("Getting generator")
        print(list(self.HelpGenerators[target_cog]))
        self.logger.debug(list(self.HelpGenerators[target_cog]))
        for command_content in target_cog_gen:
            print(command_content)
            cmd_name: str = command_content["name"]
            cmd_desc: str = command_content["description"]

            if "aliases" in command_content.keys():
                cmd_desc += command_content['aliases']
            # Add the cog's details to the embed.
            help_embed.add_field(
                name=cmd_name, value=cmd_desc, inline=False
            )

        return help_embed

    def retrieve_help_gen(self, cog_name: str = '', commands_list: List[Type[commands.Command]] = [], indent: int = 0) -> Union[Generator[dict, Any,  None], list, None]:
        # If commands_list is [] and cog_name is not '' -> First function call
        # Else if commands_list is not [] and cog_name is '' -> Recursive inner function call to get information of subcommands
        if commands_list == [] and cog_name != '':
            commands_list = self.bot.get_cog(cog_name).get_commands()
        elif commands_list != [] and cog_name =='':
            # subcommand
            pass
        else:
            return

        # Add command`s information to the variable `content`
        content_list: List[dict] = []
        indent_prefix: str = f"**{'    '*indent}**" if indent!=0 else ""
        for command in commands_list:
            # content = {"name": f"{indent_prefix}이름 : {command.name}", "description": f"{indent_prefix}설명 : {command.description}"}
            content = {"name": f"{command.name}", "description": f"{command.description}"}
            if len(command.aliases) > 0:
                # content.update({"aliases": f"\n{indent_prefix}동의어 : {', '.join(command.aliases)}"})
                content.update({"aliases": f"{', '.join(command.aliases)}"})
            content_list.append(content)
            if type(command) == commands.Group:
                indent+=1
                subcommand_contents: List[dict] = self.retrieve_help_gen(commands_list=command.commands, indent=indent)
                content_list += subcommand_contents
        if indent != 0:
            return content_list
        else:
            def help_page_generator():
                for conmmand_help in content_list:
                    yield conmmand_help

            return help_page_generator()

    def walk_through_subcommands(self, cog_name: str):
        target_cog: commands.Cog = self.bot.get_cog(name=cog_name)
        help_content: List[dict] = []
        for command in target_cog.walk_commands():
            command_help = {
                "name": "이름 : " + command.name,
                "description": "설명 : " + command.description
            }
            if len(command.aliases) > 0:
                command_help["aliases"] = "동의어 : " + ", ".join(command.aliases)


    async def single_help(self, ctx: commands.Context, cog_name: str):
        help_embed = await self.build_help_embed(target_cog=cog_name, author=ctx.author)

        # Send help embed to user/channel
        if self.bot.guild_configs[ctx.guild.name]["modules"]["help"]["use_DM"]:
            help_message: discord.Message = await ctx.author.send(embed=help_embed)
        else:
            help_message: discord.Message = await ctx.send(embed=help_embed)
        await help_message.add_reaction(emoji="❎")

        # Add emoji and check for help message for pagination intend.
        def help_page_delete_check(reaction: discord.Reaction, user: discord.User) -> bool:
            # LEFT Pagination -> True
            return reaction.emoji == '❎' and user.id == ctx.author.id

        while True:
            try:
                reaction, user = await self.bot.wait_for(event="reaction_add", check=help_page_delete_check, timeout=10.0)
                if user.id != ctx.author.id:
                    continue
            except asyncio.TimeoutError:
                return await help_message.clear_reactions()
            else:
                if reaction.emoji == "❎":
                    return await help_message.delete()

    async def paged_help(self, ctx: commands.Context):
        self.logger.info("")
        page: int = 0
        help_msg: discord.Message = await ctx.send(embed=await self.build_help_embed(target_cog=self.cog_names[page], author=ctx.author))
        await help_msg.add_reaction(emoji="❎")
        await help_msg.add_reaction("◀")
        await help_msg.add_reaction("▶")

        # Add emoji and check for help message for pagination intend.
        def help_page_check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (user.id == ctx.author.id) and (reaction.emoji in ['▶', '◀', '❎'])

        while True:
            try:
                self.logger.debug("Checking for `reaction_add` event with a check function `help_page_check` with a delay 10.0")
                reaction, user = await self.bot.wait_for(event="reaction_add", check=help_page_check, timeout=10.0)
                if user.id != ctx.author.id or reaction.message.id != help_msg.id:
                    self.logger.debug("Not a qualified request. Continue checking...")
                    continue
                else:
                    self.logger.debug("Got a qualified request. Start checking pagination..")

            except asyncio.TimeoutError:
                self.logger.info("도움말 시간초과")
                await help_msg.clear_reactions()
                await help_msg.edit(content="도움말 이용시간이 초과되었습니다.")
                return
            else:
                self.logger.info(f"반응 : {reaction.emoji}")
                if reaction.emoji == "❎":
                    self.logger.info("도움말 종료")
                    await help_msg.delete()
                    return
                elif reaction.emoji == "▶":
                    self.logger.info("도움말 페이지 +1")

                    page += 1
                    if page > len(self.cog_names) - 1:
                        page = 0

                    self.logger.debug(f"current page : {page}")
                    await help_msg.edit(embed=await self.build_help_embed(target_cog=self.cog_names[page], author=ctx.author))
                    await help_msg.clear_reactions()
                    await help_msg.add_reaction(emoji="❎")
                    await help_msg.add_reaction(emoji="◀")
                    await help_msg.add_reaction(emoji="▶")
                elif reaction.emoji == "◀":
                    self.logger.info("도움말 페이지 -1")

                    page -= 1
                    if page < 0:
                        page = len(self.cog_names) - 1

                    self.logger.debug(f"current page : {page}")
                    await help_msg.edit(embed=await self.build_help_embed(target_cog=self.cog_names[page], author=ctx.author))
                    await help_msg.clear_reactions()
                    await help_msg.add_reaction(emoji="❎")
                    await help_msg.add_reaction(emoji="◀")
                    await help_msg.add_reaction(emoji="▶")


class HelpDocParser:
    __help_doc_dir: str = ''
    __helpGenerators = []

    def __init__(self, help_doc_dir: str = "resources/help"):
        self.__help_doc_dir = help_doc_dir

    def parse_help_docs(self):
        help_docs: List[str] = os.listdir(self.__help_doc_dir)
        for help_doc in help_docs:
            if ".json" in help_doc:
                with open(file=f"resources/help/{help_doc}") as help_doc_file:
                    help_content: dict = json.load(fp=help_doc_file)





def setup(bot):
    bot.logger.info("[cogs] Help 모듈의 셋업 단계입니다!")
    bot.add_cog(Help(bot))
