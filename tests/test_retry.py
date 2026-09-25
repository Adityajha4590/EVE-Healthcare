import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.services.payment import _send_webhook

@pytest.mark.anyio
async def test_retry_on_transient_error():
    mock_post = AsyncMock()
    # Fails twice with 500, then succeeds with 200
    mock_resp_500 = httpx.Response(500, request=httpx.Request("POST", "http://test"))
    mock_resp_200 = httpx.Response(200, request=httpx.Request("POST", "http://test"))
    
    mock_post.side_effect = [
        httpx.HTTPStatusError("500", request=mock_resp_500.request, response=mock_resp_500),
        httpx.HTTPStatusError("500", request=mock_resp_500.request, response=mock_resp_500),
        mock_resp_200
    ]

    with patch("httpx.AsyncClient.post", new=mock_post):
        await _send_webhook("http://test", "{}", {})
        
    assert mock_post.call_count == 3

@pytest.mark.anyio
async def test_no_retry_on_permanent_error():
    mock_post = AsyncMock()
    mock_resp_400 = httpx.Response(400, request=httpx.Request("POST", "http://test"))
    mock_post.side_effect = httpx.HTTPStatusError("400", request=mock_resp_400.request, response=mock_resp_400)

    with patch("httpx.AsyncClient.post", new=mock_post):
        with pytest.raises(httpx.HTTPStatusError) as exc:
            await _send_webhook("http://test", "{}", {})
            
        assert exc.value.response.status_code == 400
        
    assert mock_post.call_count == 1
