"""Build the bespoke identity and vendor verified upstream SVG icons locally.

This is a manual design build, never part of the daily API-only refresh.
Source URLs and SHA-256 digests are recorded in assets/icons/sources.json.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from html import escape
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import requests

try:
    from .common import ROOT, atomic_write, replace_section
    from .design_profile import build_identity
except ImportError:
    from common import ROOT, atomic_write, replace_section
    from design_profile import build_identity

# Devicon 2.17.0, and older Simple Icons marks for brands removed upstream.
DEV = "https://cdn.jsdelivr.net/gh/devicons/devicon@v2.17.0/icons"
SIMPLE = "https://cdn.jsdelivr.net/npm/simple-icons@11.15.0/icons"

GROUPS = [
    ("Programming & Data Analysis", [("Python","python"),("SQL",None),("R","r"),("Pandas","pandas"),("NumPy","numpy"),("Jupyter","jupyter"),("Matplotlib","matplotlib"),("Seaborn","seaborn"),("Plotly","plotly")]),
    ("Business Intelligence", [("Power BI","powerbi"),("Tableau","tableau"),("Excel","excel"),("Looker Studio","lookerstudio")]),
    ("Databases", [("PostgreSQL","postgresql"),("MySQL","mysql"),("SQL Server","microsoftsqlserver"),("MongoDB","mongodb"),("Redis","redis")]),
    ("Machine Learning & Deep Learning", [("Scikit-learn","scikitlearn"),("TensorFlow","tensorflow"),("PyTorch","pytorch"),("Keras","keras"),("XGBoost","xgboost"),("LightGBM","lightgbm"),("CatBoost","catboost")]),
    ("AI Engineering & Generative AI", [("OpenAI","openai"),("Gemini","gemini"),("Hugging Face","huggingface"),("LangChain","langchain"),("LangGraph","langgraph"),("Ollama","ollama"),("FastAPI","fastapi"),("LLMs",None),("RAG",None),("AI Agents",None),("Vector Databases",None)]),
    ("Data Engineering", [("Apache Spark","apachespark"),("Apache Kafka","apachekafka"),("Apache Airflow","apacheairflow"),("Databricks","databricks"),("dbt","dbt"),("ETL",None),("ELT",None),("Data Warehousing",None)]),
    ("Cloud Computing", [("Google Cloud Platform (GCP)","googlecloud"),("BigQuery","bigquery"),("Vertex AI","vertexai"),("Amazon Web Services (AWS)","amazonwebservices"),("Microsoft Azure","azure")]),
    ("DevOps & MLOps", [("Git","git"),("GitHub","github"),("GitHub Actions","githubactions"),("Docker","docker"),("Kubernetes","kubernetes"),("MLflow","mlflow"),("Terraform","terraform")]),
]

DEVICONS = {
    "python":"python-original", "r":"r-original", "pandas":"pandas-original", "numpy":"numpy-original", "jupyter":"jupyter-original", "matplotlib":"matplotlib-original", "plotly":"plotly-original",
    "postgresql":"postgresql-original", "mysql":"mysql-original", "microsoftsqlserver":"microsoftsqlserver-original", "mongodb":"mongodb-original", "redis":"redis-original", "scikitlearn":"scikitlearn-original", "tensorflow":"tensorflow-original", "pytorch":"pytorch-original", "keras":"keras-original", "fastapi":"fastapi-original",
    "apachekafka":"apachekafka-original", "apacheairflow":"apacheairflow-original", "googlecloud":"googlecloud-original", "amazonwebservices":"amazonwebservices-original-wordmark", "azure":"azure-original", "git":"git-original", "github":"github-original", "githubactions":"githubactions-original", "docker":"docker-original", "kubernetes":"kubernetes-original", "terraform":"terraform-original",
    "javascript":"javascript-original", "typescript":"typescript-original", "java":"java-original", "html5":"html5-original", "css3":"css3-original", "bash":"bash-original", "cplusplus":"cplusplus-original", "csharp":"csharp-original", "go":"go-original", "rust":"rust-original"
}
# Each source is a first-party project or an established icon catalog.
EXTRA = {
    "seaborn":("https://raw.githubusercontent.com/mwaskom/seaborn/v0.13.2/doc/_static/logo-mark-lightbg.svg", None),
    "powerbi":(f"{SIMPLE}/powerbi.svg", "F2C811"), "tableau":(f"{SIMPLE}/tableau.svg", "E97627"), "excel":(f"{SIMPLE}/microsoftexcel.svg", "217346"), "lookerstudio":(f"{SIMPLE}/looker.svg", "4285F4"),
    "openai":(f"{SIMPLE}/openai.svg", "10A37F"), "gemini":("https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/googlegemini.svg", "8E75B2"),
    "huggingface":("https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/huggingface.svg", "FFD21E"), "langchain":("https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/langchain.svg", "1C3C3C"), "langgraph":("https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/langgraph.svg", "1C3C3C"), "ollama":("https://cdn.jsdelivr.net/npm/simple-icons@15.0.0/icons/ollama.svg", "737373"),
    "apachespark":(f"{SIMPLE}/apachespark.svg", "E25A1C"), "databricks":(f"{SIMPLE}/databricks.svg", "FF3621"), "dbt":(f"{SIMPLE}/dbt.svg", "FF694B"), "bigquery":(f"{SIMPLE}/googlebigquery.svg", "669DF6"),
    "vertexai":("https://cdn.jsdelivr.net/gh/devicons/devicon@v2.17.0/icons/googlecloud/googlecloud-original.svg", None),
    "mlflow":(f"{SIMPLE}/mlflow.svg", "0194E2"),
    "xgboost":("https://xgboost.ai/images/logo/xgboost-logo.svg", None),
    "lightgbm":("https://raw.githubusercontent.com/microsoft/LightGBM/v4.6.0/docs/logo/LightGBM_logo_no_text.svg", None),
    "catboost":("https://catboost-opensource.s3.yandex.net/logo_white_for_dark_theme.svg", None),
    "linkedin":(f"{SIMPLE}/linkedin.svg", "0A66C2"), "youtube":(f"{SIMPLE}/youtube.svg", "FF0000"), "instagram":(f"{SIMPLE}/instagram.svg", "E4405F"), "tiktok":(f"{SIMPLE}/tiktok.svg", "000000"), "linktree":(f"{SIMPLE}/linktree.svg", "43E55E"),
}


def download_icon(item):
    name, (url, color) = item
    path = ROOT / f"assets/icons/tech/{name}.svg"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    raw = response.text
    root = ET.fromstring(raw)
    if root.tag.split("}")[-1] != "svg" or re.search(r"<script|<foreignObject|onload=", raw, re.I):
        raise ValueError(f"Invalid or active SVG for {name}")
    # Remove XML prolog/DOCTYPE; keep the actual SVG self contained.
    raw = raw[raw.index("<svg"):]
    if color:
        raw = raw.replace("<svg ", f'<svg fill="#{color}" ', 1)
    # A neutral tile keeps original black/navy logos visible in GitHub dark mode.
    raw = re.sub(r'<svg\b[^>]*>', lambda m: re.sub(r'\s(?:width|height)="[^"]*"', '', m.group())[:-1] + ' x="4" y="4" width="24" height="24">', raw, count=1)
    tile = "#0F172A" if name == "catboost" else "#F8FAFC"
    raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><rect width="32" height="32" rx="6" fill="{tile}"/>' + raw + '</svg>'
    atomic_write(path, raw.strip() + "\n")
    return name, {"url":url, "sha256":hashlib.sha256(response.content).hexdigest(), "color":color, "upstream":"Simple Icons" if "simple-icons" in url else "Devicon" if "devicon" in url else name}


AREA_PATHS = {
    "dashboard":'<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 10h18M10 10v11m4-4v-3m3 3v-5"/>',
    "analytics":'<path d="M4 20h17M7 16v-5m6 5V5m6 11V8"/>',
    "science":'<path d="M9 3h6m-5 0v7L4 20h16l-6-10V3M7 15h10"/>',
    "neural":'<circle cx="5" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="20" cy="5" r="2"/><circle cx="20" cy="19" r="2"/><path d="m7 6 4 4m2 4 5 4M7 18l4-4m2-4 5-4"/>',
    "ai":'<rect x="5" y="5" width="14" height="14" rx="4"/><path d="M9 9h6v6H9zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m14 0h3M2 15h3m14 0h3"/>',
    "pipeline":'<ellipse cx="6" cy="5" rx="4" ry="2"/><path d="M2 5v12c0 3 8 3 8 0V5m2 7h10m-3-3 3 3-3 3"/>',
    "cloud":'<path d="M6 18a5 5 0 0 1-1-10 7 7 0 0 1 13-1 5.5 5.5 0 0 1 0 11H6Z"/>',
    "code":'<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"/>',
    "folder":'<path d="M3 6h7l2 3h9v11H3V6Z"/>',
    "mail":'<rect x="2" y="4" width="20" height="16" rx="3"/><path d="m3 6 9 7 9-7"/>',
    "globe":'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
}


SOCIALS = [
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/willam-huaman-saavedra/"),
    ("globe", "Portfolio", "https://portafolio-willam.netlify.app/"),
    ("github", "GitHub", "https://github.com/willamhs"),
    ("mail", "Email", "mailto:U20211E088@upc.edu.pe"),
    ("youtube", "YouTube", "https://www.youtube.com/@willam-ai"),
    ("instagram", "Instagram", "https://www.instagram.com/willam.ai/"),
    ("tiktok", "TikTok", "https://www.tiktok.com/@willam.ai"),
    ("linktree", "Linktree", "https://linktr.ee/willam.ai"),
]


def button(icon, label):
    if icon in AREA_PATHS:
        graphic = f'<svg x="14" y="12" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="1.6">{AREA_PATHS[icon]}</svg>'
    else:
        raw = (ROOT / f"assets/icons/tech/{icon}.svg").read_text(encoding="utf-8")
        raw = re.sub(r'<svg\b[^>]*>', lambda m: re.sub(r'\s(?:width|height)="[^"]*"', '', m.group())[:-1] + ' x="14" y="12" width="20" height="20">', raw, count=1)
        graphic = raw
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="140" height="44" viewBox="0 0 140 44" role="img" aria-label="{label}"><defs><linearGradient id="button-blue" x2="1" y2="1"><stop stop-color="#123B85"/><stop offset="1" stop-color="#2563EB"/></linearGradient></defs><rect x="0.5" y="0.5" width="139" height="43" rx="10" fill="url(#button-blue)" stroke="#60A5FA" stroke-opacity="0.55"/>{graphic}<text x="44" y="27" fill="#F8FAFC" font-family="Arial,Helvetica,sans-serif" font-size="14" font-weight="600">{label}</text></svg>\n'


def stack_markup():
    chunks = ["My learning roadmap across the data and AI ecosystem. Explore the source code in my projects for evidence of tools used.\n"]
    for title, technologies in GROUPS:
        chunks.append(f"<details>\n<summary><strong>{title}</strong></summary>\n\n<p>")
        for label, icon in technologies:
            graphic = f'<img src="assets/icons/tech/{icon}.svg" width="24" height="24" alt="" /> ' if icon else ""
            chunks.append(f'{graphic}{escape(label)} &nbsp; · &nbsp;')
        chunks[-1] = chunks[-1].removesuffix(" &nbsp; · &nbsp;")
        chunks.append("</p>\n\n</details>\n")
    chunks.append('<sub>Official catalog icons retain their source colors. SQL and architectural concepts use text labels. Vertex AI uses its parent Google Cloud mark; Looker Studio uses the Looker mark. <a href="docs/icon-sources.md">Icon sources and licenses</a>.</sub>')
    return "\n".join(chunks)


def main():
    sources = {name:(f"{DEV}/{name}/{file}.svg",None) for name,file in DEVICONS.items()} | EXTRA
    with ThreadPoolExecutor(max_workers=8) as pool:
        manifest = dict(pool.map(download_icon, sources.items()))
    atomic_write(ROOT / "assets/icons/sources.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for key, path in AREA_PATHS.items():
        atomic_write(ROOT / f"assets/icons/areas/{key}.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{path}</svg>\n')
    build_identity(AREA_PATHS)
    atomic_write(ROOT / "assets/banners/divider.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="12" viewBox="0 0 1100 12"><defs><linearGradient id="g"><stop stop-color="#2563EB"/><stop offset="1" stop-color="#60A5FA" stop-opacity="0.08"/></linearGradient></defs><rect y="5" width="1100" height="2" rx="1" fill="url(#g)"/></svg>\n')
    for icon, label, _ in SOCIALS:
        atomic_write(ROOT / f"assets/icons/social/{icon}.svg", button(icon,label))
    readme = ROOT / "README.md"
    atomic_write(readme, replace_section(readme.read_text(encoding="utf-8"), "STACK", stack_markup()))
    print(f"Built brand assets and verified {len(manifest)} local upstream icons")


if __name__ == "__main__":
    main()
