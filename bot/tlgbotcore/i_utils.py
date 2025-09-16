"""
 my ulitites
 Author: Ilnur Sayfutdinov
 E-mail: ilnursoft@gmail.com
"""

import requests
import aiohttp
import asyncio
import logging
from typing import Optional, Tuple
from pathlib import Path


# преобразование строки вида "SAMSUNG a50 64\\xd0\\xb3\\xd0\\xb1" в строку c кодировкой encoding
def string_escape(s, encoding="utf-8"):
    import codecs
    byte_s = bytes(s, encoding)
    res = codecs.escape_decode(byte_s)[0]
    res = res.decode(encoding) if isinstance(res, bytes) else str(res)
    return res


# сохранить в файл html из urls (синхронная версия)
# True - если смогли получить данные с запроса и сохранить в файл
def savefile_from_url(urls: Optional[str] = None, filename: str = "test.html", timeout: int = 10) -> bool:
    if urls is None:
        logging.warning("URL is None")
        return False
    
    session = requests.Session()
    try:
        r = session.get(urls, timeout=timeout)
        logging.info("GET %s -> %s", urls, r.status_code)
        if r.status_code == 200:
            html = r.text
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            return True
        else:
            logging.warning("HTTP %s for %s", r.status_code, urls)
            return False
    except requests.RequestException as exc:
        logging.exception("Request failed for %s: %s", urls, exc)
        return False
    finally:
        session.close()


# асинхронная версия сохранения файла из URL
async def async_savefile_from_url(urls: Optional[str] = None, filename: str = "test.html", timeout: int = 10) -> bool:
    if urls is None:
        logging.warning("URL is None")
        return False
    
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    try:
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.get(urls) as response:
                logging.info("GET %s -> %s", urls, response.status)
                if response.status == 200:
                    html = await response.text()
                    Path(filename).parent.mkdir(parents=True, exist_ok=True)
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html)
                    return True
                else:
                    logging.warning("HTTP %s for %s", response.status, urls)
                    return False
    except aiohttp.ClientError as exc:
        logging.exception("Async request failed for %s: %s", urls, exc)
        return False
    except asyncio.TimeoutError:
        logging.error("Timeout for %s after %s seconds", urls, timeout)
        return False


# запуск команды cmd asyncio
async def run_cmd(cmd: str, timeout: Optional[int] = 30) -> Tuple[bytes, bytes, int]:
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), 
            timeout=timeout
        )

        logging.info("Command exited: %r -> %s", cmd, proc.returncode)
        if stdout:
            logging.debug("stdout: %s", stdout.decode(errors="replace"))
        if stderr:
            logging.debug("stderr: %s", stderr.decode(errors="replace"))

        return stdout, stderr, proc.returncode or 0
    
    except asyncio.TimeoutError:
        logging.error("Command timeout after %s seconds: %r", timeout, cmd)
        if 'proc' in locals():
            proc.terminate()
            await proc.wait()
        return b"", b"Command timeout", -1
    except Exception as exc:
        logging.exception("Command failed: %r -> %s", cmd, exc)
        return b"", str(exc).encode(), -1
