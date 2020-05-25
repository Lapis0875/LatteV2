"""
Bot Codes
"""
import asyncio
import json
import logging
import os
import random
import sys
import traceback
from typing import Union, List, Callable, Any, NoReturn, Optional, Tuple
from functools import wraps

import discord
from discord.ext import commands


# Decorator for functions which loops through Cogs dir.
def loop_through_cogs():

    def decorator_func(original_func):

        @wraps(original_func)
        def wrapped_func(self, directory: str, target_cog_name: str = "all"):
            if target_cog_name == "all":
                # fine all files in directory `dir`
                print(f"type of directory = {type(directory)}")
                print(f"directory = {directory}")
                file_list: List[str] = os.listdir(directory)
                for filename in file_list:
                    if "__" in filename:
                        continue
                    if ".py" in filename:
                        cog_style_dir: str = directory[2:].replace('/', '.')
                        cog_name: str = f"{cog_style_dir}.{filename[0:-3]}"
                        try:
                            original_func(self, cog_name)
                        except commands.errors.ExtensionNotFound as e:
                            print(f"Cannot find the Cog `{cog_name}`")
                            # self.logger.exception(msg=f"Cannot find the Cog `{cog_name}` ",
                            #                       exc_info=e)

                        except commands.errors.ExtensionNotLoaded as e:
                            print(f"The Cog `{cog_name}` is not loaded.")
                            # self.logger.exception(msg=f"The Cog `{cog_name}` is not loaded.",
                            #                       exc_info=e)

                        except commands.errors.ExtensionAlreadyLoaded as e:
                            print(f"The Cog `{cog_name}` is already loaded.")
                            # self.logger.exception(msg=f"The Cog `{cog_name}` is already loaded.",
                            #                       exc_info=e)

                        except commands.errors.NoEntryPointError as e:
                            print(f"The Cog `{cog_name}` does not have setup() function.")
                            # self.logger.exception(msg=f"The Cog `{cog_name}` does not have setup() function.",
                            #                       exc_info=e)

                        except commands.errors.ExtensionFailed as e:
                            print(f"An Exception occured during executing setup() function of the Cog `{cog_name}`.")
                            # self.logger.exception(msg=f"An Exception occured during executing setup() function of the Cog `{cog_name}`.",
                            #                       exc_info=e)

                        except Exception as e:
                            print(f"Unexpected Exception occured during loading the Cog `{cog_name}`.")
                            # self.logger.exception(msg=f"Unexpected Exception occured during loading the Cog `{cog_name}`.",
                            #                       exc_info=e)

                    else:
                        inside_directory = f"{directory}/{filename}"
                        wrapped_func(self, directory=inside_directory)
            else:
                original_func(self, target_cog_name)

        return wrapped_func
    return decorator_func


class LatteBot(commands.Bot):
    # Bot Config Variables
    bot_config_dir: str = "./config.json"
    guild_configs_dir: str = ""
    module_dir: str = ""
    lang_base_dir: str = "resources/lang"

    bot_config: dict = {}
    guild_configs = {}
    guild_autorole_datas = {}
    translations: dict = {}

    # Bot Condition Variables
    __do_reboot: bool = False

    @property
    def do_reboot(self):
        return self.__do_reboot

    @do_reboot.setter
    def do_reboot(self, value: bool):
        self.__do_reboot = value

    test_mode: bool = False

    # Bot Information values
    dev_ids: list = [280855156608860160]
    discord_base_invite: str = "https://discord.gg/"
    official_community_invite: str = "duYnk96"
    bug_report_invite: str = "t6vVSYX"
    latte_color: discord.Colour = discord.Color.from_rgb(236, 202, 179)

    # logger
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)

    def __init__(self, *args, **kwargs):
        # Bot Config Variables
        """self.guild_configs: dict = {}
        self.translations: dict = {}
        self.dev_ids: list = [280855156608860160]
        self.do_reboot: bool = False"""

        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        if self.test_mode:
            token = self.bot_config["test-token"]
        else:
            token = self.bot_config["token"]
        super().run(token)


    """
    [ Settings Management ]
    Using files and database, bot manages settings of many servers
    """

    def settings_load(self):
        """
        Loads setting files(config.txt, server_setting/*.json)
        """
        # Load bot`s config
        self.logger.info("Loading bot`s config")
        self.bot_config = self.load_config(dir=self.bot_config_dir)

        if self.bot_config["token"] == "":
            print(f"[init] > {self.bot_config_dir}를 불러왔으나, token이 비어있네요 :(")
            token = input("[init] > discord application의 bot token을 입력해 주세요! : ")
            self.bot_config["token"] = token

        self.guild_configs_dir = self.bot_config["guild_config_dir"]
        self.module_dir = self.bot_config["cogs_dir"]

        # Load guilds` configs
        self.logger.info("Loading guilds` config")
        guild_configs_list: list = os.listdir(self.guild_configs_dir)
        for guild_config_dir in guild_configs_list:
            if guild_config_dir == "BASE-SERVER-CONFIG":
                continue
            print(f"[init] > found a guild config : {guild_config_dir}")
            guild_config: dict = self.load_config(dir=f"{self.guild_configs_dir}/{guild_config_dir}/server.json")
            self.guild_configs[guild_config["guild_info"]["name"]] = guild_config

        # Load Cogs
        self.logger.info("Loading bot`s Cogs")
        self.load_cogs(directory=self.module_dir)

    def settings_save(self):
        """
        save settings datas to the file.
        """

        # 봇 설정파일 저장
        print(f"[settings_save] > {self.bot_config_dir}를 저장합니다...")
        bot_config_save_result, error = self.save_config(content=self.bot_config, dir=self.bot_config_dir)
        if not bot_config_save_result and error is not None:
            print(f"[settings_save] > {self.bot_config_dir}를 저장하는데 실패했습니다! 심각한 오류 발생!!")
            return "**config.txt** 파일을 저장하는데 실패했습니다!", error

        # 서버별 설정파일 저장
        for guild_name in self.guild_configs.keys():
            if guild_name == "SERVER_NAME":
                continue
            guild_config_save_result, error = self.save_config(content=self.guild_configs[guild_name], dir=f"./configs/{guild_name}/server.json")
            if not guild_config_save_result and error is not None:
                print(f"[settings_save] > {guild_name} 서버의 설정파일을 저장하는데 실패했습니다! 심각한 오류 발생!!")
                return f"**config/{guild_name}/server.json** 파일을 저장하는데 실패했습니다!", error

        # 만약 봇이 꺼지면서 실행된것이 아닌, 명령어로 실행된 경우라면 init() 함수를 사용해 설정을 다시 불러온다.
        if not self.is_closed():
            print("[settings_save] > 새롭게 저장한 설정들을 봇의 전체 설정에 반영합니다.")
            self.settings_load()
            print("[settings_save] > 설정 불러오기에 성공했습니다!")

        return "설정 저장에 성공했습니다!", None

    def load_config(self, dir: str) -> Union[dict, NoReturn]:
        print(f"[load_config] > {dir}를 불러옵니다.")
        try:
            with open(file=dir, mode="rt", encoding="utf-8") as file:
                config: dict = json.load(fp=file)
                print(f"[load_config] > {dir} 를 성공적으로 불러왔습니다!")
                return config
        except FileNotFoundError as e:
            print(f"[load_config] > {dir}이 존재하지 않습니다!\n{e}")
            raise FileNotFoundError(f"{dir}이 존재하지 않습니다!")
        except Exception as e:
            print(f"[load_config] > {dir}을 여는 도중 오류가 발생했습니다!\n{e}")
            raise Exception(f"{dir}을 여는 도중 오류가 발생했습니다!")

    def parse_guild_configs(self, storage: dict, filename: str) -> dict:
        for guild_name in os.listdir(self.guild_configs_dir):
            if guild_name == "BASE-SERVER-CONFIG":
                continue
            try:
                storage[guild_name] = self.load_config(dir=f"{self.guild_configs_dir}/{guild_name}/{filename}")
            except FileNotFoundError as e:
                self.logger.error(f"[Latte] {guild_name}/{filename} 파일을 찾을 수 없습니다!")
                self.parse_traceback(exception=e)
                self.logger.error(f"{guild_name}/{filename} 파일을 새로 생성합니다...")

                with open(file=f"{self.guild_configs_dir}/{guild_name}/{filename}", mode="wt", encoding="utf-8") as config_file:
                    config_file.write("{}")

                storage[guild_name] = {}
            except Exception as e:
                self.logger.error("오류 발생!!!")
                self.parse_traceback(exception=e)

        return storage

    def save_config(self, content: dict, dir: str) -> Tuple[bool, Optional[Exception]]:
        print(f"[save_config] > {dir}에 전달받은 딕셔너리를 저장합니다.")
        print(f"[save_config] > 전달받은 딕셔너리 :\n\n{json.dumps(obj=content, indent=4, ensure_ascii=False)}\n\n")
        try:
            if not os.path.exists(dir):
                os.mkdir(dir.replace("server.json", ''))
            # Your error handling goes here
            with open(file=dir, mode="wt", encoding="utf-8") as file:
                json.dump(obj=content, fp=file, indent=4, ensure_ascii=False)
                print(f"[save_config] > {dir}을 성공적으로 저장했습니다!")
                return True, None

        except Exception as e:
            print(f"[save_config] > An Exception has been occured!")
            self.parse_traceback(exception=e)
            return False, e

    @loop_through_cogs()
    def load_cogs(self, cog_name: str):
        self.load_extension(cog_name)

    def clear_datas(self, dir: str) -> [str, Union[None, Exception]]:
        if not dir.endswith('/'):
            dir += '/'
        data_list: list = os.listdir(dir)
        if len(data_list) == 0:
            return "captcha directory is already clear!", None
        try:
            for data in data_list:
                os.remove(dir + data)
            return "captcha directory is successfully cleared!", None
        except Exception as e:
            self.parse_traceback(exception=e)
            return f"found an exception during clearing directory {dir}", e

    async def send_log(self, guild_name: str, embed: discord.Embed):
        log_ch_id: int = self.guild_configs[guild_name]["guild_info"]["log_ch"]
        if log_ch_id != 0:
            await self.get_channel(log_ch_id).send(embed=embed)

    def parse_traceback(self, exception: Exception) -> NoReturn:
        traceback_list = traceback.extract_tb(exception.__traceback__).format()
        for tb in traceback_list:
            self.logger.error(tb)

    def check_reboot(self):
        # if reboot mode on, run reboot code
        if self.is_closed():
            print("[check_reboot] > 봇이 종료되었습니다!")
            if self.do_reboot:
                print("[check_reboot] > 봇 재시작 명령이 들어와 봇을 재시작합니다!")
                excutable = sys.executable
                args = sys.argv[:]
                args.insert(0, excutable)
                os.execv(sys.executable, args)
        else:
            print("[check_reboot] > 봇이 종료되지 않았습니다!")

    async def presence_loop(self):
        presence_msg_list: list = ["'라떼야 도움말' 로 라떼봇을 이용해보세요!",
                                   "라떼봇은 라떼를 좋아하는 개발자가 개발했습니다 :P",
                                   "라떼봇 개발자 : sleepylapis#1608",
                                   "라떼봇은 현재 개발중입니다!",
                                   "버그 제보는 언제나 환영이에요 :D"]
        await self.wait_until_ready()
        while not self.is_closed():
            msg: str = random.choice(presence_msg_list)
            # 봇이 플레이중인 게임을 설정할 수 있습니다.
            await self.change_presence(
                status=discord.Status.online, activity=discord.Game(name=msg, type=1)
            )
            await asyncio.sleep(30)
