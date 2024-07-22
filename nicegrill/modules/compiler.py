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

from nicegrill.utils import ProcessManager
from elfrien.types.patched import Message
from traceback import format_exception
from elfrien.client import Client
from nicegrill import on, startup
from database import settings
from meval import meval

import asyncio
import shutil
import httpx
import time
import html
import os

class Compiler:

    LAST_MSG_TIME = 0
    SHELL_MODE = False
    TERMINAL_EXECUTABLE = None

    RESULT_TEMPLATE = """<b>{title}</b>

<code>{command}</code>

<b>Result</b>

<code>{result}</code>"""

    async def spawn_process():
        return await asyncio.subprocess.create_subprocess_shell(
            cmd='read line && eval "$line"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            executable=Compiler.TERMINAL_EXECUTABLE
        )

    @on(pattern="(py|python)")
    async def python_interpreter(client: Client, message: Message):
        """
        Evaluates Python code within an asynchronous environment and returns the result.

        Usage:
        .py <code>    # Evaluates the given Python code
        """

        if not message.raw_args:
            await message.edit("<i>Give me some code to work with</i>")
            return

        try:
            reply = message.reply_to_text
            chat = message.chat

            task = asyncio.create_task(
                meval(
                    code=message.raw_args,
                    globs=globals(),
                    **locals()
                )
            )

            ProcessManager.add_process(
                message_id=message.id,
                process=task
            )

            while not task.done():
                await asyncio.sleep(0)
            else:
                result = task.result()

            if message.cmd:
                await message.edit(
                    Compiler.RESULT_TEMPLATE.format(
                        title="Evaluated expression",
                        command=message.raw_args.strip(),
                        result=html.escape(str(result))
                    )
                )
            else:
                await message.edit(str(result))

        except Exception as e:
            if message.cmd:
                await message.edit(
                    Compiler.RESULT_TEMPLATE.format(
                        title="Evaluation failed",
                        command=message.raw_args.strip(),
                        result=html.escape(
                            " ".join(format_exception(e))
                        )
                    )
                )
            else:
                await message.edit(html.escape(str((e))))

    @on(pattern="(term|terminal)")
    async def terminal(client: Client, message: Message):
        """
        Executes a terminal command and returns the output.

        Usage:
        .term <command>    # Executes the given terminal command
        """
        command = message.raw_args

        if not command:
            await message.edit("<i>Give me a terminal command</i>")
            return

        await message.edit(
            Compiler.RESULT_TEMPLATE.format(
                title="Evaluated expression",
                command=command,
                result=""
            )
        )

        process = await Compiler.spawn_process()
        process.stdin.write((command + "\n").encode())

        ProcessManager.add_process(
            message_id=message.id,
            process=process
        )

        output = ""
        start = time.time() - 1.5
        iter = process.stdout.__aiter__()
        mod_time = time.time()

        while True:
            await asyncio.sleep(0)

            if not ProcessManager.find_process(message.id):
                break

            result = iter._buffer.decode()
            iter._buffer = bytearray()

            output += "\n" + result
            output = output[:4098].strip()

            if not result.strip():
                if time.time() - mod_time > 14:
                    break
                continue
            else:
                mod_time = time.time()

            if time.time() - start <= 1.5:
                continue
            else:
                start = time.time()

            if message.cmd:
                await message.edit(
                    Compiler.RESULT_TEMPLATE.format(
                        title="Evaluated expression",
                        command=command,
                        result=output
                    )
                )

            else:
                await message.edit(output)
                ProcessManager.remove_process(message.id)

            if process.returncode != None:
                process = await Compiler.spawn_process()
                old_buffer = iter._buffer
                iter = process.stdout.__aiter__()
                iter._buffer = old_buffer

                if not ProcessManager.find_process(message.id):
                    break

                ProcessManager.add_process(
                    message_id=message.id,
                    process=process
                )

        if message.cmd:
            await message.edit(
                Compiler.RESULT_TEMPLATE.format(
                    title="Input",
                    command=command,
                    result=output + "\n\nProcess exited"
                )
            )
        else:
            await message.edit(output)
    
    def find_shell():
        shells = ['zsh', 'bash', 'sh']
        for shell in shells:
            path = shutil.which(shell)
            if path:
                return path

        return os.environ.get('SHELL', '/bin/sh')

    @on(pattern="(cpp|cppm)")
    async def compile_cpp(client: Client, message: Message):
        """
        Compiles C++ code using the Wandbox API. 
        If the command is 'cppm', it wraps the code in a main function.

        Usage:
        .cpp <code>    # Compiles the given C++ code
        .cppm <code>   # Wraps the code in a main function and compiles
        """

        code = message.raw_args
        if message.cmd.strip() == "cppm":
            code = """#include <iostream>

using namespace std;

int main(int argc, char *argv[]) {{
    {}
}}"""
            code = code.format(
                "\n    ".join(message.raw_args.splitlines())
            )

        await message.edit("<i>Compiling</i>")

        response = httpx.post(
            url="https://wandbox.org/api/compile.json",
            json={
                "code": code,
                "options": "warning,gnu++1y",
                "compiler": "gcc-head",
                "compiler-option-raw": "-Dx=hogefuga\n-O3"
            }
        )

        compiler_error = response.json().get("compiler_error")
        program_output = response.json().get("program_output")
        program_error = response.json().get("program_error")

        result = Compiler.RESULT_TEMPLATE.format(
            title="Compiled code",
            command=message.raw_args,
            result=program_output
        )

        result += f"""
<b>Compiler output</b>

<code>{compiler_error}</code>

<b>Program errors</b>

<code>{program_error}</code>"""

        await message.edit(result)

    @on(pattern="(shell|shellnot)")
    async def set_shell_mode(client: Client, message: Message):
        """
        Toggles the shell mode between 'terminal' and 'python'. 
        If the command is 'shellnot', it turns off the shell mode.

        Usage:
        .shell      # Toggles the shell mode
        .shellnot   # Turns off the shell mode
        """
        if message.cmd == "shellnot":
            settings.set_shell_mode(switch=False)
            Compiler.SHELL_MODE = False
            await message.edit("<i>Shell mode is off</i>")
            return

        if Compiler.SHELL_MODE == "terminal":
            Compiler.SHELL_MODE = "python"
        else:
            Compiler.SHELL_MODE = "terminal"

        settings.set_shell_mode(switch=Compiler.SHELL_MODE)
        Compiler.LAST_MSG_TIME = time.time()
        await message.edit(f"<i>Shell mode is set to {Compiler.SHELL_MODE}</i>")

    @on(prefix="", pattern=r"(\.+$|[^\.]+)")
    async def telegram_to_shell(client: Client, message: Message):
        if Compiler.SHELL_MODE is None:
            Compiler.SHELL_MODE = settings.is_shell()

        if not Compiler.SHELL_MODE:
            return

        if time.time() - Compiler.LAST_MSG_TIME > 30:
            settings.set_shell_mode(False)
            Compiler.SHELL_MODE = False
            return

        Compiler.LAST_MSG_TIME = time.time()

        message.cmd = ''
        message.raw_args = message.raw_text
        if Compiler.SHELL_MODE == "python":
            await Compiler.python_interpreter(client, message)
        else:
            await Compiler.terminal(client, message)

@startup
def startup():
    Compiler.TERMINAL_EXECUTABLE = Compiler.find_shell()
    Compiler.SHELL_MODE = settings.is_shell()

    if Compiler.SHELL_MODE:
        Compiler.LAST_MSG_TIME = time.time()