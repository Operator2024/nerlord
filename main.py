__version__ = "0.1.6"

__author__ = "Vladimir Belomestnykh aka Operator2024"

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
from multiprocessing import Manager, Process
from sys import version_info

from API import *
from CLI import *
# from node import *
# from task import *
# from API import *
from loggers import *


# debug
def test(a):
    pass


def proc_creator(data: List, plist: List) -> List:
    data[2] = re.sub("\s{1,}", "_", data[2])
    plist.append(Process(target=data[0], args=(data[1],), name=data[2]))
    return plist


if __name__ == '__main__':
    description = "Network device configuration management system aka Nerlord"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-m", "--mode", type=str, nargs=1,
                        metavar="API/CLI/PINFO/IPsec",
                        required=True)
    messageHelp = "Enter the absolute path to the file "
    parser.add_argument("-i", "--inventory", type=str, nargs=1,
                        metavar="/etc/operator2024/inventory.yaml",
                        required=False,
                        help=messageHelp + "inventory.yaml")
    parser.add_argument("-p", "--playbook", type=str, nargs=1,
                        metavar="/etc/operator2024/playbook.yaml",
                        required=False,
                        help=messageHelp + "playbook.yaml")
    parser.add_argument("-f", "--format", type=str, nargs=1,
                        metavar="PDF/XLSX/Markdown/MD", required=False,
                        help="Choose one of the available formats "
                             "(used only when -m or --mode is PINFO)")
    parser.add_argument("-v", "--verbose", type=int, nargs=1, default=0,
                        required=False,
                        help="This key allows you to get a detailed event log",
                        metavar="")
    parser.add_argument("-V", "--version",
                        help="This key allows you to get the current version",
                        version=f'{description}, {__license__} license, '
                                f'{__author__}, version: {__version__} ',
                        action='version')
    args = parser.parse_args()

    try:
        py_version = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
        msg_patterns = [
            f"Используемая версия Python {py_version} ниже поддерживаемой 3.7+",
            f"Режим {args.mode[0]} требует следующие аргументы, которые не были"
            f" получены ",
            "Инвентаризационный файл не был найден по указанному пути ",
            "Конфигурационный файл не был найден по указанному пути ",
            f"Режим {args.mode[0]} не поддерживает указанные аргументы ", 2
            ]
        root = nlog("MainWorker")
        if re.search("^3\.([789]([0-9]|)|[0-9][0-9])\.\d{1,2}$", py_version):
            invalid_args = ""
            miss_req_args = ""
            if args.mode[0] == "API":
                if args.inventory is not None:
                    if len(invalid_args) == 0:
                        invalid_args += f"{args.inventory[0]}"
                    else:
                        invalid_args += f", {args.inventory[0]}"
                if args.playbook is not None:
                    if len(invalid_args) == 0:
                        invalid_args += f"{args.playbook[0]}"
                    else:
                        invalid_args += f", {args.playbook[0]}"
                if args.format is not None:
                    if len(invalid_args) == 0:
                        invalid_args += f"{args.format[0]}"
                    else:
                        invalid_args += f", {args.format[0]}"
                if len(invalid_args) != 0:
                    msg = msg_patterns[4] + invalid_args
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)
                else:
                    if "3.7" in py_version:
                        asyncio.set_event_loop_policy(
                            asyncio.WindowsProactorEventLoopPolicy())
                    app = web.Application()
                    app.add_routes([web.get("/", redirect)])
                    app.add_routes([web.get("/api", do_GET, name="api")])
                    app.add_routes([web.get("/post", do_POST)])
                    app.add_routes([web.post("/post", do_POST)])
                    web.run_app(host="127.0.0.1", port=8888, app=app,
                                access_log=logging.getLogger("info"),
                                access_log_format='%a %t "%{SecureRequest}o" %s'
                                                  ' %b "%{Referer}i" "%{'
                                                  'User-Agent}i"')
            elif args.mode[0] == "CLI":
                if args.inventory is None:
                    if len(miss_req_args) == 0:
                        miss_req_args += f" --inventory (-i) "
                    else:
                        miss_req_args += f", --inventory (-i) "
                if args.playbook is None:
                    if len(miss_req_args) == 0:
                        miss_req_args += f" --playbook (-p)"
                    else:
                        miss_req_args += f", --playbook (-p)"

                if args.playbook is not None and args.inventory is not None:
                    if args.format is not None:
                        if len(invalid_args) == 0:
                            invalid_args += f"{args.format[0]}"
                        msg = msg_patterns[4] + invalid_args
                        logging.getLogger("info").info(msg)
                        raise argparse.ArgumentError(None, msg)
                    else:
                        if os.path.exists(args.playbook[0]):
                            resp = verify(filepath=args.playbook[0],
                                          filename="playbook.yaml")
                            if resp == "playbook.yaml is Ok":
                                logging.getLogger("info").info(
                                    f"Verify: {resp}")
                            else:
                                logging.getLogger("info").info(
                                    f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[3] + args.playbook[0]
                            logging.getLogger("info").info(msg)
                            raise FileNotFoundError(msg)

                        if os.path.exists(args.inventory[0]):
                            resp = verify(filepath=args.inventory[0],
                                          filename="inventory.yaml")
                            if resp == "inventory.yaml is Ok":
                                logging.getLogger("info").info(
                                    f"Verify: {resp}")
                            else:
                                logging.getLogger("info").info(
                                    f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[2] + args.inventory[0]
                            logging.getLogger("info").info(msg)
                            raise FileNotFoundError(msg)

                    with open(args.inventory[0], "r", encoding="utf8") as file:
                        data = safe_load(file)

                    #debug prints
                    with Manager() as mgr:
                        block = mgr.BoundedSemaphore(2)
                        tasks_summary: Dict = mgr.dict()
                        _patterns: List[Text] = ["IPv4 адрес не отвечает"]
                        _pList: List = []
                        for i in data:
                            for j in data[i]:
                                if j != "individual":
                                    if j in ["host",
                                             "host_multiple", "host_range"]:
                                        if j == "host_range":
                                            ip, rtt, nextip = \
                                                choose_ip(hosttype=j,
                                                          data=data[i][j])
                                            print(ip, rtt, nextip, -2)
                                            if rtt != 0 and rtt > 0:
                                                _pList = proc_creator(
                                                    [test, tasks_summary,
                                                     f"{i}_{ip}"],
                                                    _pList)
                                            while True:
                                                print(data[i][j], ip)
                                                if ip != data[i][j][1] and \
                                                        ip != _patterns[0]:
                                                    ip, rtt, nextip = \
                                                        choose_ip(hosttype=j,
                                                                  data=data[i][
                                                                      j],
                                                                  rngip=nextip)
                                                else:
                                                    break
                                            print(ip, rtt, nextip, -1)
                                            if rtt != 0 and rtt > 0:
                                                _pList = proc_creator(
                                                    [test, tasks_summary,
                                                     f"{i}_{ip}"],
                                                    _pList)
                                        else:
                                            ip, rtt, _ = \
                                                choose_ip(hosttype=j,
                                                          data=data[i][j])
                                            print(ip, rtt, 1)
                                            if rtt != 0 and rtt > 0:
                                                _pList = proc_creator(
                                                    [test, tasks_summary,
                                                     f"{i}_{ip}"],
                                                    _pList)
                                else:
                                    for k in data[i][j]:
                                        for z in data[i][j][k]:
                                            # _algo_type is only three values
                                            # host, host_multiple and host_range
                                            _algo_type = data[i][j][k][z]
                                            if z in ["host", "host_multiple",
                                                     "host_range"]:
                                                if z == "host_range":
                                                    ip, rtt, nextip = choose_ip(
                                                        hosttype=z,
                                                        data=_algo_type)
                                                    print(ip, rtt, nextip, 2)
                                                    if rtt != 0 and rtt > 0:
                                                        _pList = proc_creator(
                                                            [test,
                                                             tasks_summary,
                                                             f"{i}_{ip}"],
                                                            _pList)
                                                    while True:
                                                        print(ip)
                                                        # проверить и пофиксить вариант, когда ip недоступен и возвращается строка о недоступности
                                                        if ip != _algo_type[1]\
                                                                and ip != \
                                                                _patterns[0]:
                                                            ip, rtt, nextip = \
                                                                choose_ip(
                                                                    hosttype=z,
                                                                    data=
                                                                    _algo_type,
                                                                    rngip=nextip
                                                                )
                                                        else:
                                                            break
                                                    print(ip, rtt, nextip, 3)
                                                    if rtt != 0 and rtt > 0:
                                                        _pList = proc_creator(
                                                            [test,
                                                             tasks_summary,
                                                             f"{i}_{ip}"],
                                                            _pList)
                                                else:
                                                    ip, rtt, _ = choose_ip(
                                                        hosttype=z,
                                                        data=_algo_type)
                                                    print(ip, rtt, 4)
                                                    if rtt != 0 and rtt > 0:
                                                        _pList = proc_creator(
                                                            [test,
                                                             tasks_summary,
                                                             f"{i}_{ip}"],
                                                            _pList)
                        print(_pList)

                else:
                    msg: Text = msg_patterns[1] + miss_req_args
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)

            elif args.mode[0] == "PINFO":
                if args.inventory is None:
                    if len(miss_req_args) == 0:
                        miss_req_args += f" --inventory (-i) "
                    else:
                        miss_req_args += f", --inventory (-i) "
                if args.playbook is None:
                    if len(miss_req_args) == 0:
                        miss_req_args += f" --playbook (-p)"
                    else:
                        miss_req_args += f", --playbook (-p)"
                if args.format is None:
                    if len(miss_req_args) == 0:
                        miss_req_args += f" --format (-f)"
                    else:
                        miss_req_args += f", --format (-f)"

                if args.playbook is not None and args.inventory is not None and\
                        args.format is not None:
                    if os.path.exists(args.playbook[0]):
                        print("Mode is developed state now")
                    else:
                        msg: Text = msg_patterns[3] + args.playbook[0]
                        logging.getLogger("info").info(msg)
                        raise FileNotFoundError(msg)

                    if os.path.exists(args.inventory[0]):
                        pass
                    else:
                        msg: Text = msg_patterns[2] + args.inventory[0]
                        logging.getLogger("info").info(msg)
                        raise FileNotFoundError(msg)

                else:
                    msg: Text = msg_patterns[1] + miss_req_args
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)

            elif args.mode[0] == "IPsec":
                print("Mode is developed state now")
        else:
            logging.getLogger("info").info(msg_patterns[0])

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
