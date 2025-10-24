# Backend/tools/web_vuln_scanner.py
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Set

class WebVulnScanner:
    def __init__(self, target: str, timeout: int = 10, user_agent: str = None):
        self.target = target.strip().rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or "Torii-Project/1.0"
        })
        self.results = []
        self.discovered_paths: Set[str] = set()

    def check_common_paths(self) -> None:
        common_paths = [
            "/admin", "/login", "/dashboard", "/wp-login.php", "/phpmyadmin",
            "/.git", "/.env", "/backup", "/config.php", "/robots.txt"
        ]
        for path in common_paths:
            url = self.target + path
            try:
                r = self.session.head(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 200 or r.status_code == 301:
                    self.results.append({
                        "vulnerability": "Exposed Sensitive Path",
                        "url": url,
                        "issue": f"Accessible: {path}",
                        "severity": "Medium"
                    })
                    self.discovered_paths.add(path)
            except requests.RequestException:
                continue

    def check_clickjacking(self) -> None:
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            headers = r.headers
            if not headers.get("X-Frame-Options") and not headers.get("Content-Security-Policy"):
                self.results.append({
                    "vulnerability": "Clickjacking",
                    "url": self.target,
                    "issue": "Missing X-Frame-Options or CSP",
                    "severity": "Medium"
                })
        except requests.RequestException:
            pass

    def check_xss_reflected(self) -> None:
        xss_payload = "<script>alert(document.domain)</script>"
        # Crawl forms
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            soup = BeautifulSoup(r.content, 'html.parser')
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '').strip("/")
                method = form.get('method', 'get').lower()
                action_url = urljoin(self.target, "/" + action)
                inputs = form.find_all(['input', 'textarea'])
                data = {}
                for inp in inputs:
                    name = inp.get('name') or "dummy"
                    data[name] = xss_payload
                try:
                    if method == 'post':
                        resp = self.session.post(action_url, data=data, timeout=self.timeout)
                    else:
                        resp = self.session.get(action_url, params=data, timeout=self.timeout)
                    if xss_payload in resp.text:
                        self.results.append({
                            "vulnerability": "Reflected XSS",
                            "url": action_url,
                            "issue": f"Payload echoed in response",
                            "severity": "High"
                        })
                except:
                    continue
        except:
            pass

    def check_sql_injection(self) -> None:
        sqli_payload = "' OR 1=1 --"
        parsed = urlparse(self.target)
        if parsed.query:
            for param in parsed.query.split("&"):
                if "=" in param:
                    k = param.split("=")[0]
                    payloads = [sqli_payload, "' OR 'a'='a"]
                    for pay in payloads:
                        params = {k: pay}
                        try:
                            r = self.session.get(self.target, params=params, timeout=self.timeout)
                            errors = ["syntax error", "mysql_fetch", "ORA-", "SQL error"]
                            if any(err in r.text.lower() for err in errors):
                                self.results.append({
                                    "vulnerability": "Possible SQLi",
                                    "url": r.url,
                                    "issue": f"Database error in response",
                                    "severity": "High"
                                })
                                break
                        except:
                            continue

    def check_server_version(self) -> None:
        try:
            r = self.session.get(self.target, timeout=self.timeout)
            server = r.headers.get("Server", "")
            if "apache" in server.lower() and "mod_security" not in r.text.lower():
                self.results.append({
                    "vulnerability": "Exposed Server Banner",
                    "url": self.target,
                    "issue": f"Server: {server}",
                    "severity": "Low"
                })
        except:
            pass

    def enumerate_paths(self) -> None:
        # Simple extension-based brute
        extensions = ["", ".bak", ".old", ".backup", ".zip", ".tar.gz"]
        found = set()
        for path in list(self.discovered_paths):
            base = self.target + path
            for ext in extensions:
                url = base + ext
                try:
                    r = self.session.head(url, timeout=3)
                    if r.status_code == 200:
                        found.add(url)
                        self.results.append({
                            "vulnerability": "Backup File Leak",
                            "url": url,
                            "issue": f"Backup file exposed: {path}{ext}",
                            "severity": "High"
                        })
                except:
                    continue

    def run(self) -> List[Dict]:
        print(f"[+] Scanning {self.target}...")
        self.check_common_paths()
        time.sleep(1)
        self.check_clickjacking()
        time.sleep(1)
        self.check_xss_reflected()
        time.sleep(1)
        self.check_sql_injection()
        time.sleep(1)
        self.check_server_version()
        time.sleep(1)
        self.enumerate_paths()

        print(f"[+] Found {len(self.results)} issue(s)")
        return self.results

# CLI usage:
# if __name__ == "__main__":
#     scanner = WebVulnScanner("http://example.com")
#     for issue in scanner.run():
#         print(f"{issue['severity']} - {issue['vulnerability']}: {issue['url']}")