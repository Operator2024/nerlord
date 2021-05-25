import asyncio
import json
import logging
import platform
import re
import sys
import traceback
from typing import *

import asyncssh
from aiohttp import web
from loggers import nlog


async def ping(ip: Text):
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


async def redirect(request):
    if request.method == "GET":
        print(request.url)
        if str(request.rel_url) == "/" or re.search("/\?.{1,}", str(request.rel_url)):
            location = request.app.router["api"].url_for()
            return web.HTTPFound(location=location)


async def do_GET(request: web.BaseRequest):
    headers = {"Content-Language": "en-US, ru-RU, en, ru", "Content-Type": "text/plain"}
    if str(request.rel_url) == "/api":
        return web.Response(text=f"Используйте следующий адрес для запроса - {request.url}",
                            status=200)
    if request.query_string:
        if request.method == "GET":
            query_params = dict()
            data = request.url.query_string.split("&")
            asterisk = "*" * 8
            idx = 1
            _path_qs = ""

            for i in data:
                _tmp = i.split("=")
                query_params[_tmp[0]] = _tmp[1]

            if query_params.get("vendor") is None:
                return web.Response(text="Ключевой параметр (vendor) отсутствует!", status=200)
            else:
                if query_params.get("command") is None:
                    return web.Response(text="Ключевой параметр (command) отсутствует!", status=200)
                else:
                    msg = f"Переданная команда ({query_params['command']}) не должна " \
                          "содержать изменяющих конфигурацию устройства модификаторов!"
                    if query_params["vendor"] == "Mikrotik":
                        if "set" in query_params["command"] or "add" in query_params["command"] \
                                or "remove" in query_params["command"] or "rem" in query_params[
                            "command"] or "unset" in query_params["command"] or "edit" in \
                                query_params["command"] or "enable" in query_params["command"] or \
                                "disable" in query_params["command"]:
                            logger = nlog("info")
                            logger.info(msg)
                            return web.Response(text=msg, status=200)
                    elif query_params["vendor"] == "SNR":
                        if "show" not in query_params["command"] or\
                                "sh" not in query_params["command"]:
                            logger = nlog("info")
                            logger.info(msg)
                            return web.Response(text=msg, status=200)

            for i in ["login", "password", "command"]:
                if idx == 1:
                    _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" + "=.{1,}$)",
                                      request.path_qs)
                    #bugfix params
                    if request.path_qs[_path.span()[1] - 1] == "&":
                        _path_qs = re.sub(f"{i}" + "=\w{1,}&", f"{i}={asterisk}&",
                                          request.path_qs)
                    else:
                        _path_qs = re.sub(f"{i}" + "=.{1,}$", f"{i}={asterisk}",
                                          request.path_qs)
                else:
                    _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" + "=.{1,}$)",
                                      _path_qs)
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

            r = await ping(ip=query_params["host"])
            if r == 0:
                try:
                    async with asyncssh.connect(host=query_params["host"],
                                                port=int(query_params["port"]),
                                                username=query_params["login"],
                                                password=query_params["password"],
                                                known_hosts=None) as ssh:
                        resp = await ssh.run(query_params["command"], check=True, timeout=10)
                        if resp.returncode != 0:
                            raise asyncssh.ConnectionLost(reason="ConnectionLost")
                        result = resp.stdout + resp.stderr

                except KeyError as err:
                    logger = nlog("info")
                    msg = f"KeyError: обязательный ключ {err} отсутствует"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    logger = nlog("info")
                    msg = f"{err}: ошибка аутентификации, возможно, логин или пароль указаны " \
                          f"неверно!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    logger = nlog("info")
                    msg = f"{err}: соединение было разорвано!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    logger = nlog("info")
                    msg = f"TimeoutError: не удалось подключиться к узлу в течение заданного " \
                          f"времени! - {err}"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    logger = nlog("info")
                    msg = f"ConnectionError: {err}, возможно, хост или порт указаны неверно!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    logger = nlog("info")
                    msg = f"Exception: {err}"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)

            if r == 1:
                print('aaa')
    return web.Response(text=f"Результат - {result}", headers=headers, status=200)


async def do_POST(request: web.BaseRequest):
    # headers = {"Content-Type": "application/json; charset=UTF-8"}
    headers = {"Content-Language": "en-US, ru-RU, en, ru", "Content-Type": "text/plain"}
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

            if content.get("vendor") is None:
                logger = nlog("info")
                msg = f"KeyError: обязательный ключ 'vendor' отсутствует"
                logger.info(msg)
                return web.Response(text=msg, headers=headers, status=200)
            else:
                if content.get("command") is None:
                    logger = nlog("info")
                    msg = f"KeyError: обязательный ключ 'command' отсутствует"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                else:
                    msg = f"Используемая команда ({content['command']}) не должна " \
                          "содержать изменяющих конфигурацию устройства модификаторов!"
                    if content["vendor"] == "Mikrotik":
                        if "set" in content["command"] or "add" in content["command"] \
                                or "remove" in content["command"] or "rem" in content[
                            "command"] or "unset" in content["command"] or "edit" in \
                                content["command"] or "enable" in content["command"] or \
                                "disable" in content["command"]:
                            logger = nlog("info")
                            logger.info(msg)
                            return web.Response(text=msg, status=200)
                    elif content["vendor"] == "SNR":
                        if "show" not in content["command"] or \
                                "sh" not in content["command"]:
                            logger = nlog("info")
                            logger.info(msg)
                            return web.Response(text=msg, headers=headers, status=200)

            r = await ping(ip=content["host"])
            if r == 0:
                try:
                    async with asyncssh.connect(host=content["host"], port=content["port"],
                                                username=content["login"],
                                                password=content["password"],
                                                known_hosts=None) as ssh:
                        resp = await ssh.run(content["command"], check=True, timeout=10)
                        if resp.returncode != 0:
                            raise asyncssh.ConnectionLost(reason="ConnectionLost")
                        result = resp.stdout + resp.stderr

                except KeyError as err:
                    logger = nlog("info")
                    msg = f"KeyError: обязательный ключ {err} отсутствует"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    logger = nlog("info")
                    msg = f"{err}: ошибка аутентификации, возможно, логин или пароль указаны " \
                          f"неверно!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    logger = nlog("info")
                    msg = f"{err}: соединение было разорвано!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    logger = nlog("info")
                    msg = f"TimeoutError: не удалось подключиться к узлу в течение заданного " \
                          f"времени! - {err}"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    logger = nlog("info")
                    msg = f"ConnectionError: {err}, возможно, хост или порт указаны неверно!"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    logger = nlog("info")
                    msg = f"Exception: {err}"
                    logger.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)

        else:
            return web.Response(text="Используемый метод не разрешен для данного URL!",
                                headers=headers, status=405)
    return web.Response(text=f"Результат - {result}", headers=headers, status=200)
