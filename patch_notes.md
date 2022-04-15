# Patch notes 0.2.8-beta.1 (04.15.2022)
## Module [API]
- Minor edits related to added new functional to 'loggers.py' module

## Module [CLI]
- Nothing

## Module [main]
- Code is optimized according to **[PEP8]**
- Added new features that provide thread safety when using multi-thread loggers

## Module [loggers]
- Was changed the main logic of work
- Added new features to enable more detailed logging
- Added "CustomFilter", queue-based listener, and handler to allow inter-thread communication
- Code is optimized according to **[PEP8]**

# Patch notes 0.1.7-beta.1 (04.07.2022)
## Module [API]
- Nothing

## Module [CLI]
- Fixed a bug to which command "ping" returned the wrong result with local addresses (IPv4 private ranges)

## Module [main]
- Code is optimized according to **[PEP8]**
- Added '_var_for_worker' - a list of data items for parallel workers
- Functions 'proc_creator' and '_worker' have been improved
- Added new features that provide multi-core works in CLI mode


# Patch notes 0.1.6 (04.02.2022)
## Module [API]
- Code is optimized according to **[PEP8]**

## Module [CLI]
- Code is optimized according to **[PEP8]** (only functions '**verify**' and '**choose_ip**')

## Module [main]
- Code is optimized according to **[PEP8]**
- Added 'msg_pattern' - a list of messages that can repeat periodically
- Added new features that provide multi-core works in CLI mode

[PEP8]: <https://peps.python.org/pep-0008/>
[API]: <https://github.com/Operator2024/nerlord/blob/master/API.py>
[CLI]: <https://github.com/Operator2024/nerlord/blob/master/CLI.py>
[main]: <https://github.com/Operator2024/nerlord/blob/master/main.py>
[loggers]: <https://github.com/Operator2024/nerlord/blob/master/loggers.py>
