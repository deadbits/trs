import iocextract

from .schema import Indicators


def update_iocs(iocs, ext_func, content, defang=False):
    for ioc in ext_func(content, defang=defang):
        if ioc not in iocs:
            iocs.append(ioc)


def extract_iocs(content: str):
    iocs = Indicators(
        ips=[],
        urls=[],
        hashes=[]
    )

    update_iocs(iocs.ips, iocextract.extract_ipv4s, content)
    update_iocs(iocs.urls, iocextract.extract_urls, content, defang=True)
    update_iocs(iocs.hashes, iocextract.extract_hashes, content)

    return iocs
