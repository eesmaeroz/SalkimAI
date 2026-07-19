from ml.prediction.features.openweathermap_client import fetch_openweathermap_forecast


def test_openweathermap_client_requires_api_key():
    try:
        fetch_openweathermap_forecast(
            api_key="",
            latitude=40.8991,
            longitude=31.1888,
        )
    except ValueError as error:
        assert "API key" in str(error)
    else:
        raise AssertionError("Expected empty API key to fail")
