__version__ = "0.0.5"

__author__ = "Vladimir Belomestnykh"

__license__ = "MIT"

__copyright__ = "Copyright (c) 2021 Vladimir Belomestnykh for Metropolis Company LLC" \
                " \n " \
                "Permission is hereby granted, free of charge, to any person obtaining a copy" \
                "of this software and associated documentation files (the \"Software\"), to deal" \
                "in the Software without restriction, including without limitation the rights" \
                "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell" \
                "copies of the Software, and to permit persons to whom the Software is" \
                "furnished to do so, subject to the following conditions:" \
                " \n " \
                "The above copyright notice and this permission notice shall be included in all" \
                "copies or substantial portions of the Software." \
                " \n " \
                "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR" \
                "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY," \
                "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE" \
                "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER" \
                "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM," \
                "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE" \
                "SOFTWARE."

import argparse
import sys

from API import *
from CLI import *
# from node import *
# from task import *
# from API import *
from loggers import *

if __name__ == '__main__':
    description = "Network device configuration management system aka Nerlord"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-m", "--mode", type=str, nargs=1, metavar="API/CLI/PINFO/IPsec",
                        required=True)
    messageHelp = "Enter the absolute path to the file "
    parser.add_argument("-i", "--inventory", type=str, nargs=1,
                        metavar="/etc/operator2024/inventory.yaml", required=False,
                        help=messageHelp + "inventory.yaml")
    parser.add_argument("-p", "--playbook", type=str, nargs=1,
                        metavar="/etc/operator2024/playbook.yaml", required=False,
                        help=messageHelp + "playbook.yaml")
    parser.add_argument("-f", "--format", type=str, nargs=1,
                        metavar="PDF/XLSX/Markdown/MD", required=False,
                        help="Choose one of the available formats (used only when -m or --mode is "
                             "PINFO)")
    parser.add_argument("-v", "--verbose", type=int, nargs=1, default=0, required=False,
                        help="This key allows you to get a detailed event log", metavar="")
    parser.add_argument("-V", "--version", help="This key allows you to get the current version",
                        version=f'{description}, {__license__} license, {__author__}, '
                                f'version: {__version__} ', action='version')
    args = parser.parse_args()

    try:
        root = nlog("MainWorker")
        pythonversion = f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
        if re.search("^3\.([789]([0-9]|)|[0-9][0-9])\.\d{1,2}$", pythonversion):
            invalidArgs = ""
            missreqArgs = ""
            if args.mode[0] == "API":
                if args.inventory is not None:
                    if len(invalidArgs) == 0:
                        invalidArgs += f"{args.inventory[0]}"
                    else:
                        invalidArgs += f", {args.inventory[0]}"
                if args.playbook is not None:
                    if len(invalidArgs) == 0:
                        invalidArgs += f"{args.playbook[0]}"
                    else:
                        invalidArgs += f", {args.playbook[0]}"
                if args.format is not None:
                    if len(invalidArgs) == 0:
                        invalidArgs += f"{args.format[0]}"
                    else:
                        invalidArgs += f", {args.format[0]}"
                if len(invalidArgs) != 0:
                    msg = "Режим API не поддерживает указанные аргументы " + invalidArgs
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)
                else:
                    if "3.7" in pythonversion:
                        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    app = web.Application()
                    app.add_routes([web.get("/", redirect)])
                    app.add_routes([web.get("/api", do_GET, name="api")])
                    app.add_routes([web.get("/post", do_POST)])
                    app.add_routes([web.post("/post", do_POST)])
                    web.run_app(host="127.0.0.1", port=8888, app=app,
                                access_log=logging.getLogger("info"),
                                access_log_format='%a %t "%{SecureRequest}o" %s %b "%{Referer}i" "%{'
                                                  'User-Agent}i"')
            elif args.mode[0] == "CLI":
                if args.inventory is None:
                    if len(missreqArgs) == 0:
                        missreqArgs += f" --inventory (-i) "
                    else:
                        missreqArgs += f", --inventory (-i) "
                if args.playbook is None:
                    if len(missreqArgs) == 0:
                        missreqArgs += f" --playbook (-p)"
                    else:
                        missreqArgs += f", --playbook (-p)"

                if args.playbook is not None and args.inventory is not None:
                    if args.format is not None:
                        if len(invalidArgs) == 0:
                            invalidArgs += f"{args.format[0]}"
                        msg = "Режим CLI не поддерживает указанные аргументы " + invalidArgs
                        logging.getLogger("info").info(msg)
                        raise argparse.ArgumentError(None, msg)
                    else:
                        if os.path.exists(args.playbook[0]):
                            resp = verify(filepath=args.playbook[0], filename="playbook.yaml")
                            if resp == "playbook.yaml is Ok":
                                logging.getLogger("info").info(f"Verify: {resp}")
                            else:
                                logging.getLogger("info").info(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg = f"Конфигурационный файл не был найден по указанному пути" \
                                  f" {args.playbook[0]}"
                            logging.getLogger("info").info(msg)
                            raise FileNotFoundError(msg)

                        if os.path.exists(args.inventory[0]):
                            resp = verify(filepath=args.inventory[0], filename="inventory.yaml")
                            if resp == "inventory.yaml is Ok":
                                logging.getLogger("info").info(f"Verify: {resp}")
                            else:
                                logging.getLogger("info").info(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg = f"Инвентаризационный файл не был найден по указанному пути " \
                                  f"{args.inventory[0]}"
                            logging.getLogger("info").info(msg)
                            raise FileNotFoundError(msg)

                    with open(args.inventory[0], "r", encoding="utf8") as file:
                        data = safe_load(file)

                    for i in data:
                        for j in data[i]:
                            if j != "individual":
                                if j in ["host", "host_multiple", "host_range"]:
                                    if j == "host_range":
                                        ip, rtt, nextip = chooseIP(hosttype=j, data=data[i][j])
                                        print(ip, rtt, nextip, -2)
                                        while True:
                                            if ip != data[i][j][1]:
                                                ip, rtt, nextip = chooseIP(hosttype=j,
                                                                           data=data[i][j],
                                                                           rngip=nextip)
                                            else:
                                                break
                                        print(ip, rtt, nextip, -1)
                                    else:
                                        ip, rtt, _ = chooseIP(hosttype=j, data=data[i][j])
                                        print(ip, rtt, 1)
                            else:
                                for k in data[i][j]:
                                    for z in data[i][j][k]:
                                        if z in ["host", "host_multiple", "host_range"]:
                                            if z == "host_range":
                                                ip, rtt, nextip = chooseIP(hosttype=z,
                                                                           data=data[i][j][k][z])
                                                print(ip, rtt, nextip, 2)
                                                while True:
                                                    print(ip)
                                                    # проверить и пофиксить вариант, когда ip недоступен и возвращается строка о недоступности
                                                    if ip != data[i][j][k][z][1] and ip != "IPv4 адрес не отвечает":
                                                        ip, rtt, nextip = chooseIP(hosttype=z,
                                                                                   data=
                                                                                   data[i][j][k][z],
                                                                                   rngip=nextip)
                                                    else:
                                                        break
                                                print(ip, rtt, nextip, 3)
                                            else:
                                                ip, rtt, _ = chooseIP(hosttype=z,
                                                                      data=data[i][j][k][z])
                                                print(ip, rtt, 4)

                else:
                    msg = "Режим CLI требует следующие аргументы, которые не были получены " + missreqArgs
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)

            elif args.mode[0] == "PINFO":
                if args.inventory is None:
                    if len(missreqArgs) == 0:
                        missreqArgs += f" --inventory (-i) "
                    else:
                        missreqArgs += f", --inventory (-i) "
                if args.playbook is None:
                    if len(missreqArgs) == 0:
                        missreqArgs += f" --playbook (-p)"
                    else:
                        missreqArgs += f", --playbook (-p)"
                if args.format is None:
                    if len(missreqArgs) == 0:
                        missreqArgs += f" --format (-f)"
                    else:
                        missreqArgs += f", --format (-f)"

                if args.playbook is not None and args.inventory is not None and args.format is not None:
                    if os.path.exists(args.playbook[0]):
                        pass
                    else:
                        msg = f"Конфигурационный файл не был найден по указанному пути" \
                              f" {args.playbook[0]}"
                        logging.getLogger("info").info(msg)
                        raise FileNotFoundError(msg)

                    if os.path.exists(args.inventory[0]):
                        pass
                    else:
                        msg = f"Инвентаризационный файл не был найден по указанному пути " \
                              f"{args.inventory[0]}"
                        logging.getLogger("info").info(msg)
                        raise FileNotFoundError(msg)

                else:
                    msg = "Режим PINFO требует следующие аргументы, которые не были получены " + \
                          missreqArgs
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)

            elif args.mode[0] == "IPsec":
                pass
        else:
            logging.getLogger("info").info(f"Используемая версия Python {pythonversion}"
                                           f" ниже поддерживаемой ")

    except FileNotFoundError as err:
        logging.getLogger("info").info(f"FileNotFoundError: {err}")
    except argparse.ArgumentError as err:
        logging.getLogger("info").info(f"ArgumentError: {err}")
    except web.HTTPRedirection as err:
        print(err, 1)
    except web.HTTPFound as err:
        print(err, 2)
    except AttributeError as err:
        logging.getLogger("info").info(f"AttributeError: {err}")
    except Exception as err:
        logging.getLogger("info").info(f"Exception: {err}")
    finally:
        pass
