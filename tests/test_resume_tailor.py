from bs4 import BeautifulSoup
import pytest
from jobber.resume_tailor import ResumeTailor

@pytest.fixture
def base_resume():
    return {
        "data": {
            "work_experience": [
                {"title": "Engineer", "responsibilities": ["Old task A"]},
                {"title": "Analyst", "responsibilities": ["Old task B"]}
            ]
        }
    }

def test__update_work_exp_success(base_resume):
    updated_work_exp = [
        {"title": "Engineer", "responsibilities": ["New task A"]},
        {"title": "Analyst", "responsibilities": ["New task B"]}
    ]
    tailor = ResumeTailor(base_resume, BeautifulSoup("", "html.parser"))
    result = tailor._update_work_exp(updated_work_exp)
    assert result is True
    assert base_resume["data"]["work_experience"][0]["responsibilities"] == ["New task A"]

def test__update_work_exp_mismatched_length(base_resume):
    updated = [{"title": "Engineer", "responsibilities": ["New task A"]}]
    tailor = ResumeTailor(base_resume, BeautifulSoup("", "html.parser"))
    result = tailor._update_work_exp(updated)
    assert result is False
    assert base_resume["data"]["work_experience"][0]["responsibilities"] == ["Old task A"]
    

def test_update_partial_title_match(base_resume):
    updated = [
        {"title": "Engineer", "responsibilities": ["Updated A"]},
        {"title": "Different Title", "responsibilities": ["Should not update"]}
    ]
    tailor = ResumeTailor(base_resume, BeautifulSoup("", "html.parser"))
    result = tailor._update_work_exp(updated)
    assert result is True
    assert base_resume["data"]["work_experience"][0]["responsibilities"] == ["Updated A"]
    assert base_resume["data"]["work_experience"][1]["responsibilities"] == ["Old task B"]