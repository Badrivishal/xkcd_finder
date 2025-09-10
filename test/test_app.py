import pytest
from app import build_index, respond

def test_build_index():
    print("Testing build_index...")
    index, meta = build_index()
    assert index is not None
    assert meta is not None

def test_respond():
    print("Testing respond...")
    respond("I need a comic about procrastination.")
    assert response is str

