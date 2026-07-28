import urllib.request
import urllib.parse
import html
import re
from html.parser import HTMLParser
from jarvis_x.skills.base import BaseSkill
from jarvis_x.core.config import Config


class WebTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []
        self.current_tag = None
        self.ignored_tags = {'script', 'style', 'head', 'title', 'meta', 'link', 'noscript'}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()

    def handle_endtag(self, tag):
        if self.current_tag == tag.lower():
            self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.ignored_tags:
            if data and data.strip():
                self.fragments.append(data.strip())

    def get_text(self) -> str:
        return "\n".join(self.fragments)


class WebSkill(BaseSkill):
    name = "web"
    description = "Web scraping, searching, and internet learning"

    def handle_web_scrape(self, intent):
        url = intent.entities.get("url", "")
        if not url:
            return "Please provide a valid URL to scrape."

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            parser = WebTextExtractor()
            parser.feed(content)
            extracted_text = parser.get_text()

            # Learn from this text
            learned_count = self._learn_from_text(extracted_text, source=url)
            
            # Rebuild AI index
            self.engine.local_ai.rebuild_index()

            snippet = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
            return (
                f"Successfully scraped content from {url}.\n"
                f"Learned {learned_count} facts/sentences from the page.\n\n"
                f"Preview:\n{snippet}"
            )

        except Exception as e:
            return f"Failed to scrape {url}: {e}"

    def handle_web_learn(self, intent):
        query = intent.entities.get("query", "")
        if not query:
            return "Please specify what you want me to search and learn about."

        # Step 1: Search DuckDuckGo html
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        try:
            req = urllib.request.Request(
                search_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                search_html = response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Failed to connect to search engine: {e}"

        # Step 2: Extract top external links
        # DuckDuckGo HTML results use uddg=... parameter inside search link hrefs
        matches = re.findall(r'uddg=(https?%3A%2F%2F[^\s&"]+)', search_html)
        urls = []
        for m in matches:
            decoded_url = urllib.parse.unquote(m)
            if not any(domain in decoded_url for domain in ['duckduckgo.com', 'yahoo.com', 'google.com']):
                urls.append(decoded_url)

        urls = list(dict.fromkeys(urls))[:2]  # Get top 2 unique URLs to scrape
        
        # Also extract text directly from the search snippets to learn quickly
        parser = WebTextExtractor()
        parser.feed(search_html)
        search_page_text = parser.get_text()
        learned_count = self._learn_from_text(search_page_text, source="ddg_snippets")

        scraped_sources = []
        # Step 3: Scrape the top URLs
        for url in urls:
            try:
                sub_req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
                    }
                )
                with urllib.request.urlopen(sub_req, timeout=8) as sub_res:
                    sub_html = sub_res.read().decode('utf-8', errors='ignore')
                
                sub_parser = WebTextExtractor()
                sub_parser.feed(sub_html)
                page_text = sub_parser.get_text()
                
                count = self._learn_from_text(page_text, source=url)
                learned_count += count
                scraped_sources.append(url)
            except Exception:
                continue

        # Rebuild AI index so the new knowledge is immediately searchable
        self.engine.local_ai.rebuild_index()

        sources_str = ", ".join(scraped_sources) if scraped_sources else "search page snippets"
        return (
            f"Search & Learn completed for query: '{query}'.\n"
            f"Sources learned from: {sources_str}.\n"
            f"Successfully learned and indexed {learned_count} new facts into my local Knowledge Base!"
        )

    def _learn_from_text(self, text: str, source: str) -> int:
        if not text:
            return 0

        count = 0
        # Clean up whitespace
        text = html.unescape(re.sub(r'\s+', ' ', text)).strip()
        # Split into sentences using a simple sentence boundary pattern
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            clean = sentence.strip()
            # Filter out short, overly long or uninformative sentences
            if len(clean) < 40 or len(clean) > 350:
                continue
            # Avoid sentences that look like navigation/web UI headers/footers
            if any(w in clean.lower() for w in [
                "cookie", "sign up", "log in", "subscribe", "privacy policy", 
                "terms of service", "all rights reserved", "contact us", "copyright",
                "javascript is disabled", "enable cookies", "web browser"
            ]):
                continue
            
            # Create a query key from the first few words to represent the concept/question
            words = clean.split()
            key = ' '.join(words[:8]).lower()
            if len(key) < 15:
                continue
                
            # Learn the fact in local Knowledge Base
            self.engine.kb.learn(key, clean, confidence=0.7)
            self.engine.kb.log_learning('web_learn', f"{source}: {key}")
            count += 1
        return count


def register(engine, plugin_manager):
    skill = WebSkill(engine, plugin_manager)
    plugin_manager.register_skill("web_scrape", skill.handle_web_scrape)
    plugin_manager.register_skill("web_learn", skill.handle_web_learn)
