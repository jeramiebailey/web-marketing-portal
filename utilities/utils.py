import aiohttp
import asyncio
import async_timeout
from bs4 import BeautifulSoup, SoupStrainer
import re
from urllib.parse import urlparse

class BrokenLinkChecker:
    def __init__(self, url):
        self.url = url

    async def fetch(self, session, url):
        async with async_timeout.timeout(20):
            async with session.get(url) as response:
                try:
                    return await response.text()
                except:
                    # print(response)
                    pass

    async def fetch_status(self, session, url):
        async with async_timeout.timeout(20):
            async with session.get(url) as response:
                # print(response)
                return response.status

    async def soup_d(self, html, display_result=False):
        soup = BeautifulSoup(html, 'html.parser')
        if display_result:
            print(soup.prettify())
        return soup


    async def extract_local_links(self, html, root_domain, post_url, local_only=True):
        soup = await self.soup_d(html)
        href_tags = soup.find_all("a", href=True)
        links = [a['href'] for a in href_tags]
        if local_only:
            for x in links:
                if urlparse(x).netloc == root_domain or x.startswith('/'):
                    link = urlparse(x).path
                    if link not in checked_links:
                        checked_links.append(link)
                        print(link)
                        # print(f'parent_url is {post_url}')
                        hyperlinks.append({
                            'parent_url': post_url,
                            'link': link,
                        })
        return hyperlinks


    async def get_all_links(self):
        async with aiohttp.ClientSession() as session:
            parsed_url = urlparse(self.url)
            root_domain = parsed_url.netloc
            domain = parsed_url.geturl()
            if domain.endswith('/'):
                domain = domain[:-1]
            html = await self.fetch(session, self.url)
            paths = await self.extract_local_links(html, root_domain, self.url)
            for path in hyperlinks:
                post_url  = domain + path['link']
                # print(post_url)
                new_search = await self.fetch(session, post_url)
                try:
                    all_links = await self.extract_local_links(new_search, root_domain, post_url)
                except:
                    all_links = None

    async def get_status_codes(self):
        async with aiohttp.ClientSession() as session:
            parsed_url = urlparse(self.url)
            domain = parsed_url.geturl()
            if domain.endswith('/'):
                domain = domain[:-1]
            for path in hyperlinks:
                post_url = domain + path['link']
                # print(f'post_url is {post_url}')
                status_code = await self.fetch_status(session, post_url)
                print(f'status of {post_url} is: {status_code}')
                report.append({
                    'parent': path['parent_url'],
                    'url': path['link'],
                    'status': status_code
                })

    async def main(self):
        global hyperlinks, report, checked_links
        hyperlinks = []
        checked_links = []
        report = []
        await self.get_all_links()
        await self.get_status_codes()
        # print(report)
        return report


    def run(self):
        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # output = loop.run_until_complete(self.main())
        try:
            output = loop.run_until_complete(self.main())
        except:
            print('error')
            output = None
            pass
        return output