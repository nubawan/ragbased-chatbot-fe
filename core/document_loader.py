"""
Z.M.ai - Document Loader

Handles loading and extracting text from:
- PDF files (using pypdf and pdfplumber)
- Web pages (using trafilatura)
"""

import io
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import pypdf
import pdfplumber
import trafilatura
import requests
from bs4 import BeautifulSoup

from config import get_data_source_config

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a loaded document with its metadata."""
    content: str
    source: str
    source_type: str  # "pdf" or "web"
    page_numbers: Optional[List[int]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def __len__(self) -> int:
        return len(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "page_numbers": self.page_numbers,
            "metadata": self.metadata,
        }


class PDFLoader:
    """Loads text content from PDF files."""

    def __init__(self):
        self.config = get_data_source_config()

    def load_from_path(self, file_path: str | Path) -> List[Document]:
        """
        Load PDF from file path.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of Document objects, one per page

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

        logger.info(f"Loading PDF from: {file_path}")

        try:
            # Try pdfplumber first (better text extraction)
            return self._load_with_pdfplumber(file_path)
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying pypdf: {e}")
            return self._load_with_pypdf(file_path)

    def load_from_bytes(self, pdf_bytes: bytes, source_name: str = "uploaded.pdf") -> List[Document]:
        """
        Load PDF from bytes (for uploaded files).

        Args:
            pdf_bytes: PDF file content as bytes
            source_name: Name to use as source identifier

        Returns:
            List of Document objects, one per page
        """
        logger.info(f"Loading PDF from bytes: {source_name}")

        try:
            # Try pdfplumber first
            return self._load_with_pdfplumber_bytes(pdf_bytes, source_name)
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying pypdf: {e}")
            return self._load_with_pypdf_bytes(pdf_bytes, source_name)

    def _load_with_pdfplumber(self, file_path: Path) -> List[Document]:
        """Load PDF using pdfplumber."""
        documents = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                if text and text.strip():
                    documents.append(Document(
                        content=text.strip(),
                        source=str(file_path),
                        source_type="pdf",
                        page_numbers=[page_num],
                        metadata={"page": page_num, "total_pages": len(pdf.pages)}
                    ))

        logger.info(f"Loaded {len(documents)} pages from PDF using pdfplumber")
        return documents

    def _load_with_pdfplumber_bytes(self, pdf_bytes: bytes, source_name: str) -> List[Document]:
        """Load PDF from bytes using pdfplumber."""
        documents = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                if text and text.strip():
                    documents.append(Document(
                        content=text.strip(),
                        source=source_name,
                        source_type="pdf",
                        page_numbers=[page_num],
                        metadata={"page": page_num, "total_pages": len(pdf.pages)}
                    ))

        logger.info(f"Loaded {len(documents)} pages from PDF bytes using pdfplumber")
        return documents

    def _load_with_pypdf(self, file_path: Path) -> List[Document]:
        """Load PDF using pypdf (fallback)."""
        documents = []

        with open(file_path, "rb") as f:
            pdf_reader = pypdf.PdfReader(f)

            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()

                if text and text.strip():
                    documents.append(Document(
                        content=text.strip(),
                        source=str(file_path),
                        source_type="pdf",
                        page_numbers=[page_num],
                        metadata={"page": page_num, "total_pages": len(pdf_reader.pages)}
                    ))

        logger.info(f"Loaded {len(documents)} pages from PDF using pypdf")
        return documents

    def _load_with_pypdf_bytes(self, pdf_bytes: bytes, source_name: str) -> List[Document]:
        """Load PDF from bytes using pypdf (fallback)."""
        documents = []

        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()

            if text and text.strip():
                documents.append(Document(
                    content=text.strip(),
                    source=source_name,
                    source_type="pdf",
                    page_numbers=[page_num],
                    metadata={"page": page_num, "total_pages": len(pdf_reader.pages)}
                ))

        logger.info(f"Loaded {len(documents)} pages from PDF bytes using pypdf")
        return documents


class WebScraper:
    """Scrapes and extracts text content from web pages."""

    def __init__(self):
        self.config = get_data_source_config()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def scrape_url(self, url: str, timeout: int = 30) -> Optional[Document]:
        """
        Scrape text content from a URL.

        Args:
            url: The URL to scrape
            timeout: Request timeout in seconds

        Returns:
            Document object with scraped content, or None if scraping failed
        """
        logger.info(f"Scraping URL: {url}")

        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            # Use trafilatura for main content extraction
            content = trafilatura.extract(
                response.content,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            if not content or not content.strip():
                logger.warning(f"No content extracted from {url}, trying BeautifulSoup")
                return self._scrape_with_beautifulsoup(response.text, url)

            document = Document(
                content=content.strip(),
                source=url,
                source_type="web",
                metadata={
                    "url": url,
                    "status_code": response.status_code,
                }
            )

            logger.info(f"Successfully scraped {len(content)} characters from {url}")
            return document

        except requests.RequestException as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None

    def _scrape_with_beautifulsoup(self, html: str, url: str) -> Optional[Document]:
        """Fallback scraping using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = "\n".join(lines)

            if not content:
                return None

            return Document(
                content=content,
                source=url,
                source_type="web",
                metadata={"url": url, "method": "beautifulsoup"}
            )

        except Exception as e:
            logger.error(f"BeautifulSoup scraping failed: {e}")
            return None

    def scrape_multiple_urls(self, urls: List[str]) -> List[Document]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of successfully scraped Documents
        """
        documents = []

        for url in urls:
            if doc := self.scrape_url(url):
                documents.append(doc)

        logger.info(f"Successfully scraped {len(documents)} out of {len(urls)} URLs")
        return documents


class DocumentLoader:
    """Main document loader that combines PDF and web scraping."""

    def __init__(self):
        self.pdf_loader = PDFLoader()
        self.web_scraper = WebScraper()
        self.config = get_data_source_config()

    def load_default_pdf(self) -> List[Document]:
        """
        Load the default PDF from configuration.

        Returns:
            List of Document objects
        """
        pdf_path = self.config.project_root / self.config.default_pdf_path

        if not pdf_path.exists():
            logger.warning(f"Default PDF not found: {pdf_path}")
            return []

        return self.pdf_loader.load_from_path(pdf_path)

    def scrape_default_url(self) -> Optional[Document]:
        """
        Scrape the default URL from configuration.

        Returns:
            Document object or None if scraping disabled/failed
        """
        if not self.config.scrape_enabled:
            logger.info("Web scraping is disabled in configuration")
            return None

        return self.web_scraper.scrape_url(self.config.scrape_url)

    def load_all_sources(self) -> List[Document]:
        """
        Load all configured data sources (PDF + web).

        Returns:
            Combined list of all Documents
        """
        all_documents = []

        # Load PDF
        pdf_docs = self.load_default_pdf()
        all_documents.extend(pdf_docs)

        # Scrape web
        web_doc = self.scrape_default_url()
        if web_doc:
            all_documents.append(web_doc)

        logger.info(f"Loaded {len(all_documents)} documents total ({len(pdf_docs)} PDF pages, {1 if web_doc else 0} web)")
        return all_documents

    def load_uploaded_pdfs(self, uploaded_files) -> List[Document]:
        """
        Load PDF files uploaded via Streamlit.

        Args:
            uploaded_files: Streamlit UploadedFile list

        Returns:
            List of Document objects
        """
        all_documents = []

        for uploaded_file in uploaded_files:
            try:
                pdf_bytes = uploaded_file.read()
                documents = self.pdf_loader.load_from_bytes(pdf_bytes, uploaded_file.name)
                all_documents.extend(documents)
                logger.info(f"Loaded {len(documents)} pages from {uploaded_file.name}")
            except Exception as e:
                logger.error(f"Failed to load {uploaded_file.name}: {e}")

        return all_documents

    def combine_documents(self, documents: List[Document]) -> str:
        """
        Combine multiple documents into a single text.

        Args:
            documents: List of Document objects

        Returns:
            Combined text with source labels
        """
        if not documents:
            return ""

        combined_parts = []

        for doc in documents:
            # Add source header
            if doc.source_type == "pdf":
                source_label = f"PDF: {Path(doc.source).name}"
                if doc.page_numbers:
                    source_label += f" (Page {doc.page_numbers[0]})"
            else:
                source_label = f"Web: {doc.source}"

            combined_parts.append(f"\n{'='*60}\nSource: {source_label}\n{'='*60}\n")
            combined_parts.append(doc.content)

        return "\n".join(combined_parts)
