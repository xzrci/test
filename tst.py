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
        url = message.command[1]
        module_name = url.split("/")[-1].split(".")[0]
        resp = requests.get(url)
        if not resp.ok:
            await message.edit(f"<b>Failed to download module: <code>{url}</code></b>")
            return

        os.makedirs(f"{BASE_PATH}/modules/custom_modules", exist_ok=True)
        with open(f"./modules/custom_modules/{module_name}.py", "wb") as f:
            f.write(resp.content)
    else:
        file_name = await message.reply_to_message.download()
        module_name = message.reply_to_message.document.file_name[:-3]
        os.makedirs(f"{BASE_PATH}/modules/custom_modules", exist_ok=True)
        shutil.move(file_name, f"./modules/custom_modules/{module_name}.py")

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

    if os.path.exists(f"{BASE_PATH}/modules/custom_modules/{module_name}.py"):
        os.remove(f"{BASE_PATH}/modules/custom_modules/{module_name}.py")
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
    else:
        await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")


@Client.on_message(filters.command(["loadallmods", "lmall"], prefix) & filters.me)
async def load_all_mods(_, message: Message):
    await message.edit("<b>Fetching module list...</b>")
    os.makedirs(f"{BASE_PATH}/modules/custom_modules", exist_ok=True)

    with open("modules/full.txt", "r") as f:
        modules_list = f.read().splitlines()

    await message.edit("<b>Loading modules...</b>")
    for module_name in modules_list:
        url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{module_name}.py"
        resp = requests.get(url)
        if resp.ok:
            with open(
                f"./modules/custom_modules/{module_name.split('/')[1]}.py", "wb"
            ) as f:
                f.write(resp.content)

    await message.edit(
        f"<b>Successfully loaded {len(modules_list)} modules. Restarting...</b>"
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
    os.makedirs(f"{BASE_PATH}/modules/custom_modules", exist_ok=True)
    shutil.rmtree(f"{BASE_PATH}/modules/custom_modules")
    await message.edit("<b>All custom modules removed! Restarting...</b>")

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


modules_help["loader"] = {
    "loadmod [module_name or URL]*": "Download and load a module",
    "unloadmod [module_name]*": "Delete a loaded module",
    "loadallmods": "Load all modules listed in modules/full.txt",
    "unloadallmods": "Remove all custom modules",
}
