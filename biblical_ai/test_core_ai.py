import pytest
import asyncio
import httpx
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Import the code to be tested
from biblical_ai.core_ai import BiblicalAI
# Import the actual dependency for accurate patching paths
from biblical_ai.feast_date_calculator import FeastDateCalculator 

# --- Fixtures and Mocks ---

# Mock FeastDateCalculator for consistent test results
@pytest.fixture
def mock_feast_calculator():
    """Mocks the FeastDateCalculator for unit testing core_ai logic."""
    # Patch the class in the *module* where it is imported (core_ai)
    with patch('biblical_ai.core_ai.FeastDateCalculator') as MockFeastCalc:
        instance = MockFeastCalc.return_value
        # Mock specific responses for get_feast_dates_for_year
        # Note: We must mock the actual return structure of the mock FDC for year-based detection tests
        
        # Determine current year to accurately mock 'next year' logic
        current_year = datetime.now().year
        next_year = current_year + 1
        
        # Side effect lambda to handle different years requested
        def side_effect(year):
            mock_data = {
                current_year: {
                    'Passover (Pesach)': {'gregorian_date': 'CURRENT-04-10', 'hebrew_date_approx': f'Nisan 14, {current_year} (approx)', 'moon_phase_detail': 'Full Moon (approx)', 'notes': 'Calculated...'}
                },
                next_year: {
                    'Passover (Pesach)': {'gregorian_date': 'NEXT-04-10', 'hebrew_date_approx': f'Nisan 14, {next_year} (approx)', 'moon_phase_detail': 'Full Moon (approx)', 'notes': 'Calculated...'}
                },
                2027: {
                    'Feast of Tabernacles (Sukkot)': {'gregorian_date': '2027-10-15 - 2027-10-21', 'hebrew_date_approx': 'Tishrei 15-21, 2027 (approx)', 'moon_phase_detail': 'Full Moon period', 'notes': 'Calculated...'}
                }
            }
            # Replace placeholder dates for the current/next year logic
            data = mock_data.get(year, {})
            if data and year == current_year:
                 data['Passover (Pesach)']['gregorian_date'] = date(current_year, 4, 10).strftime('%Y-%m-%d')
            if data and year == next_year:
                 data['Passover (Pesach)']['gregorian_date'] = date(next_year, 4, 10).strftime('%Y-%m-%d')
            
            return data
            
        instance.get_feast_dates_for_year.side_effect = side_effect
        
        yield instance

@pytest.fixture
def biblical_ai_instance(mock_feast_calculator):
    """Provides a functional BiblicalAI instance for tests."""
    # We must mock the httpx client to prevent real API calls in most tests
    with patch('biblical_ai.core_ai.httpx.AsyncClient'):
         # The mock_feast_calculator fixture already handles patching the FDC
         return BiblicalAI(api_key="mock_api_key")

# --- Test Cases ---

def test_init_raises_error_without_api_key():
    """Tests that initialization fails if the API key is empty."""
    with pytest.raises(ValueError, match="Gemini API key cannot be empty."):
        BiblicalAI(api_key="")

def test_respond_to_query_feast_date_detection_next_year(biblical_ai_instance, mock_feast_calculator):
    """Tests if a 'next year' feast query correctly triggers the calculator."""
    async def _test():
        query = "When is Passover next year?"
        response = await biblical_ai_instance.respond_to_query(query)
        current_year = datetime.now().year
        expected_year = current_year + 1
        
        # Assert that the calculator was called with the correct year
        mock_feast_calculator.get_feast_dates_for_year.assert_called_once_with(expected_year)
        
        # Assert the response contains confirmation of the calculation and data
        assert f"Here are the calculated biblical feast dates for {expected_year}" in response
        assert "Passover (Pesach)" in response
        assert date(expected_year, 4, 10).strftime('%Y-%m-%d') in response # Check for mocked date
    asyncio.run(_test())


def test_respond_to_query_feast_date_detection_specific_year(biblical_ai_instance, mock_feast_calculator):
    """Tests if an explicit year feast query correctly triggers the calculator."""
    async def _test():
        query = "What is the date for the Feast of Tabernacles in 2027?"
        response = await biblical_ai_instance.respond_to_query(query)
        
        # Assert that the calculator was called with the specific year 2027
        mock_feast_calculator.get_feast_dates_for_year.assert_called_once_with(2027)
        
        # Assert the response contains confirmation of the calculation and data
        assert f"Here are the calculated biblical feast dates for 2027" in response
        assert "Feast of Tabernacles (Sukkot)" in response
        assert "2027-10-15 - 2027-10-21" in response
    asyncio.run(_test())

def test_respond_to_query_feast_date_default_next_year(biblical_ai_instance, mock_feast_calculator):
    """Tests if a feast query without a year defaults to next year."""
    async def _test():
        query = "When is Sukkot?"
        response = await biblical_ai_instance.respond_to_query(query)
        current_year = datetime.now().year
        expected_year = current_year + 1
        
        mock_feast_calculator.get_feast_dates_for_year.assert_called_once_with(expected_year)
        assert f"Here are the calculated biblical feast dates for {expected_year}" in response
    asyncio.run(_test())


def test_respond_to_query_llm_call_for_general_query(biblical_ai_instance):
    """Tests that a general query bypasses the calculator and calls the LLM."""
    async def _test():
        query = "Tell me about the teachings of Paul on faith."

        # Mock the internal API call method
        with patch.object(biblical_ai_instance, '_call_gemini_api_async', new_callable=AsyncMock) as mock_gemini_call:
            mock_gemini_call.return_value = "Paul taught extensively on faith and grace..."
            response = await biblical_ai_instance.respond_to_query(query)
            
            # Assert the LLM function was called with the original query
            mock_gemini_call.assert_called_once_with(query)
            
            # Assert the response is from the mocked LLM
            assert "Paul taught extensively on faith and grace..." in response
    asyncio.run(_test())

def test_respond_to_query_error_in_feast_calculation(biblical_ai_instance, mock_feast_calculator):
    """Tests robust error handling for calculator failures."""
    async def _test():
        query = "When is Passover for some invalid year?"
        
        # Force the calculator to raise an exception
        mock_feast_calculator.get_feast_dates_for_year.side_effect = Exception("Calculation error")
        
        response = await biblical_ai_instance.respond_to_query(query)
        
        assert "I encountered an error while trying to calculate the feast dates." in response
    asyncio.run(_test())

def test_respond_to_query_error_in_gemini_api(biblical_ai_instance):
    """Tests robust error handling for Gemini API failures."""
    async def _test():
        query = "Who was King David?"
        
        # Mock the internal API call method to raise an exception
        with patch.object(biblical_ai_instance, '_call_gemini_api_async', new_callable=AsyncMock) as mock_gemini_call:
            mock_gemini_call.side_effect = Exception("Gemini API error")
            response = await biblical_ai_instance.respond_to_query(query)
            
            assert "I apologize, but I'm unable to connect to the knowledge base at the moment." in response
    asyncio.run(_test())

def test_detect_and_extract_year_no_year(biblical_ai_instance):
    """Tests year extraction when no year is mentioned."""
    query = "Just tell me about the new moon."
    year = biblical_ai_instance._detect_and_extract_year(query)
    assert year is None

def test_detect_and_extract_year_explicit_year(biblical_ai_instance):
    """Tests year extraction when an explicit year is mentioned."""
    query = "What about 2028?"
    year = biblical_ai_instance._detect_and_extract_year(query)
    assert year == 2028

def test_detect_and_extract_year_next_year(biblical_ai_instance):
    """Tests year extraction for 'next year' phrase."""
    query = "Passover next year please."
    expected_year = datetime.now().year + 1
    year = biblical_ai_instance._detect_and_extract_year(query)
    assert year == expected_year
    
# --- Test Exponential Backoff Logic (Mocking HTTP responses) ---

def test_exponential_backoff_fetch_async_retries_on_500(biblical_ai_instance):
    """Tests if the fetch function retries on a 500 error and eventually succeeds."""
    async def _test():
        # Use patch on the actual httpx client instance with AsyncMock for await compatibility
        with patch.object(biblical_ai_instance.http_client, 'post', new_callable=AsyncMock) as mock_post:
            # Simulate 500 error twice, then success
            mock_post.side_effect = [
                httpx.Response(500, request=httpx.Request("POST", "http://test.com")),
                httpx.Response(500, request=httpx.Request("POST", "http://test.com")),
                httpx.Response(200, request=httpx.Request("POST", "http://test.com"), json={"test": "success"})
            ]

            response = await biblical_ai_instance._exponential_backoff_fetch_async(
                "http://test.com", {}, {"data": "test"}, max_retries=3, initial_delay=0.01 
            )
            assert response == {"test": "success"}
            assert mock_post.call_count == 3
    asyncio.run(_test())

def test_exponential_backoff_fetch_async_fails_after_max_retries(biblical_ai_instance):
    """Tests if the fetch function raises an error after maximum retries are exceeded."""
    async def _test():
        with patch.object(biblical_ai_instance.http_client, 'post', new_callable=AsyncMock) as mock_post:
            # Simulate 500 error every time using return_value (since side_effect expects an iterable or exception)
            mock_post.return_value = httpx.Response(500, request=httpx.Request("POST", "http://test.com"))

            with pytest.raises(httpx.HTTPStatusError):
                await biblical_ai_instance._exponential_backoff_fetch_async(
                    "http://test.com", {}, {"data": "test"}, max_retries=2, initial_delay=0.01
                )
            # Should attempt 3 times: initial attempt + 2 retries
            assert mock_post.call_count == 3
    asyncio.run(_test())
