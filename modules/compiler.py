#    This file is part of NiceGrill.
#    NiceGrill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    NiceGrill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with NiceGrill.  If not, see <https://www.gnu.org/licenses/>.

import time
from database import settingsdb as settings
from telethon.tl.patched import Message
from main import run, event_watcher
from meval import meval

import logging
import utils
import io
import os
import sys
import html
import asyncio
import traceback

class Compiler:
    processes = {}
    shell_mode = None
    terminal_executable = None
    shell_mode_executable = None

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)

    async def process_done(message, res, template, exit_code):
        if not (res := res.strip()):
            exit_code = exit_code.strip()

        if len(res) + len(template) < 4000:
            await message.edit(
                template +
                f"<code>{res}</code>" +
                exit_code
            )
        else:
            await utils.stream(
                message=message,
                res=res,
                template=template,
                exit_code=exit_code
            )

    @run(command="term")
    async def terminal(message: Message, client):
        cmd = message.args.strip()

        if not Compiler.terminal_executable:
            Compiler.terminal_executable = await Compiler.find_shell()

        proc = await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            executable=Compiler.terminal_executable
        )

        res = ""
        template = f"""<b>⬤ Input:</b>

<code>{html.escape(cmd)}</code>

<b>⬤ Output:</b>

"""
        exit_code = """

<code>Process exited with code {}</code>
"""

        if not message.cmd:
            template = ""
            exit_code = ""
        else:
            await message.edit(template)

        await asyncio.sleep(.1)

        Compiler.processes.update({message.id: proc})

        flood_control = 0
        while line := (await proc.stdout.readline()).decode():
            res += html.escape(line)

            if not line.strip():
                continue

            if proc.returncode is not None:
                res += html.escape((await proc.stdout.read()).decode())

                if not (res := res.strip()):
                    exit_code = exit_code.strip()

                exit_code = exit_code.format(proc.returncode)

                if message.id in Compiler.processes:
                    del Compiler.processes[message.id]

                await Compiler.process_done(
                    message,
                    res,
                    template,
                    exit_code
                )
                return

            if flood_control < 20:
                flood_control += 1
                continue
            else:
                flood_control = 1
                await asyncio.sleep(2)

            try:
                if len(res) < 4000:
                    await message.edit(
                        template +
                        f"<code>{res}</code>"
                    )
                else:
                    await message.edit(
                        template +
                        f"<code>{res[-4000:]}</code>"
                    )
            except:
                pass

        log_url = f"""

<b>For full log:</b> {(await utils.full_log(res)).text}
""" if len(res) > 4000 else ""

        if message.id in Compiler.processes:
            exit_code = exit_code.format(
                proc.returncode if proc.returncode is not None else 0
            )
            del Compiler.processes[message.id]
        else:
            exit_code = exit_code.format(-9)

        if not res:
            exit_code = exit_code.strip()

        await message.edit(
            template +
            f"<code>{res[-4000:]}</code>" +
            exit_code +
            log_url
        )

    @run(command="cpp")
    async def cpp_compiler(message, client):
        """Compiles a given C++ code"""
        code = message.args

        if not (code := code.strip()):
            if (reply := message.replied) is None:
                await message.edit("<i>No c++ code provided</i>")
                return
            else:
                code = html.escape(reply.message.strip())

        if os.path.exists("/usr/bin/c++"):
            compiler = "/usr/bin/c++"
        elif os.path.exists("/usr/bin/g++"):
            compiler = "/usr/bin/g++"
        else:
            await message.edit(
                "<b>No compilers found. Install clang or gnu-clang and make sure they are in path /usr/bin.</b>")
            return

        if "int main(" not in code:
            code = """
#include <iostream>
#include <vector>

using namespace std;

int main(int argc, char** argv) {{
    {}
}}
""".format("\n    ".join(code.splitlines()))

        with open("main.cpp", "w+") as fd:
            fd.write(code)

        proc = await asyncio.create_subprocess_shell(
                cmd=f"{compiler} -std=c++20 main.cpp -o main && ./main",
                shell=True,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.PIPE
        )

        template = """<b>◍ Input:</b>

<code>{}</code>

<b>◍ Output:</b>

""".format(html.escape(message.args.strip()))

        await message.edit(template)

        Compiler.processes.update({message.id: proc})
        
        res = ""
        while line := (await proc.stdout.readline()).decode():
            res += line

        exit_code = f"""

<code>Process exited with code {proc.returncode}</code>"""

        if not (res := res.strip()):
            exit_code = exit_code.strip()

        if len(res) < 4000:
            await message.edit(
                template +
                f"<code>{res}<code>" +
                exit_code
            )
        else:
            await utils.stream(message, res, template, exit_code)


    @run(command="py")
    async def python(message, client):
        """A nice tool (like you 🥰) to test python codes"""
        args = message.args

        if not (args := args.strip()):
            if (reply := message.replied) is None:
                await message.edit("<i>No python code provided</i>")
                return
            else:
                args = html.escape(reply.message.strip())

        caption = """<b>⬤ {}:</b>

<code>{}</code>

<b>⬤ Result:</b>

"""
        if message.cmd:
            await message.edit(caption.format("Evaluating expression", args))

        out = sys.stdout
        err = sys.stderr

        sys.stdout = io.StringIO()
        sys.stderr = sys.stdout
        sys.stdin = io.BytesIO()
        
        async def stdin_read():
            while not (full_data := sys.stdin.getvalue()):
                await asyncio.sleep(0)

            sys.stdin.truncate(0)
            sys.stdin.seek(0)
            return full_data.decode().strip()

        async def custom_input(input_message=""):
            return f"{input_message}{(await stdin_read())}"

        sys.stdin.read = stdin_read

        locals().update(
            {
                "input": custom_input,
                "replied": message.replied,
                "getme": client.ME.id
            }
        )

        try:
            task = asyncio.create_task(
                meval(
                    args,
                    globals(),
                    **locals()
                )
            )

            task.kill = task.cancel
            task.stdin = sys.stdin

            Compiler.processes.update({message.id: task})

            if not task.done():
                try:
                    task = await task
                except asyncio.CancelledError:
                    return

            res = html.escape(str(task))
            caption = caption.format("Evaluated expression", html.escape(args))
        except Exception as e:
            caption = caption.format("Evaluation failed", html.escape(args))
            etype, val, _ = sys.exc_info()
            res = html.escape(''.join(traceback.format_exception(etype, val, None, 0)))

        try:
            val = html.escape(sys.stdout.getvalue())
        except AttributeError:
            val = ""

        res = res + val if res != "None" else val

        if not message.cmd:
            caption = ""

        if not (res := res.strip()):
            res = "None"
        if len(caption) + len(res) < 4000:
            await message.edit(caption + f"<code>{res}</code>")
        else:
            await utils.stream(message, res, caption)

        sys.stdout = out
        sys.stderr = err


    @run(command="input")
    async def input(message, client):
        args = message.args.strip()

        if not args:
            await message.edit(
                "<i>You should input something to pass to the terminal</i>"
            )
            return

        if not message.is_reply or message.replied.id not in Compiler.processes:
            await message.edit(
                "<i>Make sure to reply to a running terminal process</i>"
            )
            return

        await message.edit(
            "<i>Input has been sent to the terminal</i>"
        )

        Compiler.processes[message.replied.id].stdin.write(bytes(args + "\n", 'utf-8'))

    @run(command="kill")
    async def kill(message, client):
        process = message.replied

        if not process:
            await message.edit("<i>You have to reply to a message with a process</i>")
            return

        if process.id not in Compiler.processes:
            await message.edit("<i>No process running in that message</i>")
        else:
            try:
                Compiler.processes[process.id].kill()
            except:
                pass
            del Compiler.processes[process.id]
            await message.edit("<i>Successfully killed</i>")

    async def find_shell(*args):
        return os.popen("which zsh || which bash || which sh").read().strip()

    @run(command="shell")
    async def set_shell_mode(message, client):
        if Compiler.shell_mode is None:
            Compiler.shell_mode = settings.is_shell()

        if message.args == "python":
            Compiler.shell_mode_executable = sys.executable
            await message.edit("<i>Shell is set to Python executable</i>")
            return

        elif message.args == "shell":
            Compiler.shell_mode_executable = await Compiler.find_shell()
            await message.edit("<i>Shell is set to default executable</i>")
            return

        Compiler.shell_mode = not Compiler.shell_mode
        settings.set_shell_mode(Compiler.shell_mode)
        await message.edit(f"<i>Shell mode is set to {Compiler.shell_mode}</i>")

    @event_watcher(pattern=r"(\.+$|^[^.].*)+")
    async def telegram_to_shell(message: Message, client):
        if Compiler.shell_mode is None or Compiler.shell_mode_executable is None:
            Compiler.shell_mode = settings.is_shell()
            Compiler.shell_mode_executable = await Compiler.find_shell()

        if not Compiler.shell_mode or message.sender_id != client.ME.id:
            return

        try:
            if Compiler.shell_mode_executable == sys.executable:
                await Compiler.python(message, client)
            else:
                await Compiler.terminal(message, client)
        except:
            pass
