from colorama import Fore, init, Style
import aiohttp
import asyncio
import random
import os
from typing import List, Optional

init(autoreset=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

class GitHubChecker:
    def __init__(self):
        self.available_count = 0
        self.taken_count = 0
        self.retries = 3
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.concurrency = 5
        self.available_list = []  # Store available usernames

    async def check_username(self, session: aiohttp.ClientSession, username: str) -> Optional[bool]:
        url = f"https://github.com/{username}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

        for attempt in range(self.retries):
            try:
                async with session.get(url, headers=headers, allow_redirects=False) as response:
                    if response.status == 404:
                        return True
                    elif response.status == 200:
                        return False
                    elif response.status == 429:
                        delay = int(response.headers.get("Retry-After", 10))
                        print(f"{Fore.YELLOW}Rate limited. Retrying after {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    return None
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"{Fore.RED}Error checking {username}: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        
        return None

    async def worker(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        while True:
            username = await queue.get()
            try:
                result = await self.check_username(session, username)
                if result is True:
                    self.available_count += 1
                    self.available_list.append(username)
                    print(f"{Fore.GREEN}[+] Available: {username}")
                elif result is False:
                    self.taken_count += 1
                    print(f"{Fore.RED}[-] Taken: {username}")
                else:
                    print(f"{Fore.YELLOW}[?] Unknown status for {username}")
            finally:
                queue.task_done()

    async def run(self, usernames: List[str]):
        queue = asyncio.Queue()
        for username in usernames:
            await queue.put(username.strip())

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            workers = [
                asyncio.create_task(self.worker(session, queue))
                for _ in range(self.concurrency)
            ]
            
            await queue.join()
            
            for worker_task in workers:
                worker_task.cancel()

    def print_stats(self):
        print(f"\n{Fore.CYAN}Check complete!")
        print(f"{Fore.GREEN}Available: {self.available_count}")
        print(f"{Fore.RED}Taken: {self.taken_count}")
        
        if self.available_list:
            print(f"\n{Fore.CYAN}Available Usernames:")
            for idx, username in enumerate(self.available_list, 1):
                print(f"{Fore.WHITE}{idx}. {username}")
        
        print(Style.RESET_ALL)

def print_banner():
    print(f"""{Fore.LIGHTBLUE_EX}
 ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗     ███████╗███╗   ██╗██╗██████╗ ███████╗██████╗ 
██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝████╗  ██║██║██╔══██╗██╔════╝██╔══██╗
██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ███████╗██╔██╗ ██║██║██████╔╝█████╗  ██████╔╝
██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ╚════██║██║╚██╗██║██║██╔═══╝ ██╔══╝  ██╔══██╗
╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ███████║██║ ╚████║██║██║     ███████╗██║  ██║
 ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝     ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                               
Made by- $ @hzcv on Github , @metaloses on Instagram
{Fore.RESET}""")

def main():
    print_banner()
    
    input_file = "usernames.txt"
    if not os.path.exists(input_file):
        print(f"{Fore.RED}Error: {input_file} not found!")
        return

    with open(input_file, "r") as f:
        usernames = f.readlines()

    print(f"{Fore.YELLOW}Starting check for {len(usernames)} usernames...\n")
    
    checker = GitHubChecker()
    asyncio.run(checker.run(usernames))
    checker.print_stats()

if __name__ == "__main__":
    main()
