import re
import socket
import requests
import whois
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urlparse
from datetime import datetime
import warnings

# Suppress XML warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def having_ip_address(url: str) -> int:
    try:
        ip = re.findall(r"[0-9]+(?:\.[0-9]+){3}", url)
        return 1 if ip else 0
    except Exception:
        return 0


def url_length(url: str) -> int:
    return len(url)


def shortening_service(url: str) -> int:
    shortening_services = r"(bit\.ly|goo\.gl|tinyurl\.com|ow\.ly|t\.co)"
    return 1 if re.search(shortening_services, url) else 0


def having_at_symbol(url: str) -> int:
    return 1 if "@" in url else 0


def double_slash_redirecting(url: str) -> int:
    # should only count after protocol
    try:
        return 1 if url.rfind("//") > 6 else 0
    except Exception:
        return 0


def prefix_suffix(url: str) -> int:
    try:
        return 1 if "-" in urlparse(url).netloc else 0
    except Exception:
        return 0


def having_sub_domain(url: str) -> int:
    try:
        hostname = urlparse(url).hostname
        return hostname.count(".") - 1 if hostname else 0
    except Exception:
        return 0


def ssl_final_state(url: str) -> int:
    try:
        return 1 if urlparse(url).scheme == "https" else 0
    except Exception:
        return 0


def favicon_from_soup(soup: BeautifulSoup) -> int:
    try:
        icon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        return 1 if icon else 0
    except Exception:
        return 0


def domain_registration_length_from_who(w) -> int:
    try:
        exp = getattr(w, "expiration_date", None)
        if isinstance(exp, list):
            exp = exp[0]
        if exp:
            return (exp - datetime.now()).days
    except Exception:
        return -1
    return -1


def abnormal_url_from_who(w) -> int:
    try:
        return 0 if getattr(w, "domain_name", None) else 1
    except Exception:
        return 1


def age_of_domain_from_who(w) -> int:
    try:
        creation = getattr(w, "creation_date", None)
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            return (datetime.now() - creation).days
    except Exception:
        return -1
    return -1


def dns_record(domain: str) -> int:
    try:
        socket.gethostbyname(domain)
        return 1
    except Exception:
        return 0


def request_url_from_soup(soup: BeautifulSoup, domain: str) -> int:
    try:
        imgs = soup.find_all("img")
        total = len(imgs)
        external = sum(1 for i in imgs if domain not in str(i))
        if total == 0:
            return 0
        ratio = external / total
        if ratio < 0.22:
            return 1
        elif ratio < 0.61:
            return 0
        else:
            return -1
    except Exception:
        return 0


def url_of_anchor_from_soup(soup: BeautifulSoup, domain: str) -> int:
    try:
        anchors = soup.find_all("a")
        total = len(anchors)
        external = sum(1 for a in anchors if domain not in str(a))
        if total == 0:
            return 0
        ratio = external / total
        if ratio < 0.31:
            return 1
        elif ratio < 0.67:
            return 0
        else:
            return -1
    except Exception:
        return 0


def links_in_tags_from_soup(soup: BeautifulSoup, domain: str) -> int:
    try:
        tags = soup.find_all(["link", "script", "meta"])
        total = len(tags)
        external = sum(1 for t in tags if domain not in str(t))
        if total == 0:
            return 0
        ratio = external / total
        if ratio < 0.17:
            return 1
        elif ratio < 0.81:
            return 0
        else:
            return -1
    except Exception:
        return 0


def sfh_from_soup(soup: BeautifulSoup) -> int:
    try:
        forms = soup.find_all("form")
        for f in forms:
            action = f.get("action")
            if action in [None, "", "about:blank"]:
                return -1
        return 1
    except Exception:
        return 0


def submitting_to_email_from_text(text: str) -> int:
    try:
        return 1 if "mailto:" in text else 0
    except Exception:
        return 0


def redirect_from_resp(resp: requests.Response) -> int:
    try:
        return len(getattr(resp, "history", []) or [])
    except Exception:
        return 0


def on_mouseover_from_text(text: str) -> int:
    try:
        return 1 if "onmouseover" in text else 0
    except Exception:
        return 0


def right_click_from_text(text: str) -> int:
    try:
        return 1 if "event.button==2" in text else 0
    except Exception:
        return 0


def popup_window_from_text(text: str) -> int:
    try:
        return 1 if "window.open" in text else 0
    except Exception:
        return 0


def iframe_from_text(text: str) -> int:
    try:
        return 1 if "<iframe" in text else 0
    except Exception:
        return 0


# Placeholder for unavailable APIs

def web_traffic(url: str) -> int:
    return 0


def page_rank(url: str) -> int:
    return 0


def google_index(url: str) -> int:
    return 0


def links_pointing_to_page(url: str) -> int:
    return 0


def statistical_report(url: str) -> int:
    return 0


def fetch_page(url: str):
    try:
        resp = requests.get(url, timeout=3, allow_redirects=True)
        text = resp.text if hasattr(resp, "text") else ""
        soup = BeautifulSoup(text, "html.parser")
        return resp, text, soup
    except Exception:
        return None, "", BeautifulSoup("", "html.parser")


# -------- Extract All Features -------- #

def extract_features(url: str) -> dict:
    parsed = urlparse(url)
    domain = parsed.netloc
    resp, text, soup = fetch_page(url)
    try:
        w = whois.whois(domain)
    except Exception:
        w = type("W", (), {})()
    return {
        "having_IP_Address": having_ip_address(url),
        "URL_Length": url_length(url),
        "Shortining_Service": shortening_service(url),
        "having_At_Symbol": having_at_symbol(url),
        "double_slash_redirecting": double_slash_redirecting(url),
        "Prefix_Suffix": prefix_suffix(url),
        "having_Sub_Domain": having_sub_domain(url),
        "SSLfinal_State": ssl_final_state(url),
        "Domain_registeration_length": domain_registration_length_from_who(w),
        "Favicon": favicon_from_soup(soup),
        "port": 1 if ":" in domain else 0,
        "HTTPS_token": 1 if "https" in domain else 0,
        "Request_URL": request_url_from_soup(soup, domain),
        "URL_of_Anchor": url_of_anchor_from_soup(soup, domain),
        "Links_in_tags": links_in_tags_from_soup(soup, domain),
        "SFH": sfh_from_soup(soup),
        "Submitting_to_email": submitting_to_email_from_text(text),
        "Abnormal_URL": abnormal_url_from_who(w),
        "Redirect": redirect_from_resp(resp) if resp is not None else 0,
        "on_mouseover": on_mouseover_from_text(text),
        "RightClick": right_click_from_text(text),
        "popUpWidnow": popup_window_from_text(text),
        "Iframe": iframe_from_text(text),
        "age_of_domain": age_of_domain_from_who(w),
        "DNSRecord": dns_record(domain),
        "web_traffic": web_traffic(url),
        "Page_Rank": page_rank(url),
        "Google_Index": google_index(url),
        "Links_pointing_to_page": links_pointing_to_page(url),
        "Statistical_report": statistical_report(url),
    }
