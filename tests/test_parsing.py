from ci.parser import *

@pytest.fixture
def sample_tag_map(tmp_path):
    tag_map_content = """
repos:
  repo1:
    url: "pruplestack/repo1"
  repo2:
    url: "pruplestack/repo2"
  repo3:
    url: "pruplestack/repo3"
  repo4:
    url: "pruplestack/repo4"
  repo5:
    url: "pruplestack/repo5"

tag_map:
  - repo1: ["tag1", "tag2"]
  - repo2: ["tag3", "tag4"]
  - repo3: ["tag5", "tag6"]
  - repo4: ["tag1", "tag3"]
  - repo5: ["tag2", "tag4"]
"""
    tag_map_file = tmp_path / "tag_map.yaml"
    tag_map_file.write_text(tag_map_content)
    return tag_map_file
print (parse_tag_map(str(sample_tag_map)))
def test_parse_tag_map(sample_tag_map):
    repos, tag_to_repo = parse_tag_map(str(sample_tag_map))

    assert len(repos) == 5
    assert repos["repo1"] == "pruplestack/repo1"
    assert repos["repo5"] == "pruplestack/repo5"

    assert len(tag_to_repo) == 6
    assert set(tag_to_repo["tag1"]) == {"repo1", "repo4"}
    assert set(tag_to_repo["tag4"]) == {"repo2", "repo5"}
#not sure this work , lets test it in prod

