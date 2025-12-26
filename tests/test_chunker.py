from app.utils.chunker import chunk_from_docling_sections, sliding_window_chunk


def test_sliding_window_chunk_respects_overlap():
    text = "abcdefghijklmnopqrstuvwxyz" * 5  # 130 chars
    chunks = sliding_window_chunk(text, chunk_size=50, overlap=10, metadata={"source": "test"})

    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)
    assert chunks[0].metadata["source"] == "test"
    # ensure overlap by comparing endings/beginnings
    first_chunk_tail = chunks[0].text[-10:]
    second_chunk_head = chunks[1].text[:10]
    assert first_chunk_tail == second_chunk_head


def test_chunk_from_docling_sections_builds_payload():
    sections = [
        {"text": "hello world", "metadata": {"section": "intro"}},
        {"text": "goodbye world", "metadata": {"section": "outro"}},
    ]
    chunks = chunk_from_docling_sections(sections, overlap=0)

    assert len(chunks) == 2
    assert chunks[0].metadata["section"] == "intro"
    assert chunks[1].metadata["chunk_index"] == 0  # reset per section
