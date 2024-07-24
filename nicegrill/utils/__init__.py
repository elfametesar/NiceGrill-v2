import re
from typing import Coroutine
from nicegrill import on

import asyncio
import httpx
import time
import sys

class ProcessManager:

    _process_list = {}

    @on(pattern="input")
    async def input_data(client, message):
        """
        Sends input data to a running process.

        Usage:
        .input <data>       # Sends the given data as input to the process associated with the replied-to message
        """
        if not message.reply_to_text:
            await message.delete()
            return

        process = ProcessManager._process_list.get(message.reply_to_text.id)
        if not message.raw_args:
            await message.delete()
            return

        if process:
            stdin = getattr(process, "stdin", sys.stdin) or sys.stdin

            try:
                stdin.write(message.raw_args)
            except AssertionError:
                stdin.write((message.raw_args + "\n").encode())

        await message.delete()

    def add_process(message_id: int, process: asyncio.Task | asyncio.subprocess.Process):

        ProcessManager._process_list[message_id] = process

        if isinstance(process, asyncio.Task):
            process.add_done_callback(lambda task: ProcessManager._process_list.pop(message_id, None))

    def remove_process(process_id: int):
        process = ProcessManager._process_list.pop(process_id, False)

        try:
            process.kill()
            return True
        except ProcessLookupError:
            return False
        except Exception:
            return False

    @on(pattern="kill")
    async def kill_process(client, message):
        """
        Kills a running process that was initiated by a command.

        Usage:
        Reply with .kill     # Kills the process associated with the replied-to message
        """
        if not message.reply_to_text:
            await message.edit("<i>What process am I to kill? Reply to it.</i>")
            return

        if process := ProcessManager._process_list.get(message.reply_to_text.id):
            if hasattr(process, "cancel"):
                process.cancel()
            elif hasattr(process, "kill"):
                process.kill()
            elif hasattr(process, "stdin") and process.stdin:
                process.stdin.write("exit")

            ProcessManager._process_list.pop(message.reply_to_text.id)
            await message.edit("<i>Successfully killed</i>")
        else:
            await message.edit("<i>No process found in message</i>")
    
    def find_process(process_id: int):
        return ProcessManager._process_list.get(process_id)


async def timeout(
    timeout: int,
    func: Coroutine,
    keepalive: bool = False,
    *args, **kwargs
):
    task = asyncio.create_task(func(*args, **kwargs))
    start = time.time()

    while not task.done():
        await asyncio.sleep(0)

        if time.time() - start >= timeout:
            if not keepalive:
                task.cancel()
                break
            else:
                break
    else:
        return task.result()


async def up_to_bin(data: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            url="https://0x0.st",
            files={
                "file": (
                    "log", data
                )
            }
        )

        return response

async def get_bin_url(url: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(
            url=url
        )

        return response

async def humanize(data, time=False):
    hit_limit = 1024 if not time else 60
    magnitudes = ("bytes", "Kb", "Mb", "Gb", "Tb", "Pb") if not time \
        else ("seconds", "minutes", "hours", "days", "months", "years")

    m = 0
    while data > hit_limit and m < len(magnitudes):
        data /= hit_limit
        m += 1

    return f"{data:.2f} {magnitudes[m]}" if not time else f"{int(data)} {magnitudes[m]}"


async def get_user(user, client):
    if user.isdigit():
        user = int(user)

    try:
        user = await client.get_entity(user)

        if not hasattr(user, "first_name"):
            raise Exception
        else:
            return user

    except Exception:
        return False

def parse_kwargs(command: str, defaults: dict = {}):
    for match in re.finditer(pattern="(\w+)=([\",\w]+)", string=command, flags=re.I):
        key = match.group(1)
        value = eval(match.group(2))

        defaults[key] = value
        command = command.replace(match.group(1) + "=", "") \
                          .replace(match.group(2), "")

    return command.strip(), defaults