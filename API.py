import asyncio
import json
import logging
import platform
import re
from typing import Text

import asyncssh
from aiohttp import web

from loggers import load_config, logger_generator

if __name__ != "__main__":
    load_config()
    _loggers = logger_generator()

    root = _ilog = _loggers[7]
    _eLog = _loggers[1]

    _fmt = "%(asctime)s, %(levelname)s: %(message)s"
    _datefmt = "%d-%m-%Y %I:%M:%S %p"
    _style = "%"

    root.handlers[0].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
    root.handlers[1].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
    _eLog.handlers[0].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
    _eLog.handlers[1].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
    root.info("*" * 25 + " [API mode ON] " + "*" * 25)

    msg_patterns = [
        "Обязательный параметр 'vendor' отсутствует!",
        "Обязательный параметр 'command' отсутствует!",
        "API режим работает только по ssh!",
        "Обязательный параметр 'protocol' отсутствует!",
        "Обязательный параметр 'host' отсутствует!",
        "Обязательный параметр 'port' отсутствует!",
        "Используемый метод не разрешен для данного URL!",
        "Обязательный параметр отсутствует"
    ]

else:
    raise Exception(f"Name '{__name__}' is not equal"
                    f" to {__file__.split('/')[-1].rstrip('.py')}")


async def ping(ip: Text) -> int:
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


async def redirect(request: web.Request) -> web.HTTPFound:
    if request.method == "GET":
        if str(request.rel_url) == "/" or re.search("/\?.{1,}",
                                                    str(request.rel_url)):
            location = request.app.router["api"].url_for()
            return web.HTTPFound(location=location)


async def do_GET(request: web.BaseRequest) -> web.Response:
    headers = {"Content-Language": "en-US, ru-RU, en, ru",
               "Content-Type": "text/plain"}
    if str(request.rel_url) == "/api":
        return web.Response(text=f"Используйте следующий адрес для запроса"
                                 f" - {request.url}", status=200)
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
                msg = msg_patterns[0]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)
            else:
                if query_params.get("command") is None:
                    msg = msg_patterns[1]
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, status=200, headers=headers)
                else:
                    msg = f"Переданная команда ({query_params['command']}) " \
                          f"не должна содержать изменяющих конфигурацию " \
                          f"устройства модификаторов!"
                    if query_params["vendor"] == "Mikrotik":
                        if "set" in query_params["command"] or \
                                "add" in query_params["command"] or \
                                "remove" in query_params["command"] or \
                                "rem" in query_params["command"] or \
                                "unset" in query_params["command"] or \
                                "edit" in query_params["command"] or \
                                "enable" in query_params["command"] or \
                                "disable" in query_params["command"]:
                            headers['text'] = msg
                            _eLog.error(msg)
                            return web.Response(text=msg, status=200,
                                                headers=headers)
                    elif query_params["vendor"] == "SNR":
                        if "show" not in query_params["command"] and \
                                "sh" not in query_params["command"]:
                            headers['text'] = msg
                            _eLog.error(msg)
                            return web.Response(text=msg, status=200,
                                                headers=headers)

            if query_params.get("protocol"):
                if query_params["protocol"] != "ssh":
                    msg = msg_patterns[2]
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, status=200, headers=headers)
            else:
                msg = msg_patterns[3]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            if query_params.get("host") is None:
                msg = msg_patterns[4]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            if query_params.get("port") is None:
                msg = msg_patterns[5]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            for i in ["login", "password", "command"]:
                try:
                    if idx == 1:
                        _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" +
                                          "=.{1,}$)", request.path_qs)
                        # bugfix params
                        if request.path_qs[_path.span()[1] - 1] == "&":
                            _path_qs = re.sub(f"{i}" + "=\w{1,}&",
                                              f"{i}={asterisk}&",
                                              request.path_qs)
                        else:
                            _path_qs = re.sub(f"{i}" + "=.{1,}$",
                                              f"{i}={asterisk}",
                                              request.path_qs)
                    else:
                        _path = re.search("(" + f"{i}" + "=\w{1,}&|" + f"{i}" +
                                          "=.{1,}$)", _path_qs)
                        if _path_qs[_path.span()[1] - 1] == "&":
                            _path_qs = re.sub(f"{i}" + "=\w{1,}&",
                                              f"{i}={asterisk}&", _path_qs)
                        else:
                            _path_qs = re.sub(f"{i}" + "=.{1,}$",
                                              f"{i}={asterisk}", _path_qs)
                    idx += 1
                except AttributeError as err:
                    msg = f"Обязательный параметр отсутствует - {i},{ err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)

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
                                                password=
                                                query_params["password"],
                                                known_hosts=None,
                                                login_timeout=10) as ssh:
                        resp = await ssh.run(query_params["command"],
                                             check=True, timeout=10)
                        if resp.returncode != 0 and resp.returncode is not None:
                            raise asyncssh.ConnectionLost(
                                reason="ConnectionLost")
                        result = resp.stdout + resp.stderr

                except KeyError as err:
                    msg = msg_patterns[7] + f"- {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    msg = f"{err}: ошибка аутентификации, возможно, " \
                          f"логин или пароль указаны неверно!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    msg = f"{err}: соединение было разорвано!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    msg = f"TimeoutError: не удалось подключиться к узлу в " \
                          f"течение заданного времени! - {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    msg = f"ConnectionError: {err}, возможно, хост или порт " \
                          f"указаны неверно!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ProcessError as err:
                    msg = f"ProcessError: {err}, ошибка SSH!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    msg = f"Exception: {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
            else:
                msg = f"IP '{query_params['host']}' недоступен"
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, headers=headers, status=200)
        else:
            msg = msg_patterns[6]
            headers['text'] = msg
            return web.Response(text=msg, headers=headers, status=405)

    result = result.rstrip("\r\n").lstrip("\r\n")
    msg = f"Результат - {result}"
    headers['text'] = msg
    return web.Response(text=msg, headers=headers, status=200)


async def do_POST(request: web.BaseRequest) -> web.Response:
    headers = {"Content-Language": "en-US, ru-RU, en, ru",
               "Content-Type": "text/plain"}
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
                msg = msg_patterns[0]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, headers=headers, status=200)
            else:
                if content.get("command") is None:
                    msg = msg_patterns[1]
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                else:
                    msg = f"Используемая команда ({content['command']}) не " \
                          f"должна содержать изменяющих конфигурацию " \
                          f"устройства модификаторов!"
                    if content["vendor"] == "Mikrotik":
                        if "set" in content["command"] or \
                                "add" in content["command"] or \
                                "remove" in content["command"] or \
                                "rem" in content["command"] or \
                                "unset" in content["command"] or \
                                "edit" in content["command"] or \
                                "enable" in content["command"] or \
                                "disable" in content["command"]:
                            headers['text'] = msg
                            _eLog.error(msg)
                            return web.Response(text=msg, status=200,
                                                headers=headers)
                    elif content["vendor"] == "SNR":
                        if "show" not in content["command"] and \
                                "sh" not in content["command"]:
                            headers['text'] = msg
                            _eLog.error(msg)
                            return web.Response(text=msg, headers=headers,
                                                status=200)

            if content.get("protocol"):
                if content["protocol"] != "ssh":
                    msg = msg_patterns[2]
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, status=200, headers=headers)
            else:
                msg = msg_patterns[3]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            if content.get("host") is None:
                msg = msg_patterns[4]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            if content.get("port") is None:
                msg = msg_patterns[5]
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, status=200, headers=headers)

            r = await ping(ip=content["host"])
            if r == 0:
                try:
                    async with asyncssh.connect(host=content["host"],
                                                port=content["port"],
                                                username=content["login"],
                                                password=content["password"],
                                                known_hosts=None,
                                                login_timeout=10) as ssh:
                        resp = await ssh.run(content["command"], check=True,
                                             timeout=10)
                        if resp.returncode != 0 and resp.returncode is not None:
                            raise asyncssh.ConnectionLost(
                                reason="ConnectionLost")
                        result = resp.stdout + resp.stderr

                except KeyError as err:
                    msg = msg_patterns[7] + f"- {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    msg = f"{err}: ошибка аутентификации, возможно, логин " \
                          f"или пароль указаны неверно!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    msg = f"{err}: соединение было разорвано!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    msg = f"TimeoutError: не удалось подключиться к узлу в" \
                          f" течение заданного времени! - {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    msg = f"ConnectionError: {err}, возможно, хост или порт " \
                          f"указаны неверно!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ProcessError as err:
                    msg = f"ProcessError: {err}, ошибка SSH!"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    msg = f"Exception: {err}"
                    headers['text'] = msg
                    _eLog.error(msg)
                    return web.Response(text=msg, headers=headers, status=200)
            else:
                msg = f"IP '{content['host']}' недоступен"
                headers['text'] = msg
                _eLog.error(msg)
                return web.Response(text=msg, headers=headers, status=200)
        else:
            msg = msg_patterns[6]
            headers['text'] = msg
            return web.Response(text=msg, headers=headers, status=405)

    result = result.rstrip("\r\n").lstrip("\r\n")
    msg = f"Результат - {result}"
    headers['text'] = msg
    return web.Response(text=msg, headers=headers, status=200)
