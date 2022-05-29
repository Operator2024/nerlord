__version__ = "0.3.10"

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
import sys
from multiprocessing import Manager, Process, Queue, current_process, \
    set_start_method
from sys import version_info
# for tests; remove after
from time import sleep
from typing import Text, List, Dict

from yaml import safe_load

from loggers import listener_setup, queue_handler_setup, \
    load_config, logger_generator, COLORS

if sys.platform != "win32":
    import cryptography.utils
    import warnings
    warnings.simplefilter("ignore",
                          cryptography.utils.CryptographyDeprecationWarning)


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

    from CLI import check_path, get_step, get_hash, get_device_config, ssh

    if sys.version_info >= (3, 9):
        from zoneinfo import ZoneInfo
    else:
        from pytz import timezone
    # get logger object
    _ = queue_handler_setup(e)

    _iLog = logging.getLogger('info_b_con')
    _eLog = logging.getLogger('error')
    _wLog = logging.getLogger('warning')

    _iLog_file = logging.getLogger("info_file")

    _worker_name = current_process().name
    _list_summary = [0, 0, 0, 0]
    a[_worker_name] = _list_summary
    _all_revision = list()
    _step_names = set()
    _rev_content = {'origin': '', 'diff': '', 'result': '',
                    'command': '', 'revision': '', 'date_utc': ''}
    _root_path_db = "db"

    _local_msg = f"Worker '{_worker_name}' started"
    _iLog.info(_local_msg)
    _iLog_file.info(_local_msg)

    # добавить pid, ppid и имя в сообщения из воркеров
    if d[0] != "ssh" and d[0] != "SSH":
        _local_msg = f"Worker is supported only SSH proto, " \
                     f"but was received {d[0]}"
        _eLog.error(_local_msg)
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

        for task_name in _tasks.keys():
            _local_msg = f"Task -> '{task_name}' started, " \
                         f"worker -> '{_worker_name}'"
            _iLog.info(_local_msg)
            _iLog_file.info(_local_msg)

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
                    _local_msg = f"Worker is supported only Mikrotik vendor, " \
                                 f"but was received {d[5]}"
                    _eLog.error(_local_msg)
                    sys.exit(1)

                r = get_step(_tasks, task_name, _step_names)
                if isinstance(r, list):
                    _step_names = r[1]
                    if len(_all_revision) == 0:
                        _virgin_rev = True
                else:
                    _step_names.clear()
                    _local_msg = f"Task -> '{task_name}' ended, " \
                                 f"worker -> '{_worker_name}'"
                    _iLog.info(_local_msg)
                    _iLog_file.info(_local_msg)
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
                        if _prev_rev['result'] != _rev_content['origin']:
                            _wLog.warning("The latest revision is not equal to"
                                          " the current one! "
                                          "Probably something changed, "
                                          f"worker -> {_worker_name}")
                    else:
                        _local_msg = f"The file containing the latest version" \
                                     f" has been modified manually, " \
                                     f"filename - {_prev_rev_name}"
                        _eLog.error(_local_msg)
                        sys.exit(1)

                    _rev_content['diff'] = get_hash(r[0]["command"])
                    if _rev_content['diff'] == _prev_rev['diff']:
                        _local_msg = f"diff is equal to previous"
                        _wLog.warning(_local_msg)
                        _list_summary[0] = 1
                        a[_worker_name] = _list_summary
                        sys.exit(1)

                _rev_content['command'] = r[0]['command']
                if r[0]['output'] == "extend":
                    _local_msg = f"Step name -> '{r[0]['name']}', " \
                                 f"Task -> '{task_name}'"\
                                 f",\n Full step -> " \
                                 f"{json.dumps(r[0], indent=2)}, " \
                                 f"worker -> '{_worker_name}'"
                    _iLog.info(_local_msg)
                    _iLog_file.info(_local_msg)
                else:
                    _local_msg = f"Step name -> '{r[0]['name']}', " \
                                 f"Task -> '{task_name}'"\
                                 f",\n worker -> '{_worker_name}'"
                    _iLog.info(_local_msg)
                    _iLog_file.info(_local_msg)
                if d[5] == "Mikrotik":
                    result = ssh(ipv4=b, login=d[2], password=d[3], port=d[4],
                                 cmd=f"{r[0]['command']}")
                    _rev_content['result'] = get_hash(
                        re.sub("#.+\r", "",
                               get_device_config((b, d[2], d[3], d[4]),
                                                 "Mikrotik").decode()))
                    if _rev_content['result'] == _rev_content['origin']:
                        _list_summary[0] += 1

                    _local_msg = f"Step name -> '{r[0]['name']}', " \
                                 f"Task -> '{task_name}'" \
                                 f",\n Response from device -> " \
                                 f"{result.decode()}, " \
                                 f"worker -> '{_worker_name}'"
                    _iLog.info(_local_msg)
                    _iLog_file.info(_local_msg)
                else:
                    _local_msg = f"Worker is supported only Mikrotik vendor, " \
                                 f"but was received {d[5]}"
                    _eLog.error(_local_msg)
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

                _local_msg = f"Save revision file -> '{_rev_name}', " \
                             f"worker -> '{_worker_name}'"
                _iLog.info(_local_msg)
                _iLog_file.info(_local_msg)

                _list_summary[1] = _list_summary[3] - \
                                   _list_summary[0] - _list_summary[2]
                a[_worker_name] = _list_summary
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
    set_start_method('spawn')
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
    parser.add_argument("--ip", type=str, nargs=1, default="127.0.0.1",
                        help="IPv4 address that exists in your system which "
                             "will bind to the server", metavar="")
    parser.add_argument("--port", type=str, nargs=1, default="8888",
                        help="IPv4 port. Max value is 65535.", metavar="")

    args = parser.parse_args()
    # logger setup block
    if args.mode[0] == "CLI":
        from CLI import verify, choose_ip, get_header, ssh

        queue = Queue(-1)
        listener = Process(target=listener_setup, args=(queue,))
        listener.start()
        root = queue_handler_setup(queue)

        iLog_h_con = logging.getLogger("info_h_con")
        iLog_b_con = logging.getLogger("info_b_con")

        iLog_file = logging.getLogger("info_file")
        eLog = logging.getLogger("error")
    elif args.mode[0] == "API":
        from API import redirect, do_GET, do_POST, web, asyncio

        load_config()
        _loggers = logger_generator()
        root = _loggers[7]
        eLog = _loggers[1]

        _fmt = "%(asctime)s, %(levelname)s: %(message)s"
        _datefmt = "%d-%m-%Y %I:%M:%S %p"
        _style = "%"

        root.handlers[0].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
        root.handlers[1].setFormatter(logging.Formatter(_fmt, _datefmt, _style))
    else:
        print(f"Allowed mode is CLI or API, but not " +
              f"'{COLORS['red']}{args.mode[0]}{COLORS['reset']}'")
        root = iLog_file = iLog_h_con = iLog_b_con =\
            eLog = logging.getLogger()

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
                if "3.7" in py_version and sys.platform == "win32":
                    asyncio.set_event_loop_policy(
                        asyncio.WindowsProactorEventLoopPolicy())
                app = web.Application()
                app.add_routes([web.get("/", redirect)])
                app.add_routes([web.get("/api", do_GET, name="api")])
                app.add_routes([web.get("/post", do_POST)])
                app.add_routes([web.post("/post", do_POST)])
                _access_log_format = '%a %t "%{SecureRequest}o" %s %b ' \
                                     '"%{Referer}i" "%{User-Agent}i" %{text}o'
                if not isinstance(args.ip, list) and\
                        not isinstance(args.port, list):
                    web.run_app(host=args.ip, port=args.port, app=app,
                                access_log=root,
                                access_log_format=_access_log_format)
                elif isinstance(args.ip, list) and\
                        not isinstance(args.port, list):
                    web.run_app(host=args.ip[0], port=args.port, app=app,
                                access_log=root,
                                access_log_format=_access_log_format)
                elif not isinstance(args.ip, list) and\
                        isinstance(args.port, list):
                    web.run_app(host=args.ip, port=args.port[0], app=app,
                                access_log=root,
                                access_log_format=_access_log_format)
                else:
                    web.run_app(host=args.ip[0], port=args.port[0], app=app,
                                access_log=root,
                                access_log_format=_access_log_format)
            elif args.mode[0] == "CLI":
                msg = f"[{args.mode[0]} mode ON] "

                iLog_file.info(get_header(msg, "file"))
                iLog_h_con.info(get_header(msg))

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
                        raise argparse.ArgumentError(None, msg)
                    else:
                        if os.path.exists(args.playbook[0]):
                            resp = verify(filepath=args.playbook[0],
                                          filename="playbook.yaml")
                            if resp == "playbook.yaml is Ok":
                                msg = f"Verified: {resp}"
                                iLog_b_con.info(msg)
                                iLog_file.info(msg)
                            else:
                                eLog.error(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[3] + args.playbook[0]
                            eLog.error(msg)
                            raise FileNotFoundError(msg)

                        if os.path.exists(args.inventory[0]):
                            resp = verify(filepath=args.inventory[0],
                                          filename="inventory.yaml")
                            if resp == "inventory.yaml is Ok":
                                msg = f"Verified: {resp}"
                                iLog_b_con.info(msg)
                                iLog_file.info(msg)
                            else:
                                eLog.info(f"Verify: {resp}")
                                raise Exception(resp)
                        else:
                            msg: Text = msg_patterns[2] + args.inventory[0]
                            eLog.info(msg)
                            raise FileNotFoundError(msg)

                    with open(args.inventory[0], "r", encoding="utf8") as file:
                        data = safe_load(file)

                    msg = "[Detecting available devices by ICMP] wait... "
                    iLog_h_con.info(get_header(msg))
                    iLog_file.info(get_header(msg, "file"))

                    with Manager() as mgr:
                        block = mgr.BoundedSemaphore(2)
                        tasks_summary: Dict = mgr.dict()
                        _var_for_worker: List = [tasks_summary, "_._._._",
                                                 block, "_auth_data_tpml_",
                                                 queue]
                        _patterns: List[Text] = ["IPv4 адрес не отвечает"]
                        _pList: List = []
                        _msg = "Detected IP -> "
                        for i in data:
                            for j in data[i]:
                                if j != "individual":
                                    if j in ["host",
                                             "host_multiple", "host_range"]:
                                        if j == "host_range":
                                            ip, rtt, nextip = \
                                                choose_ip(host_type=j,
                                                          data=data[i][j])

                                            if rtt != -1 and rtt >= 0:
                                                iLog_b_con.info(_msg + ip)
                                                iLog_file.info(_msg + ip)
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
                                                                  range_ip=
                                                                  nextip)
                                                else:
                                                    break

                                            if rtt != -1 and rtt >= 0:
                                                iLog_b_con.info(_msg + ip)
                                                iLog_file.info(_msg + ip)
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

                                            if rtt != -1 and rtt >= 0:
                                                iLog_b_con.info(_msg + ip)
                                                iLog_file.info(_msg + ip)
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

                                                    if rtt != -1 and rtt >= 0:
                                                        iLog_b_con.info(
                                                            _msg + ip)
                                                        iLog_file.info(
                                                            _msg + ip)
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
                                                        if ip != _algo_type[1]\
                                                                and ip != \
                                                                _patterns[0]:
                                                            ip, rtt, nextip = \
                                                                choose_ip(
                                                                    host_type=z,
                                                                    data=
                                                                    _algo_type,
                                                                    range_ip=
                                                                    nextip)
                                                        else:
                                                            break

                                                    if rtt != -1 and rtt >= 0:
                                                        iLog_b_con.info(
                                                            _msg + ip)
                                                        iLog_file.info(
                                                            _msg + ip)
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

                                                    if rtt != -1 and rtt >= 0:
                                                        iLog_b_con.info(
                                                            _msg + ip)
                                                        iLog_file.info(
                                                            _msg + ip)
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

                        msg = f"Detected {len(_pList)} device(s) "
                        iLog_b_con.info(msg)
                        iLog_file.info(msg)

                        msg = "[Task(s) processing started] "
                        iLog_h_con.info(get_header(msg))
                        iLog_file.info(get_header(msg, "file"))
                        sleep(1)

                        for _, p in enumerate(_pList):
                            block.acquire()
                            p.start()
                        for idx, p in enumerate(_pList):
                            if p.is_alive():
                                p.join()

                        _ok_status = _changed_status = _error_status = 0
                        _total = _total_task = 0

                        for _k, v in _var_for_worker[0].items():
                            _ok_status += v[0]
                            _changed_status += v[1]
                            _error_status += v[2]
                            if v[0] or v[1] or v[2] != 0:
                                _total += 1
                        sleep(1)

                        _total_task = _ok_status + _changed_status +\
                                      _error_status
                        msg = "[Work report] "
                        iLog_h_con.info(get_header(msg))
                        iLog_file.info(get_header(msg, "file"))

                        iLog_b_con.info(f"{COLORS['green']}ok: {_ok_status},"
                                        f" {COLORS['reset']}{COLORS['yellow']} "
                                        f"changed: {_changed_status},"
                                        f"{COLORS['reset']}{COLORS['red']} "
                                        f"error: {_error_status}"
                                        f"{COLORS['reset']}{COLORS['green']} "
                                        f"out of {_total_task} in {_total} "
                                        f"processes")
                        iLog_file.info(f"ok: {_ok_status}, changed: "
                                         f"{_changed_status}, error: "
                                         f"{_error_status} out of {_total_task}"
                                         f" in {_total} processes")
                else:
                    msg: Text = msg_patterns[1] + miss_req_args
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
        eLog.error(f"FileNotFoundError: {err}")
    except argparse.ArgumentError as err:
        eLog.error(f"ArgumentError: {err}")
    except AttributeError as err:
        eLog.error(f"AttributeError: {err}")
    except Exception as err:
        eLog.error(f"Exception: {err}")
    finally:
        if args.mode[0] == "CLI":
            iLog_file.info("*" * 51)
            queue.put_nowait(None)
