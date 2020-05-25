import json
import logging
from typing import List, Tuple

import aiohttp


import discord
from discord.ext import commands
from cogs import help as help_py

from core.LatteBot import LatteBot

class NaverSearch:
    client_id: str = ""
    token: str = ""
    # request url base.
    # supported search types : [
    #   blog, -> https://developers.naver.com/docs/search/blog
    #   news, -> https://developers.naver.com/docs/search/news
    #   book, -> https://developers.naver.com/docs/search/book
    #   adult, -> https://developers.naver.com/docs/search/adult
    #   encyc, -> https://developers.naver.com/docs/search/encyclopedia
    #   movie, -> https://developers.naver.com/docs/search/movie
    #   cafearticle, -> https://developers.naver.com/docs/search/cafearticle
    #   kin, -> https://developers.naver.com/docs/search/kin
    #   local, -> https://developers.naver.com/docs/search/local
    #   webkr, -> https://developers.naver.com/docs/search/web
    #   image, -> https://developers.naver.com/docs/search/image
    #   shop, -> https://developers.naver.com/docs/search/shopping
    #   doc -> https://developers.naver.com/docs/search/doc
    # ]
    supported_categories: List[str] = [
            "blog",
            "news",
            "book",
            "book_adv",
            "adult",
            "encyc",
            "movie",
            "cafearticle",
            "kin",
            "local",
            "webkr",
            "image",
            "shop",
            "doc"
        ]
    request_url_base: str = "https://openapi.naver.com/v1/search"
    logger: logging.Logger = logging.getLogger("Latte.NaverSearch")

    def __init__(self, client_id: str, token: str):
        self.client_id = client_id
        self.token = token

    async def search(self, category: str, response_format: str = "json", *query: str) -> dict:
        if response_format not in ["json", "xml"]:
            return {
                "result": "Invalid Response Format",
                "content": {}
            }
        if category not in self.supported_categories:
            return {
                "result": "Invalid Search Category",
                "content": {}
            }

        if category == "book_adv" and response_format == "json":
            return {
                "result": "Seach Category `book_adv` does not support `json` format",
                "content": {}
            }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.request_url_base}/{category}.{response_format}?query={''.join(query)}") as response:
                content_str: str = await response.text(encoding="utf-8")
                content: dict = json.loads(s=content_str)
                return {
                    "result": "Success",
                    "content": content
                }


class GoogleSearch:
    def __init__(self):
        pass


class SearchAPI(commands.Cog):
    def __init__(self, bot: LatteBot):
        self.bot: LatteBot = bot
        self.naverSearch = NaverSearch(
            client_id=bot.bot_config["api"]["naver-search"]["client_id"],
            token=bot.bot_config["api"]["naver-search"]["token"]
        )
        self.googleSearch = GoogleSearch()
        self.bot.logger.info("[cogs] SearchAPI 모듈이 로드되었습니다!")

    def cog_unload(self):
        self.bot.logger.info("[cogs] SearchAPI 모듈이 언로드되었습니다!")

    @commands.group(
        name="search",
        description="검색엔진 API를 활용해 검색 결과를 반환합니다.",
        aliases=["검색"]
    )
    async def search(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            return

    @search.command(
        name="naver",
        description="네이버 검색엔진 API를 활용해 검색 결과를 반환합니다.",
        aliases=["네이버"]
    )
    async def search_naver(self, ctx: commands.Context, category: str, *query: str):
        result: dict = await self.naverSearch.search(category=category, response_format="json")
        if result["result"] == "Success":
            response_data: dict = result["content"]




class Parser(commands.Cog):
    bot: LatteBot = None

    def __init__(self, bot: LatteBot):
        self.bot = bot
        self.bot.logger.info("[cogs] Parser 모듈이 로드되었습니다!")

    def cog_unload(self):
        self.bot.logger.info("[cogs] Parser 모듈이 언로드되었습니다!")

    @commands.is_owner()
    @commands.command(name="도움말파싱",
                      description="파일 기반 도움말 체계를 위한, 명령어 및 모듈 정보를 .json 파일에 저장하는 명령어입니다.",
                      aliases=["help-parse", "parser"])
    async def help_parse(self, ctx: commands.Context):
        await ctx.send(content="도움말v2에 쓰일 명령어의 정보들을 파싱합니다...")
        parsed_content: dict = {}
        help_cog: 'help_py.Help' = self.bot.get_cog("Help")
        if help_cog is not None:
            helpBuilder: 'help_py.HelpCommandBuilder' = help_cog.helpBuilder
            if helpBuilder is not None:
                helpBuilder.load_cogs([c for c in self.bot.cogs.keys()])
                for (cog_name, HelpGenerator) in helpBuilder.HelpGenerators.items():
                    parsed_content[cog_name] = {}
                    for command_content in HelpGenerator:
                        parsed_content[cog_name][command_content["name"]] = {
                            "name": command_content["name"],
                            "desc": command_content["description"]
                        }
                        try:
                            parsed_content[cog_name][command_content["name"]].update(
                                {"aliases": command_content["aliases"]})
                        except KeyError:
                            continue
                with open(file="resources/help/help_raw.json", mode="wt", encoding="utf-8") as help_raw_file:
                    import json
                    json.dump(obj=parsed_content, fp=help_raw_file, indent=4, ensure_ascii=False)
                await ctx.send(content="도움말 정보를 성공적으로 파싱했습니다! ==> resources/help/help_raw.json")
            else:
                await ctx.send(content="도움말 모듈 내부의 HelpBuilder 오브젝트가 생성되지 않았습니다 :(")
                self.bot.logger.error(msg="[cogs] [Parser] HelpBuilder object in cogs.help module is not initialied :(")
        else:
            await ctx.send(content="도움말 모듈이 로드되지 않아 실행이 불가합니다 :(")
            self.bot.logger.error(msg="[cogs] [Parser] cogs.help module is not loaded :(")


def setup(bot: LatteBot):
    bot.logger.info("[cogs] Parser 모듈의 셋업 단계입니다!")
    bot.add_cog(Parser(bot))
