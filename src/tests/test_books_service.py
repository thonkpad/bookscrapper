from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

EXPECTED_DATA = {
    "title": "Meditations",
    "cover": "https://books.toscrape.com/media/cache/90/f7/90f79652caecac36bc97bf7b769c8fc4.jpg",
    "category": "Philosophy",
    "ratings": 2,
    "description": "\n    Written in Greek, without any intention of publication, by the only Roman emperor who was also a philosopher, the Meditations of Marcus Aurelius (AD 121-180) offer a remarkable series of challenging spiritual reflections and exercises developed as the emperor struggled to understand himself and make sense of the universe. Ranging from doubt and despair to conviction and ex Written in Greek, without any intention of publication, by the only Roman emperor who was also a philosopher, the Meditations of Marcus Aurelius (AD 121-180) offer a remarkable series of challenging spiritual reflections and exercises developed as the emperor struggled to understand himself and make sense of the universe. Ranging from doubt and despair to conviction and exaltation, they cover such diverse topics as the nature of moral virtue, human rationality, divine providence, and Marcus' own emotions. But while the Meditations were composed to provide personal consolation and encouragement, in developing his beliefs Marcus Aurelius also created one of the greatest of all works of philosophy: a timeless collection of extended meditations and short aphorisms that has been consulted and admired by statesmen, thinkers and readers through the centuries. ...more\n",
    "information": {
        "UPC": "4f19709e47883df5",
        "Product Type": "Books",
        "Price (excl. tax)": "£25.89",
        "Price (incl. tax)": "£25.89",
        "Tax": "£0.00",
        "Availability": "In stock (1 available)",
        "Number of reviews": "0",
    },
}


@pytest.fixture
def mock_html():
    """Create a mock BeautifulSoup object matching the expected data"""
    html_str = f"""
    <html>
        <h1>{EXPECTED_DATA["title"]}</h1>
        <img src="/media/cache/90/f7/90f79652caecac36bc97bf7b769c8fc4.jpg" />
        <meta name="description" content="{EXPECTED_DATA["description"]}" />
        <table>
            <tr><th>UPC</th><td>{EXPECTED_DATA["information"]["UPC"]}</td></tr>
            <tr><th>Product Type</th><td>{EXPECTED_DATA["information"]["Product Type"]}</td></tr>
            <tr><th>Price (excl. tax)</th><td>Â£25.89</td></tr>
            <tr><th>Price (incl. tax)</th><td>Â£25.89</td></tr>
            <tr><th>Tax</th><td>Â£0.00</td></tr>
            <tr><th>Availability</th><td>{EXPECTED_DATA["information"]["Availability"]}</td></tr>
            <tr><th>Number of reviews</th><td>{EXPECTED_DATA["information"]["Number of reviews"]}</td></tr>
        </table>
    </html>
    """
    return BeautifulSoup(html_str, "html.parser")


@patch("utils.helpers.parse_ratings")
@patch("utils.helpers.parse_book_id_html")
def test_get_book_details(mock_parse_book_id_html, mock_parse_ratings, mock_html):
    """Test get_book_details returns correct structure and values"""
    # Setup mocks
    mock_parse_book_id_html.return_value = mock_html
    mock_parse_ratings.return_value = EXPECTED_DATA["ratings"]

    # Import and call the function
    from api.services.books_service import get_book_details
    from utils import helpers

    result = get_book_details("meditations_33")

    # Assertions
    assert result["title"] == EXPECTED_DATA["title"]
    assert result["cover"] == EXPECTED_DATA["cover"]
    assert result["category"] == EXPECTED_DATA["category"]
    assert result["ratings"] == EXPECTED_DATA["ratings"]
    assert result["description"] == EXPECTED_DATA["description"]
    assert result["information"] == EXPECTED_DATA["information"]


@patch("utils.helpers.parse_ratings")
@patch("utils.helpers.parse_book_id_html")
def test_get_book_details_structure(
    mock_parse_book_id_html, mock_parse_ratings, mock_html
):
    """Test get_book_details returns all required keys"""
    mock_parse_book_id_html.return_value = mock_html
    mock_parse_ratings.return_value = EXPECTED_DATA["ratings"]

    from api.services.books_service import get_book_details
    from utils import helpers

    result = get_book_details("meditations_33")

    required_keys = {
        "title",
        "cover",
        "category",
        "ratings",
        "description",
        "information",
    }
    assert set(result.keys()) == required_keys


@patch("utils.helpers.parse_ratings")
@patch("utils.helpers.parse_book_id_html")
def test_get_book_details_price_formatting(
    mock_parse_book_id_html, mock_parse_ratings, mock_html
):
    """Test that Â£ is replaced with £"""
    mock_parse_book_id_html.return_value = mock_html
    mock_parse_ratings.return_value = EXPECTED_DATA["ratings"]

    from api.services.books_service import get_book_details
    from utils import helpers

    result = get_book_details("meditations_33")

    # Check that price formatting is correct
    assert result["information"]["Price (excl. tax)"] == "£25.89"
    assert result["information"]["Price (incl. tax)"] == "£25.89"
    assert result["information"]["Tax"] == "£0.00"
    assert "Â£" not in str(result["information"])
