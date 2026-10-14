import pytest

from quality import check_quality


def test_clean_file_scores_100():
    assert check_quality("time,temp\n0,20\n5,21\n").quality_score == 100


def test_gap_and_missing_value_lower_the_score():
    report = check_quality("time,temp\n0,20\n50,21\n100,\n")
    assert report.gaps == 2
    assert report.missing == 1
    assert report.quality_score == 100 - 1 - 5 * 2


@pytest.mark.parametrize(
    "text, expected",
    [
        ("time,temp\n0,1\n", 100),
        ("time,temp\n0,\n", 99),
    ],
)
def test_score_examples(text, expected):
    assert check_quality(text).quality_score == expected
