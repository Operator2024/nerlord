__version__ = "0.2.9-beta.2"

__author__ = "Vladimir Belomestnykh aka Operator2024"

__license__ = "MIT"

__copyright__ = "Copyright (c) 2021-22 Vladimir Belomestnykh for Metropolis Company LLC" \
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
import logging
import os
import re
from multiprocessing import Manager, Process, Queue, current_process
from random import randint
from sys import version_info
# for tests; remove after
from time import sleep
from typing import Text, List, Dict

from yaml import safe_load

from loggers import listener_setup, queue_handler_setup, \
    load_config, logger_generator


def _worker(a, b, c, d, e):
    """
    :param a: Dict - shared vocabulary between processes.
              a['key'] = [ok_status, changed_status,
                          error_status, total_steps]
    :param b: Text - IPv4 addr
    :param c: BoundedSemaphore - block object
    :param d: Set - raw_auth_data
              d[0] - protocol, d[1] - ssh key; it's dict, d[2] - username,
              d[3] - password, d[4] - ssh port, d[5] - vendor
    :param e: queue logger object
    :return: None
    """
    import sys
    import json
    from datetime import datetime

    from CLI import check_path, get_step, get_hash, get_device_config

    if sys.version_info >= (3, 9):
        from zoneinfo import ZoneInfo
    else:
        from pytz import timezone
    # get logger object
    _ = queue_handler_setup(e)
    _iLog = logging.getLogger('info_w')
    _eLog = logging.getLogger('error')

    _worker_name = current_process().name
    _list_summary = [0, 0, 0, 0]
    a[_worker_name] = _list_summary
    _all_revision = list()
    _step_names = set()
    _rev_content = {'origin': '', 'diff': '', 'result': '',
                    'command': '', 'revision': '', 'date_utc': ''}
    _root_path_db = "db"
    # добавить pid, ppid и имя в сообщения из воркеров
    if d[0] != "ssh" and d[0] != "SSH":
        sys.exit(1)

    try:
        # load tasks and calculate steps
        with open("playbook.yaml", "r", encoding="utf8") as plb:
            _tasks = safe_load(plb)

        total_steps = 0
        for task in _tasks:
            if "steps" in _tasks[task]:
                for step in _tasks[task]["steps"]:
                    if _tasks[task]["steps"][step].get("name"):
                        total_steps += 1
            else:
                if _tasks[task]['step'].get("name"):
                    total_steps += 1
        _list_summary[3] = total_steps
        a[_worker_name] = _list_summary

        # result = ssh(ipv4=b, login=d[2], passw=d[3], port=d[4],
        #              cmd="export compact")
        for task_name in _tasks.keys():
            while True:
                _virgin_rev = False
                # check history folder path
                if check_path(_root_path_db):
                    if check_path(f"{_root_path_db}/{_worker_name}"):
                        _all_revision = os.listdir(
                            f"{_root_path_db}/{_worker_name}")

                if d[5] == "Mikrotik":
                    _rev_content['origin'] = get_hash(
                        re.sub("#.+\r", "", get_device_config(
                            (b, d[2], d[3], d[4]), d[5]).decode()))
                elif d[5] == "SNR" or d[5] == "Cisco" or d[5] == "cisco":
                    sys.exit(1)

                r = get_step(_tasks, task_name, _step_names)
                if isinstance(r, list):
                    _step_names = r[1]
                    if len(_all_revision) == 0:
                        _virgin_rev = True
                else:
                    _step_names.clear()
                    break

                if _virgin_rev:
                    _rev_content['revision'] = 1
                    _rev_content['diff'] = get_hash(r[0]["command"])
                else:
                    _rev = 0
                    _prev_rev_name = ""
                    for _item in _all_revision:
                        if _rev < int(_item.split("_")[0]):
                            _rev = int(_item.split("_")[0])
                            _prev_rev_name = _item

                    if len(_prev_rev_name) == 0:
                        sys.exit(1)
                    else:
                        with open(f"{_root_path_db}/{_worker_name}/"
                                  f"{_prev_rev_name}", "r") as _db:
                            _prev_rev = json.load(_db)
                    if int(_prev_rev['revision']) == _rev:
                        _rev_content['revision'] = _rev + 1
                    else:
                        sys.exit(1)

                    _rev_content['diff'] = get_hash(r[0]["command"])
                    if _rev_content['diff'] != _prev_rev['diff']:
                        pass
                    else:
                        _iLog.info("diff is equal to previous")
                        _list_summary[0] = 1
                        a[_worker_name] = _list_summary
                        # sys.exit(1)

                _rev_content['command'] = r[0]['command']
                if d[5] == "Mikrotik":
                    _rev_content['result'] = get_hash(
                        re.sub("#.+\r", "",
                               get_device_config((b, d[2], d[3], d[4]),
                                                 "Mikrotik").decode()))
                else:
                    sys.exit(1)
                _rev_name = f"{_rev_content['revision']}_" \
                            f"{_rev_content['result'][0:16:2]}_" \
                            f"{_rev_content['result'][16::2]}"
                if sys.version_info >= (3, 9):
                    _rev_content['date_utc'] = \
                        datetime.now(ZoneInfo('Asia/Yekaterinburg')
                                     ).strftime('%Y-%m-%d %H:%M:%S%z')
                else:
                    _rev_content['date_utc'] = \
                        datetime.now(timezone('Asia/Yekaterinburg')
                                     ).strftime('%Y-%m-%d %H:%M:%S%z')

                with open(f"{_root_path_db}/{_worker_name}/{_rev_name}", "w",
                          encoding="utf8") as rev_file:
                    json.dump(fp=rev_file, obj=_rev_content)
                # saves the result
                _list_summary[1] = _list_summary[3] - \
                                   _list_summary[0] - _list_summary[2]
                a[_worker_name] = _list_summary

        sleep(randint(1, 4))
        _iLog.info(f'Worker - {current_process().name}')
    except OSError as err:
        _list_summary[2] = _list_summary[3] - \
                           _list_summary[0] + _list_summary[1]
        a[_worker_name] = _list_summary
        _eLog.error(err)
    finally:
        c.release()


def proc_creator(_pconfig: List, plist: List) -> List:
    # _pconfig by index
    # 0 - func name: Dict, 1 - args for process: List,
    # 2 - name for process: Text
    # _pconfig[1] - _var_for_worker by index
    # 0 - tasks_summary: Dict - shared vocabulary between processes.
    #     saves the result.
    # 1 - ip: Text, 2 - block: BoundedSemaphore, 3 - raw_auth_data: Set
    _pconfig[2] = re.sub("\s{1,}", "_", _pconfig[2])
    plist.append(Process(target=_pconfig[0], args=(*_pconfig[1],),
                         name=_pconfig[2]))
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
    # logger setup block
    if args.mode[0] == "CLI":
        from CLI import verify, choose_ip

        queue = Queue(-1)
        listener = Process(target=listener_setup, args=(queue,))
        listener.start()
        root = queue_handler_setup(queue)
    elif args.mode[0] == "API":
        from API import redirect, do_GET, do_POST, web, asyncio

        load_config()
        # _loggers - ['critical', 'error', 'warning', 'info',
        #                 0        1          2        3
        #              'info_w', 'info_h', 'debug', 'root']
        #                 4        5         6        7
        _loggers = logger_generator()
        root = _loggers[3]
    else:
        root = logging.getLogger()

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
                    root.info(msg)
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
                                access_log=root,
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
                        root.info(msg)
                        raise argparse.ArgumentError(None, msg)
                    else:
                        if os.path.exists(args.playbook[0]):
                            resp = verify(filepath=args.playbook[0],
                                          filename="playbook.yaml")
                            if resp == "playbook.yaml is Ok":
                                root.info(f"Verify: {resp}")
                            else:
                                root.info(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[3] + args.playbook[0]
                            root.info(msg)
                            raise FileNotFoundError(msg)

                        if os.path.exists(args.inventory[0]):
                            resp = verify(filepath=args.inventory[0],
                                          filename="inventory.yaml")
                            if resp == "inventory.yaml is Ok":
                                root.info(f"Verify: {resp}")
                            else:
                                root.info(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[2] + args.inventory[0]
                            root.info(msg)
                            raise FileNotFoundError(msg)

                    with open(args.inventory[0], "r", encoding="utf8") as file:
                        data = safe_load(file)

                    #debug prints
                    with Manager() as mgr:
                        block = mgr.BoundedSemaphore(2)
                        tasks_summary: Dict = mgr.dict()
                        _var_for_worker: List = [tasks_summary, "_._._._",
                                                 block, "_auth_data_tpml_",
                                                 queue]
                        _patterns: List[Text] = ["IPv4 адрес не отвечает"]
                        _pList: List = []
                        for i in data:
                            for j in data[i]:
                                if j != "individual":
                                    if j in ["host",
                                             "host_multiple", "host_range"]:
                                        if j == "host_range":
                                            ip, rtt, nextip = \
                                                choose_ip(host_type=j,
                                                          data=data[i][j])
                                            print(ip, rtt, nextip, -2)
                                            if rtt != -1 and rtt >= 0:
                                                _var_for_worker[1] = ip
                                                _var_for_worker[3] = (
                                                    data[i]['protocol'][0],
                                                    data[i]['key'],
                                                    data[i]['login'],
                                                    data[i]['password'],
                                                    data[i]['ssh_port'],
                                                    data[i]['vendor']
                                                )
                                                _pList = proc_creator(
                                                    [_worker, _var_for_worker,
                                                     f"{i}_{ip}"], _pList)
                                            while True:
                                                print(data[i][j], ip)
                                                if ip != data[i][j][1] and \
                                                        ip != _patterns[0]:
                                                    ip, rtt, nextip = \
                                                        choose_ip(host_type=j,
                                                                  data=data[i][
                                                                      j],
                                                                  range_ip=nextip)
                                                else:
                                                    break
                                            print(ip, rtt, nextip, -1)
                                            if rtt != -1 and rtt >= 0:
                                                _var_for_worker[1] = ip
                                                _var_for_worker[3] = (
                                                    data[i]['protocol'][0],
                                                    data[i]['key'],
                                                    data[i]['login'],
                                                    data[i]['password'],
                                                    data[i]['ssh_port'],
                                                    data[i]['vendor']
                                                )
                                                _pList = proc_creator(
                                                    [_worker, _var_for_worker,
                                                     f"{i}_{ip}"], _pList)
                                        else:
                                            ip, rtt, _ = \
                                                choose_ip(host_type=j,
                                                          data=data[i][j])
                                            print(ip, rtt, 1)
                                            if rtt != -1 and rtt >= 0:
                                                _var_for_worker[1] = ip
                                                _var_for_worker[3] = (
                                                    data[i]['protocol'][0],
                                                    data[i]['key'],
                                                    data[i]['login'],
                                                    data[i]['password'],
                                                    data[i]['ssh_port'],
                                                    data[i]['vendor']
                                                )
                                                _pList = proc_creator(
                                                    [_worker, _var_for_worker,
                                                     f"{i}_{ip}"], _pList)
                                else:
                                    for k in data[i][j]:
                                        for z in data[i][j][k]:
                                            # _algo_type is only three values
                                            # host, host_multiple and host_range
                                            _algo_type = data[i][j][k][z]
                                            # _rhd - _raw_host_data
                                            _rhd = data[i][j][k]
                                            if z in ["host", "host_multiple",
                                                     "host_range"]:
                                                if z == "host_range":
                                                    ip, rtt, nextip = choose_ip(
                                                        host_type=z,
                                                        data=_algo_type)
                                                    print(ip, rtt, nextip, 2)
                                                    if rtt != -1 and rtt >= 0:
                                                        _var_for_worker[1] = ip
                                                        _var_for_worker[3] = (
                                                            _rhd['protocol'][
                                                                0],
                                                            _rhd['key'],
                                                            _rhd['login'],
                                                            _rhd['password'],
                                                            _rhd['ssh_port'],
                                                            _rhd['vendor']
                                                        )
                                                        _pList = proc_creator(
                                                            [_worker,
                                                             _var_for_worker,
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
                                                                    host_type=z,
                                                                    data=_algo_type,
                                                                    range_ip=nextip)
                                                        else:
                                                            break
                                                    print(ip, rtt, nextip, 3)
                                                    if rtt != -1 and rtt >= 0:
                                                        _var_for_worker[1] = ip
                                                        _var_for_worker[3] = (
                                                            _rhd['protocol'][
                                                                0],
                                                            _rhd['key'],
                                                            _rhd['login'],
                                                            _rhd['password'],
                                                            _rhd['ssh_port'],
                                                            _rhd['vendor']
                                                        )
                                                        _pList = proc_creator(
                                                            [_worker,
                                                             _var_for_worker,
                                                             f"{i}_{ip}"],
                                                            _pList)
                                                else:
                                                    ip, rtt, _ = choose_ip(
                                                        host_type=z,
                                                        data=_algo_type)
                                                    print(ip, rtt, 4)
                                                    if rtt != -1 and rtt >= 0:
                                                        _var_for_worker[1] = ip
                                                        _var_for_worker[3] = (
                                                            _rhd['protocol'][
                                                                0],
                                                            _rhd['key'],
                                                            _rhd['login'],
                                                            _rhd['password'],
                                                            _rhd['ssh_port'],
                                                            _rhd['vendor']
                                                        )
                                                        _pList = proc_creator(
                                                            [_worker,
                                                             _var_for_worker,
                                                             f"{i}_{ip}"],
                                                            _pList)
                        print("=" * 15)
                        root_h = logging.getLogger('info_h')
                        for _, p in enumerate(_pList):
                            block.acquire()
                            p.start()
                        for idx, p in enumerate(_pList):
                            if p.is_alive():
                                p.join()

                        _ok_status = _changed_status = _error_status = 0
                        _total = 0

                        for _k, v in _var_for_worker[0].items():
                            _ok_status += v[0]
                            _changed_status += v[1]
                            _error_status += v[2]
                            _total += 1
                        sleep(1)
                        msg = "[Work report] "
                        ll = os.get_terminal_size().columns
                        ll -= len(msg) + 6
                        msg += int(ll) * "*"
                        root_h.info(msg)
                        _total1 = _ok_status + _changed_status + _error_status
                        msg2 = f"ok: {_ok_status}, changed: {_changed_status},"\
                               f" error: {_error_status} out of {_total1}" \
                               f" in {_total} processes"
                        root.info(msg2)



                else:
                    msg: Text = msg_patterns[1] + miss_req_args
                    root.info(msg)
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
                        root.info(msg)
                        raise FileNotFoundError(msg)

                    if os.path.exists(args.inventory[0]):
                        pass
                    else:
                        msg: Text = msg_patterns[2] + args.inventory[0]
                        root.info(msg)
                        raise FileNotFoundError(msg)

                else:
                    msg: Text = msg_patterns[1] + miss_req_args
                    root.info(msg)
                    raise argparse.ArgumentError(None, msg)

            elif args.mode[0] == "IPsec":
                print("Mode is developed state now")
        else:
            root.info(msg_patterns[0])

    except FileNotFoundError as err:
        root.info(f"FileNotFoundError: {err}")
    except argparse.ArgumentError as err:
        root.info(f"ArgumentError: {err}")
    except web.HTTPRedirection as err:
        print(err, 1)
    except web.HTTPFound as err:
        print(err, 2)
    except AttributeError as err:
        root.info(f"AttributeError: {err}")
    except Exception as err:
        root.info(f"Exception: {err}")
    finally:
        if args.mode[0] == "CLI":
            queue.put_nowait(None)
