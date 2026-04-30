import base64
import logging
import requests

from src.config import GH_PAT, GITHUB_REPO

logger = logging.getLogger(__name__)

_H = {
    "Authorization": f"token {GH_PAT}",
    "Content-Type": "application/json",
}


def upload_chart(local_path: str, code: str, period: str) -> None:
    filename = f"{code}_{period}.png"
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/charts/{filename}",
        headers=_H, timeout=10,
    )
    sha = r.json().get("sha") if r.ok else None

    body = {"message": f"Update chart {filename}", "content": content_b64}
    if sha:
        body["sha"] = sha

    requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/charts/{filename}",
        headers=_H, json=body, timeout=30,
    ).raise_for_status()
    logger.info(f"GitHub 업로드 완료: {filename}")
