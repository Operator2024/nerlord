import asyncio
import json
import platform
import re
from typing import Text

import asyncssh
from aiohttp import web

from loggers import load_config, logger_generator

if __name__ != "__main__":
    load_config()
    _loggers = logger_generator()
    _clog = _loggers[0]
    _elog = _loggers[1]
    _wlog = _loggers[2]
    _ilog = _loggers[3]
    _dlog = _loggers[4]
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
                return web.Response(text="Ключевой параметр (vendor) "
                                         "отсутствует!", status=200)
            else:
                if query_params.get("command") is None:
                    return web.Response(text="Ключевой параметр (command) "
                                             "отсутствует!", status=200)
                else:
                    msg = f"Переданная команда ({query_params['command']}) " \
                          f"не должна содержать изменяющих конфигурацию " \
                          f"устройства модификаторов!"
                    if query_params["vendor"] == "Mikrotik":
                        if "set" in query_params["command"] or\
                                "add" in query_params["command"] or \
                                "remove" in query_params["command"] or \
                                "rem" in query_params["command"] or\
                                "unset" in query_params["command"] or \
                                "edit" in query_params["command"] or \
                                "enable" in query_params["command"] or \
                                "disable" in query_params["command"]:
                            _ilog.info(msg)
                            return web.Response(text=msg, status=200)
                    elif query_params["vendor"] == "SNR":
                        if "show" not in query_params["command"] and \
                                "sh" not in query_params["command"]:
                            _ilog.info(msg)
                            return web.Response(text=msg, status=200)

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
                    msg = f"AttributeError: обязательный ключ {i} " \
                          f"отсутствует - {err}"
                    _ilog.info(msg)
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
                    msg = f"KeyError: обязательный ключ {err} отсутствует"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    msg = f"{err}: ошибка аутентификации, возможно, " \
                          f"логин или пароль указаны неверно!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    msg = f"{err}: соединение было разорвано!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    msg = f"TimeoutError: не удалось подключиться к узлу в " \
                          f"течение заданного времени! - {err}"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    msg = f"ConnectionError: {err}, возможно, хост или порт " \
                          f"указаны неверно!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ProcessError as err:
                    msg = f"ProcessError: {err}, ошибка SSH!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    msg = f"Exception: {err}"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
    return web.Response(text=f"Результат - {result}", headers=headers,
                        status=200)


async def do_POST(request: web.BaseRequest) -> web.Response:
    # headers = {"Content-Type": "application/json; charset=UTF-8"}
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
                msg = f"KeyError: обязательный ключ 'vendor' отсутствует"
                _ilog.info(msg)
                return web.Response(text=msg, headers=headers, status=200)
            else:
                if content.get("command") is None:
                    msg = f"KeyError: обязательный ключ 'command' отсутствует"
                    _ilog.info(msg)
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
                            _ilog.info(msg)
                            return web.Response(text=msg, status=200)
                    elif content["vendor"] == "SNR":
                        if "show" not in content["command"] and \
                                "sh" not in content["command"]:
                            _ilog.info(msg)
                            return web.Response(text=msg, headers=headers,
                                                status=200)

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
                    msg = f"KeyError: обязательный ключ {err} отсутствует"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.PermissionDenied as err:
                    msg = f"{err}: ошибка аутентификации, возможно, логин " \
                          f"или пароль указаны неверно!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ConnectionLost as err:
                    msg = f"{err}: соединение было разорвано!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.TimeoutError as err:
                    msg = f"TimeoutError: не удалось подключиться к узлу в" \
                          f" течение заданного времени! - {err}"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except ConnectionError as err:
                    msg = f"ConnectionError: {err}, возможно, хост или порт " \
                          f"указаны неверно!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except asyncssh.ProcessError as err:
                    msg = f"ProcessError: {err}, ошибка SSH!"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)
                except Exception as err:
                    msg = f"Exception: {err}"
                    _ilog.info(msg)
                    return web.Response(text=msg, headers=headers, status=200)

        else:
            return web.Response(text="Используемый метод не разрешен "
                                     "для данного URL!",
                                headers=headers, status=405)
    return web.Response(text=f"Результат - {result}", headers=headers,
                        status=200)
