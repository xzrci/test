import os
import shutil
import subprocess
import sys

import requests
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.misc import modules_help, prefix
from utils.scripts import restart
from utils.db import db


BASE_PATH = os.path.abspath(os.getcwd())
CATEGORIES = [
    "ai",
    "dl",
    "admin",
    "anime",
    "fun",
    "images",
    "info",
    "misc",
    "music",
    "news",
    "paste",
    "rev",
    "tts",
    "utils",
]


@Client.on_message(filters.command(["loadmod", "lm"], prefix) & filters.me)
async def loadmod(_, message: Message):
    if (
        not (
            message.reply_to_message
            and message.reply_to_message.document
            and message.reply_to_message.document.file_name.endswith(".py")
        )
        and len(message.command) == 1
    ):
        await message.edit("<b>Specify module to download</b>")
        return

    if len(message.command) > 1:
        url = message.command[1].lower()

        if url.startswith(
            "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/"
        ):
            module_name = url.split("/")[-1].split(".")[0]
        elif "." not in url:
            module_name = url.lower()
            with open("modules/full.txt", "r") as f:
                modules_dict = {
                    line.split("/")[-1].split()[0]: line.strip() for line in f
                }
            if module_name in modules_dict:
                url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{modules_dict[module_name]}.py"
            else:
                await message.edit(
                    f"<b>Module <code>{module_name}</code> is not found</b>"
                )
                return
        else:
            module_name = url.split("/")[-1].split(".")[0]

        resp = requests.get(url)
        if not resp.ok:
            await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")
            return

        if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
            os.mkdir(f"{BASE_PATH}/modules/custom_modules")

        with open(f"./modules/custom_modules/{module_name}.py", "wb") as f:
            f.write(resp.content)
    else:
        file_name = await message.reply_to_message.download()
        module_name = message.reply_to_message.document.file_name[:-3]
        os.rename(file_name, f"./modules/custom_modules/{module_name}.py")

    await message.edit(
        f"<b>The module <code>{module_name}</code> is loaded!\nRestarting...</b>"
    )
    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "restart",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )
    restart()


@Client.on_message(filters.command(["unloadmod", "ulm"], prefix) & filters.me)
async def unload_mods(_, message: Message):
    if len(message.command) <= 1:
        return

    module_name = message.command[1].lower()

    if module_name.startswith(
        "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/"
    ):
        module_name = module_name.split("/")[-1].split(".")[0]

    if os.path.exists(f"{BASE_PATH}/modules/custom_modules/{module_name}.py"):
        os.remove(f"{BASE_PATH}/modules/custom_modules/{module_name}.py")
        if module_name == "musicbot":
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "requirements.txt"],
                cwd=f"{BASE_PATH}/musicbot",
            )
            shutil.rmtree(f"{BASE_PATH}/musicbot")
        await message.edit(
            f"<b>The module <code>{module_name}</code> removed!\nRestarting...</b>"
        )
        db.set(
            "core.updater",
            "restart_info",
            {
                "type": "restart",
                "chat_id": message.chat.id,
                "message_id": message.id,
            },
        )
        restart()
    elif os.path.exists(f"{BASE_PATH}/modules/{module_name}.py"):
        await message.edit(
            "<b>It is forbidden to remove built-in modules, it will disrupt the updater</b>"
        )
    else:
        await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")


@Client.on_message(filters.command(["loadallmods", "lmall"], prefix) & filters.me)
async def load_all_mods(_, message: Message):
    await message.edit("<b>Fetching info...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        os.mkdir(f"{BASE_PATH}/modules/custom_modules")

    with open("modules/full.txt", "r") as f:
        modules_list = f.read().splitlines()

    await message.edit("<b>Loading modules...</b>")
    for module_name in modules_list:
        url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{module_name}.py"
        resp = requests.get(url)
        if not resp.ok:
            continue
        with open(
            f"./modules/custom_modules/{module_name.split('/')[1]}.py", "wb"
        ) as f:
            f.write(resp.content)

    await message.edit(
        f"<b>Successfully loaded new modules: {len(modules_list)}\nRestarting...</b>",
    )
    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "restart",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )
    restart()


@Client.on_message(filters.command(["unloadallmods", "ulmall"], prefix) & filters.me)
async def unload_all_mods(_, message: Message):
    await message.edit("<b>Fetching info...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        return await message.edit("<b>You don't have any modules installed</b>")
    shutil.rmtree(f"{BASE_PATH}/modules/custom_modules")
    await message.edit("<b>Successfully unloaded all modules!\nRestarting...</b>")

    db.set(
        "core.updater",
        "restart_info",
        {
            "type": "restart",
            "chat_id": message.chat.id,
            "message_id": message.id,
        },
    )
    restart()


@Client.on_message(filters.command(["updateallmods"], prefix) & filters.me)
async def updateallmods(_, message: Message):
    await message.edit("<b>Updating modules...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        os.mkdir(f"{BASE_PATH}/modules/custom_modules")

    modules_installed = list(os.walk("modules/custom_modules"))[0][2]

    if not modules_installed:
        return await message.edit("<b>You don't have any modules installed</b>")

    for module_name in modules_installed:
        if not module_name.endswith(".py"):
            continue

        with open("modules/full.txt", "r") as f:
            modules_dict = {line.split("/")[-1].split()[0]: line.strip() for line in f}
        if module_name in modules_dict:
            resp = requests.get(
                f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{modules_dict[module_name]}.py"
            )
            if not resp.ok:
                modules_installed.remove(module_name)
                continue

            with open(f"./modules/custom_modules/{module_name}", "wb") as f:
                f.write(resp.content)

    await message.edit(f"<b>Successfully updated {len(modules_installed)} modules</b>")


modules_help["loader"] = {
    "loadmod [module_name]*": "Download module.\n"
    "Only modules from the official custom_modules repository and proven "
    "modules whose hashes are in modules_hashes.txt are supported",
    "unloadmod [module_name]*": "Delete module",
    "modhash [link]*": "Get module hash by link",
    "loadallmods": "Load all custom modules (use it at your own risk)",
    "unloadallmods": "Unload all custom modules",
    "updateallmods": "Update all custom modules"
    "\n\n* - required argument"
    "\n <b>short cmds:</b>"
    "\n loadmod - lm"
    "\n unloadmod - ulm"
    "\n modhash - mh"
    "\n loadallmods - lmall"
    "\n unloadallmods - ulmall",
}
