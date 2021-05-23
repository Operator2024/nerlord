import asyncio
import json
import platform
import re

import asyncssh
from aiohttp import web

tasks = []


async def ping(ip):
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    resp = await asyncio.create_subprocess_shell(f"ping {ip} {parameter} 5",
                                                 stderr=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await resp.communicate()
    return resp.returncode


async def a():
    for i in range(10):
        print(i)
    await asyncio.sleep(10)


async def do_GET(request):
    headers = {"Content-Language": "en-US", "Content-Type": "text/plain"}
    if request.query_string:
        if request.method == "GET":
            query_params = dict()
            data = request.url.query_string.split("&")
            asterisk = "*" * 8
            idx = 1
            _path_qs = ""
            for i in ["login", "password", "command"]:
                if idx == 1:
                    _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" + "=\.{1,}$)",
                                      request.path_qs)

                    if request.path_qs[_path.span()[1] - 1] == "&":
                        _path_qs = re.sub(f"{i}" + "=\w{1,}&", f"{i}={asterisk}&",
                                          request.path_qs)
                    else:
                        _path_qs = re.sub(f"{i}" + "=\.{1,}$", f"{i}={asterisk}",
                                          request.path_qs)
                else:
                    _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" + "=.{1,}$)", _path_qs)
                    if _path_qs[_path.span()[1] - 1] == "&":
                        _path_qs = re.sub(f"{i}" + "=\w{1,}&", f"{i}={asterisk}&", _path_qs)
                    else:
                        _path_qs = re.sub(f"{i}" + "=.{1,}$", f"{i}={asterisk}", _path_qs)
                idx += 1

            del _path
            headers["SecureRequest"] = "{} {} HTTP/{}.{}".format(
                request.method,
                _path_qs,
                request.version.major,
                request.version.minor,
            )

            for i in data:
                _tmp = i.split("=")
                query_params[_tmp[0]] = _tmp[1]
            r = await ping(ip=query_params["host"])
            if r == 0:
                async with asyncssh.connect(host=query_params["host"],
                                            port=int(query_params["port"]),
                                            username=query_params["login"],
                                            password=query_params["password"],
                                            known_hosts=None) as ssh:
                    resp = await ssh.run(query_params["command"], check=False, timeout=10)
                    result = resp.stdout + resp.stderr
    return web.Response(text=f"Результат - {result}", headers=headers, status=200)


async def do_POST(request):
    # headers = {"Content-Type": "application/json; charset=UTF-8"}
    headers = {"Content-Language": "en-US", "Content-Type": "text/plain"}
    if request.content:
        if request.method == "POST":
            content = await request.read()
            content = json.loads(content.decode("utf-8"))

            headers["SecureRequest"] = "{} {} HTTP/{}.{}".format(
                request.method,
                request.rel_url,
                request.version.major,
                request.version.minor,
            )

            r = await ping(ip=content["host"])
            if r == 0:
                async with asyncssh.connect(host=content["host"], port=content["port"],
                                            username=content["login"], password=content["password"],
                                            known_hosts=None) as ssh:
                    resp = await ssh.run(content["command"], check=False, timeout=10)
                    result = resp.stdout + resp.stderr

    return web.Response(text=f"Result - {result}", headers=headers, status=200)


async def main(b):
    if b == 1:
        tasks.append(asyncio.create_task(ping("1")))
    else:
        tasks.append(asyncio.create_task(a()))
    await asyncio.gather(*tasks)

# if __name__ == '__main__':
#     app = web.Application()
#     app.add_routes([web.get("/api", do_GET)])
#     app.add_routes([web.post("/post", do_POST)])
#     web.run_app(host="127.0.0.1", port=8080, app=app)
