
                           ███    ██ ███████ ██████  ██       ██████  ██████  ██████  
                           ████   ██ ██      ██   ██ ██      ██    ██ ██   ██ ██   ██ 
                           ██ ██  ██ █████   ██████  ██      ██    ██ ██████  ██   ██ 
                           ██  ██ ██ ██      ██   ██ ██      ██    ██ ██   ██ ██   ██ 
                           ██   ████ ███████ ██   ██ ███████  ██████  ██   ██ ██████  
---
<p align="center">
<br>
<img height="20" alt="python supported version" src="shields/pythonversion.svg">
<a href="/doc/index.html"><img height="20" alt="project documentation" src="shields/docs-clickme-success.svg"></a>
</p>

## How to use

### Docker

1. Create network `docker network create --subnet 172.18.0.0/24 --gateway 172.18.0.1 -d bridge mynet`
2. Build [**Dockerfile**](https://github.com/Operator2024/nerlord/tree/build_0_3_X/docker/dockerfile) `docker build -t nerlord:1.0.0 .`
3. Run built image `docker run -d -p 8888:8888/tcp -m 512M --memory-swap 512M  --network mynet 
--ip 172.18.0.254 nerlord:1.0.0 ` 
or in **CLI mode** `docker run -d -p 8888:8888/tcp -m 512M --memory-swap 512M  --network mynet
--ip 172.18.0.254 -v /path/to/inventory.yaml:/nerlord/inventory.yaml 
-v /path/to/playbook.yaml:/nerlord/playbook.yaml -e MODE="CLI" nerlord:1.0.0 `

> ⚠️ Default **port** in API mode '**8888**', 
> **ip** (value saved variable environment 'IP'): '**172.17.0.2**'

### Not docker

1. Clone this repo
2. Install **python3.7+** and all dependencies from file `requirements.txt`
3. Run `python3 main.py -h`

## License

See the **[LICENSE](LICENSE)** file for license right and limitations (MIT)

## Patch notes

Sea the **[Patch notes](patch_notes.md)**
