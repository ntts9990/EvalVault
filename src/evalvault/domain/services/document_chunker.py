"""Document chunking utilities for testset generation."""

import re


class DocumentChunker:
    """문서를 의미있는 청크로 분할하는 클래스.

    텍스트를 chunk_size 길이로 분할하고, overlap만큼 겹치게 만듭니다.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize document chunker.

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Handles both Korean and English sentence endings.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Korean and English sentence endings
        sentence_pattern = r"[.!?。！？]\s+"
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, document: str) -> list[str]:
        """Chunk document into overlapping segments.

        Args:
            document: Document text to chunk

        Returns:
            List of text chunks
        """
        if not document:
            return []

        # If document is shorter than chunk_size, return as single chunk
        if len(document) <= self.chunk_size:
            return [document]

        chunks = []
        sentences = self._split_sentences(document)

        current_chunk = ""
        for sentence in sentences:
            # Add sentence to current chunk
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if self.overlap > 0 and current_chunk:
                    # Take last `overlap` characters as start of new chunk
                    overlap_text = current_chunk[-self.overlap :]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
