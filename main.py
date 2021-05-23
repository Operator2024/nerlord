__version__ = "0.0.1"

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
import logging.config
import os

import yaml

from API import *

# from node import *
# from task import *
# from API import *


if __name__ == '__main__':
    description = "Network device configuration management system aka Nerlord"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-m", "--mode", type=str, nargs=1, metavar="API/CLI/PINFO/IPsec",
                        required=True)
    messageHelp = "Enter the absolute path to the file "
    parser.add_argument("-i", "--inventory", type=str, nargs=1,
                        metavar="/etc/operator2024/inventory.yaml", required=False,
                        help=messageHelp + "inventory.yaml")
    parser.add_argument("-d", "--devices", type=str, nargs=1,
                        metavar="/etc/operator2024/devices.yaml", required=False,
                        help=messageHelp + "devices.yaml")
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
        if os.path.exists("log_settings.yaml"):
            with open("log_settings.yaml", encoding="utf8") as file:
                log_cfg = yaml.safe_load(file)
        else:
            msg = "File log_settings.yaml not found!"
            raise FileNotFoundError(msg)
        logging.config.dictConfig(log_cfg)
        root = logging.getLogger(name="MainWorker")

        invalidArgs = ""
        missreqArgs = ""
        if args.mode[0] == "API":
            if args.inventory is not None:
                if len(invalidArgs) == 0:
                    invalidArgs += f"{args.inventory[0]}"
                else:
                    invalidArgs += f", {args.inventory[0]}"
            if args.devices is not None:
                if len(invalidArgs) == 0:
                    invalidArgs += f"{args.devices[0]}"
                else:
                    invalidArgs += f", {args.devices[0]}"
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
                app = web.Application()
                app.add_routes([web.get("/api", do_GET)])
                app.add_routes([web.post("/post", do_POST)])
                web.run_app(host="127.0.0.1", port=8080, app=app,
                            access_log=logging.getLogger("info"),
                            access_log_format='%a %t "%{SecureRequest}o" %s %b "%{Referer}i" "%{'
                                              'User-Agent}i"')
        elif args.mode[0] == "CLI":
            if args.inventory is None:
                if len(missreqArgs) == 0:
                    missreqArgs += f" --inventory (-i) "
                else:
                    missreqArgs += f", --inventory (-i) "
            if args.devices is None:
                if len(missreqArgs) == 0:
                    missreqArgs += f" --devices (-d)"
                else:
                    missreqArgs += f", --devices (-d)"

            if args.devices is not None and args.inventory is not None:
                if args.format is not None:
                    if len(invalidArgs) == 0:
                        invalidArgs += f"{args.format[0]}"
                    msg = "Режим CLI не поддерживает указанные аргументы " + invalidArgs
                    logging.getLogger("info").info(msg)
                    raise argparse.ArgumentError(None, msg)
                else:
                    if os.path.exists(args.devices[0]):
                        pass
                    else:
                        msg = f"Конфигурационный файл не был найден по указанному пути" \
                              f" {args.devices[0]}"
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
                msg = "Режим CLI требует следующие аргументы, которые не были получены " + missreqArgs
                logging.getLogger("info").info(msg)
                raise argparse.ArgumentError(None, msg)

        elif args.mode[0] == "PINFO":
            if args.inventory is None:
                if len(missreqArgs) == 0:
                    missreqArgs += f" --inventory (-i) "
                else:
                    missreqArgs += f", --inventory (-i) "
            if args.devices is None:
                if len(missreqArgs) == 0:
                    missreqArgs += f" --devices (-d)"
                else:
                    missreqArgs += f", --devices (-d)"
            if args.format is None:
                if len(missreqArgs) == 0:
                    missreqArgs += f" --format (-f)"
                else:
                    missreqArgs += f", --format (-f)"

            if args.devices is not None and args.inventory is not None and args.format is not None:
                if os.path.exists(args.devices[0]):
                    pass
                else:
                    msg = f"Конфигурационный файл не был найден по указанному пути" \
                          f" {args.devices[0]}"
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

    except FileNotFoundError as err:
        print(f"Exception - {err}")
    except argparse.ArgumentError as err:
        print(f"Exception - {err}")
    finally:
        pass
