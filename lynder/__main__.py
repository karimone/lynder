import argparse
import os

from .downloader import dispatcher
from .settings import settings


def parse_arguments():
    parser = argparse.ArgumentParser(description='Lynda Tutorial Downloader')
    parser.add_argument('-u', '--url', dest="url", action='store', help="Url to download")
    parser.add_argument('-f', '--file', dest="file", action='store',
                        help="File to load the urls from")
    parser.add_argument('-d', '--dir', dest="download_dir", action='store',
                        help="Download directory")
    parser.add_argument('-c', '--cookies', dest="cookies", action='store', help="Cookie file")
    parser.add_argument('-w', '--worker', nargs=1, dest="worker", action='store', help="")
    parser.add_argument('-s', '--silent', dest="silent", action='store', default=None)
    return parser.parse_args()


parser = parse_arguments()


if parser.cookies:
    settings.COOKIES = os.path.abspath(parser.cookies)
    print("Cookies location: " + settings.COOKIES)
else:
    settings.USERNAME = input("Lynda Username: ")
    settings.PASSWORD = input("Lynda Password: ")

if parser.worker:
    settings.WORKER_NUM = int(parser.worker[0])

if parser.silent:
    settings.SILENT = parser.silent

print("Number of workers is: ", settings.WORKER_NUM)

if parser.file:
    urls = open(parser.file, 'r')
    # for url in urls:
    #     download_tutorial(url.strip())
    dispatcher(urls)

else:
    if parser.url:
        url = parser.url
    else:
        url = input("URL of tutorial: ")
        dispatcher(url)
    # download_tutorial(url)
