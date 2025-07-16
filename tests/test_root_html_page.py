import pytest


@pytest.mark.asyncio
async def test_of_html_page_output(async_client) -> None:
    """Корневой тест проверяет отдается ли статика"""
    resp = await async_client.get("/")
    assert resp.status_code == 200