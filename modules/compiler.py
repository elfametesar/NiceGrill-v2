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

from database import settingsdb as settings
from main import Message, run, event_watcher
from telethon import TelegramClient as Client
from meval import meval

import utils
import os
import sys
import html
import asyncio
import traceback

class Compiler:
    PROCESSES = {}
    SHELL_MODE = None
    TERMINAL_EXEC = None
    SHELL_MODE_EXEC = None

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
    async def terminal(message: Message, client: Client):
        """Asynchronous function for running terminal commands and capturing their output. It captures the standard output and error streams of the command and provides real-time feedback

This command can be used to execute shell commands and display their output in a chat or messaging environment, making it useful for interactive shell-like experiences within a chatbot or similar application

Notes:
- It asynchronously manages the execution of the command and processes its output.
- The output is formatted with information about the input command, actual output, and exit code.
- It provides an option to view the full log if the output exceeds a certain length.

Usage:

.term <shellscript code>
"""
        cmd = message.args.strip()

        if not Compiler.TERMINAL_EXEC:
            Compiler.TERMINAL_EXEC = await Compiler.find_shell()

        proc = await asyncio.create_subprocess_shell(
            cmd=cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            executable=Compiler.TERMINAL_EXEC
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

        Compiler.PROCESSES.update({message.id: proc})

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

                if message.id in Compiler.PROCESSES:
                    del Compiler.PROCESSES[message.id]

                await Compiler.process_done(
                    message,
                    res,
                    template,
                    exit_code
                )
                return

            if flood_control < 3:
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

        if message.id in Compiler.PROCESSES:
            exit_code = exit_code.format(
                proc.returncode if proc.returncode is not None else 0
            )
            del Compiler.PROCESSES[message.id]
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
    async def cpp_compiler(message: Message, client: Client):
        """
Compiles and executes C++ code provided in a message.

This function is a decorator function designed to be used with a command handler.
It compiles and executes C++ code and returns the output. If the code doesn't
contain a `main` function, a default one is added.

Parameters:
    message (Message): A message object containing the C++ code to be compiled and executed.
    client (Client): The client instance that manages the interaction.

Notes:
- It automatically determines the C++ compiler ('c++' or 'g++') to use based on
  availability.
- The input code can be provided as the argument or as a reply to another message.
- It compiles the code, executes it, captures the output, and provides real-time feedback.
- The function handles output formatting, including information about the input code
  and exit code.
- For long output, it calls the 'utils.stream' function to handle streaming.

Usage:

.cpp <c++ code> - you do not necessarily need to provide a main function
"""
        code = message.args

        if not (code := code.strip()):
            if (reply := message.reply_to_text) is None:
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

        Compiler.PROCESSES.update({message.id: proc})
        
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


    @run(command="(py|pyr)")
    async def python(message: Message, client: Client):
        """
A utility for testing Python code snippets interactively.

This command allows users to execute Python code and view the results in a chat or messaging
environment. The code can be provided as an argument or as a reply to another message.

Notes:
- It captures the output of the code, handles exceptions, and formats the output for display.
- If the output is too long, it uses the 'utils.stream' function to handle streaming.
- Users can use the command 'py' to clear the output buffer and to evaluate an expression and 'pyr' to evaluate an expression without clearing buffer.

Usage:

.py <python code>
.pyr <python code>
"""
        args = message.args

        if not (args := args.strip()):
            if message.reply_to_text is None:
                await message.edit("<i>No python code provided</i>")
                return
            else:
                args = html.escape(message.reply_to_text.message.strip())

        caption = """<b>⬤ {}:</b>

<code>{}</code>

<b>⬤ Result:</b>

"""
        if message.cmd:
            await message.edit(caption.format("Evaluating expression", args))

        async def run_in_main_loop(coro):
            return await coro

        async def iter_in_main_loop(future):
            item_list = []
            async for item in future:
                item_list.append(item)
            
            return item_list

        async def future_iterator(item_list: list):
            for item in item_list:
                yield item

        async def run_thread_safe(coro_or_future):
            is_iterable = False
            if hasattr(coro_or_future, "__aiter__"):
                is_iterable = True
                future = asyncio.run_coroutine_threadsafe(
                    coro=iter_in_main_loop(coro_or_future),
                    loop=client._loop
                )
            else:
                future = asyncio.run_coroutine_threadsafe(
                    coro=run_in_main_loop(coro_or_future),
                    loop=client._loop
                )

            while not future.done():
                await asyncio.sleep(0)

            return future.result() if not is_iterable else future_iterator(future.result())
        

        locals().update(
            {
                "replied": message.reply_to_text,
                "getme": client.me.id,
                "safe": run_thread_safe
            }
        )
        
        #clear buffer
        if message.cmd != "pyr":
            sys.stdout.read()

        task: asyncio.Task = asyncio.create_task(
            asyncio.to_thread(
                asyncio.run,
                meval(
                    code=args,
                    globs=globals(),
                    **locals()
                )
            )
        )

        task.kill = task.cancel

        Compiler.PROCESSES.update({message.id: task})
        res = ""

        try:
            res = await task
            caption = caption.format("Evaluated expression", html.escape(args))
        except RuntimeError:
            print(task.exception())
            if "see the FAQ" in str(task.exception()):
                print(
                    "\nTry wrapping your telethon calls inside await safe() wrapper. " +\
                    "For example: \n\n" +\
                    "await safe(\n\tmessage.edit('what the hell')\n)".expandtabs(4)
                )
        except asyncio.CancelledError:
            pass
        except BaseException:
            traceback.print_exc(limit=0, file=sys.stdout)
        finally:
            caption = caption.format("Evaluation failed", html.escape(args))

        res = html.escape(str(res))

        try:
            val = html.escape(sys.stdout.read())
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


    @run(command="input")
    async def input(message: Message, client: Client):
        """
Send input to a running terminal process.

This command allows users to send input to a running terminal process by replying to that
process's message with the desired input.

Notes:
- This function assumes that there is an ongoing terminal process with which the user
  can interact by providing input.
- It checks if the input message is a reply to a running terminal process and sends
  the input to that process.

Usage:
.input <data> - as a reply to a running process
"""
        args = message.args.strip()

        if not args:
            await message.edit(
                "<i>You should input something to pass to the terminal</i>"
            )
            return

        if not message.is_reply or message.reply_to_text.id not in Compiler.PROCESSES:
            await message.edit(
                "<i>Make sure to reply to a running terminal process</i>"
            )
            return

        proc = Compiler.PROCESSES[message.reply_to_msg_id]
        if isinstance(proc, asyncio.Task):
            sys.stdin.write(args + "\n")
        else:
            proc.stdin.write(bytes(args + "\n", encoding="utf-8"))

        await message.edit(
            "<i>Input has been sent to the terminal</i>"
        )

    @run(command="kill")
    async def kill(message: Message, client: Client):
        """
Terminate a running process in response to a user command.

This function is designed to be used as a decorator for a command handler.
It allows users to terminate a running process by replying to the message
associated with that process.

Notes:
- This function checks if the input message is a reply to a message that corresponds
  to a running process.
- If a process is found, it attempts to terminate it using the 'kill' method.
- The terminated process is removed from the process list.

Usage:

.kill - as a reply to a running process
"""
        process = message.reply_to_text

        if not process:
            await message.edit("<i>You have to reply to a message with a process</i>")
            return

        if process.id not in Compiler.PROCESSES:
            await message.edit("<i>No process running in that message</i>")
        else:
            try:
                Compiler.PROCESSES[process.id].kill()
            except:
                pass
            del Compiler.PROCESSES[process.id]
            await message.edit("<i>Successfully killed</i>")

    async def find_shell(*args):
        return os.popen("which zsh || which bash || which sh").read().strip()

    @run(command="shell")
    async def set_shell_mode(message: Message, client: Client):
        """
Set the shell mode for executing commands.

This command allows users to switch between different shell modes for executing commands,
such as using the Python executable or the default shell.

Notes:
- The function checks the current shell mode and switches between the Python executable
  mode and the default shell mode based on user input.
- The available shell modes are "python" (for Python executable) and "shell" (for the
  default shell).
- The selected shell mode will affect how subsequent commands are executed.

Usage:

.shell - to enable/disable shell mode
.shell shell - to switch to shellscripting mode
.shell python - to switch to python mode
"""
        if Compiler.SHELL_MODE is None:
            Compiler.SHELL_MODE = settings.is_shell()

        if message.args == "python":
            Compiler.SHELL_MODE_EXEC = sys.executable
            await message.edit("<i>Shell is set to Python executable</i>")
            return

        elif message.args == "shell":
            Compiler.SHELL_MODE_EXEC = await Compiler.find_shell()
            await message.edit("<i>Shell is set to default executable</i>")
            return

        Compiler.SHELL_MODE = not Compiler.SHELL_MODE
        settings.set_shell_mode(Compiler.SHELL_MODE)
        await message.edit(f"<i>Shell mode is set to {Compiler.SHELL_MODE}</i>")

    @event_watcher(pattern=r"(\.+$|^[^.].*)+")
    async def telegram_to_shell(message: Message, client: Client):
        if Compiler.SHELL_MODE is None or Compiler.SHELL_MODE_EXEC is None:
            Compiler.SHELL_MODE = settings.is_shell()
            Compiler.SHELL_MODE_EXEC = await Compiler.find_shell()

        if not Compiler.SHELL_MODE or message.sender_id != client.me.id:
            return

        try:
            if Compiler.SHELL_MODE_EXEC == sys.executable:
                await Compiler.python(message, client)
            else:
                await Compiler.terminal(message, client)
        except:
            pass
