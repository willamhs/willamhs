from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from scripts.common import ROOT, read_config, replace_section, safe_url
from scripts.generate_stats import build_stats
from scripts.update_projects import (GitHubClient, GitHubError, classify, eligible_repositories,
    grouped_repositories, project_block, refresh, render_projects)


@pytest.fixture
def config():
    return read_config()


def repo(name="example", **kwargs):
    return dict(id=hash(name), name=name, full_name=f"willamhs/{name}", owner={"login":"willamhs"},
        private=False, fork=False, archived=False, html_url=f"https://github.com/willamhs/{name}",
        description="An actual description", language="Python", topics=[], stargazers_count=2,
        updated_at="2026-11-25T12:00:00Z", homepage=None) | kwargs


def response(data, code=200, next_url=None, headers=None):
    result = Mock(status_code=code, headers=headers or {}, links={"next":{"url":next_url}} if next_url else {})
    result.json.return_value = data
    return result


def client_with(*responses):
    session = Mock(headers={})
    session.get.side_effect = list(responses)
    return GitHubClient("unit-test-token", session=session, sleep=Mock())


def local_root(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/categories.json").write_bytes((ROOT / "config/categories.json").read_bytes())
    (tmp_path / "README.md").write_text("Manual intro\n<!-- PROJECTS:START -->old projects<!-- PROJECTS:END -->\nManual middle\n<!-- STATS:START -->old stats<!-- STATS:END -->\nManual end\n", encoding="utf-8")
    return tmp_path


def test_pagination_and_duplicate_ids():
    next_page = "https://api.github.com/users/willamhs/repos?page=2"
    one, two = repo("a"), repo("b")
    client = client_with(response([one], next_url=next_page), response([one,two]))
    assert client.repositories("willamhs") == [one,two]
    assert client.session.get.call_count == 2


def test_untrusted_next_page_never_receives_token():
    client = client_with(response([repo()], next_url="https://evil.example/steal"))
    with pytest.raises(GitHubError, match="untrusted"):
        client.repositories("willamhs")
    assert client.session.get.call_count == 1


def test_cyclic_pagination_fails():
    url = "https://api.github.com/users/willamhs/repos?page=2"
    client = client_with(response([repo()], next_url=url), response([], next_url=url))
    with pytest.raises(GitHubError, match="pagination"):
        client.repositories("willamhs")


def test_filtering(config):
    public = repo("public")
    config["exclude"] = ["willamhs/excluded"]
    all_repos = [public, repo("private",private=True), repo("fork",fork=True), repo("archive",archived=True), repo("willamhs"), repo("excluded"), public]
    assert eligible_repositories(all_repos,config) == [public]


@pytest.mark.parametrize("topics,expected", [
    ([],"other"), (["unrecognized"],"other"), (["RAG"],"ai-engineering"),
    (["data-science","python"],"data-science"), (["etl","docker"],"data-engineering"),
    (["rag","portfolio-analytics"],"analytics"), (["rag","portfolio-other"],"other"),
    (["terraform","mlops"],"cloud-mlops"), (["backend"],"software"),
    (["machine-learning","deep-learning"],"machine-learning"),
])
def test_classification(config,topics,expected):
    assert classify(repo(topics=topics),config) == expected


def test_feature_priority_then_recency(config):
    config["featured"] = ["willamhs/featured"]
    config["priority"] = {"willamhs/priority":5}
    repos = [repo("new",updated_at="2026-11-26T00:00:00Z"), repo("old",updated_at="2020-01-01T00:00:00Z"), repo("priority"), repo("featured")]
    assert [r["name"] for r in grouped_repositories(repos,config)["other"]] == ["featured","priority","new","old"]


def test_empty_categories_hidden(config):
    groups = grouped_repositories([repo()],config)
    result = render_projects(groups,config)
    assert "Other Projects" in result
    assert "Data Science" not in result
    assert "<details>" not in result


def test_more_projects_remain_available(config):
    result = render_projects(grouped_repositories([repo(str(i)) for i in range(7)],config),config)
    assert "Explore 3 more projects" in result
    assert result.count("<h4>") == 7


def test_escape_metadata_and_validate_demo(config):
    result = project_block(repo(description='<script>alert("x")</script>',topics=['<img onerror="x">'],homepage="javascript:alert(1)"),config)
    assert "<script>" not in result and "&lt;script&gt;" in result
    assert "<img onerror" not in result and "Live demo" not in result
    assert "Live demo" in project_block(repo(homepage="https://example.org/?q=1&x=2"),config)


def test_missing_metadata_is_explicit(config):
    result = project_block(repo(description=None,language=None),config)
    assert "No repository description provided" in result
    assert "Language not reported" in result
    assert "Not identified" in result


@pytest.mark.parametrize("bad", ["javascript:alert(1)","data:text/html,test","https://user:password@example.com", "https://example.com/\nfoo", "//example.com", None])
def test_reject_bad_demo_urls(bad):
    assert safe_url(bad) is None


@pytest.mark.parametrize("text", ["no markers", "<!-- PROJECTS:END --><!-- PROJECTS:START -->", "<!-- PROJECTS:START --><!-- PROJECTS:START --><!-- PROJECTS:END -->"])
def test_marker_validation(text):
    with pytest.raises(ValueError):
        replace_section(text,"PROJECTS","new")


def test_transient_and_network_retry():
    client = client_with(response({},500),requests.ConnectionError("offline"),response([]))
    assert client.repositories("willamhs") == []
    assert client.sleep.call_count == 2


def test_short_rate_limit_retry():
    client = client_with(response({},429,headers={"Retry-After":"1"}),response([]))
    assert client.repositories("willamhs") == []
    client.sleep.assert_called_once_with(1)


def test_long_rate_limit_preserves_content():
    client = client_with(response({},403,headers={"Retry-After":"3600"}))
    with pytest.raises(GitHubError,match="rate limit"):
        client.repositories("willamhs")
    client.sleep.assert_not_called()


@pytest.mark.parametrize("bad", [{}, {"message":"Not Found"}, [repo(topics="invalid")], [repo(private="false")], [repo(updated_at="yesterday")], [repo(owner={"login":"someone-else"})]])
def test_malformed_snapshot_rejected(bad):
    with pytest.raises(GitHubError):
        client_with(response(bad)).repositories("willamhs")


def test_later_page_failure_preserves_all_files(tmp_path):
    root = local_root(tmp_path)
    sentinel = root / "assets/stats/activity-dark.svg"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("existing chart",encoding="utf-8")
    before = {str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    client = client_with(response([repo()],next_url="https://api.github.com/users/willamhs/repos?page=2"), response({},403,headers={"Retry-After":"3600"}))
    with pytest.raises(GitHubError):
        refresh(root,client)
    after = {str(p.relative_to(root)):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert before == after


def test_refresh_preserves_manual_content_and_is_idempotent(tmp_path):
    root = local_root(tmp_path)
    snapshot = refresh(root,client_with(response([repo(),repo("willamhs")])) )
    text = (root / "README.md").read_text(encoding="utf-8")
    assert text.startswith("Manual intro\n") and text.endswith("Manual end\n") and "Manual middle" in text
    before = {str(p):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    refresh(root,client_with(response([repo(),repo("willamhs",updated_at="2026-11-26T00:00:00Z",language="Python")])) )
    assert before == {str(p):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert snapshot["public_repositories"] == 2
    assert len(snapshot["portfolio_repositories"]) == 1
    assert "1 portfolio projects" in text and "2 project stars" in text


def test_empty_snapshot_is_truthful(tmp_path):
    root = local_root(tmp_path)
    snapshot = refresh(root,client_with(response([])))
    assert snapshot["public_repositories"] == 0
    text = (root / "README.md").read_text(encoding="utf-8")
    assert "No eligible public repositories" in text
    assert "0 project stars" in text
