"""Document processing and enrichment module."""

import os
import json
import re
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

from ..config import get_settings


class ChunkMetadata(BaseModel):
    """Structured metadata for a document chunk."""
    summary: str = Field(description="A concise 1-2 sentence summary of the chunk.")
    keywords: List[str] = Field(description="A list of 5-7 key topics or entities mentioned.")
    hypothetical_questions: List[str] = Field(description="A list of 3-5 questions this chunk could answer.")
    table_summary: Optional[str] = Field(
        description="If the chunk is a table, a natural language summary of its key insights.", 
        default=None
    )


class DocumentProcessor:
    """Handles document parsing, chunking, and enrichment."""
    
    def __init__(self):
        self.settings = get_settings()
        self.enrichment_llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0,
            api_key=self.settings.openai_api_key
        ).with_structured_output(ChunkMetadata)
    
    def parse_html_file(self, file_path: str) -> List[Dict]:
        """
        Parse an HTML file and extract structured elements.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            List of parsed elements with metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML using unstructured
            elements = partition_html(text=html_content)
            
            # Convert to list of dictionaries
            parsed_elements = []
            for element in elements:
                element_dict = element.to_dict()
                parsed_elements.append(element_dict)
            
            return parsed_elements
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def chunk_documents(self, elements: List[Dict]) -> List[Document]:
        """
        Chunk parsed elements into manageable pieces.
        
        Args:
            elements: List of parsed elements
            
        Returns:
            List of chunked documents
        """
        # Convert elements to Document objects
        documents = []
        for element in elements:
            if element.get('text', '').strip():
                doc = Document(
                    page_content=element['text'],
                    metadata=element.get('metadata', {})
                )
                documents.append(doc)
        
        # Chunk by title for better structure preservation
        chunks = chunk_by_title(documents)
        
        return chunks
    
    def generate_enrichment_prompt(self, chunk_text: str, is_table: bool) -> str:
        """Generate a prompt for the LLM to enrich a chunk."""
        table_instruction = """
        This chunk is a TABLE. Your summary should describe the main data points and trends, 
        for example: 'This table shows a 15% year-over-year increase in revenue for the Cloud segment.'
        """ if is_table else ""
        
        prompt = f"""
        You are an expert financial analyst. Please analyze the following document chunk and generate the specified metadata.
        {table_instruction}
        Chunk Content:
        ---
        {chunk_text}
        ---
        """
        return prompt
    
    def enrich_chunk(self, chunk: Document) -> Optional[Dict[str, Any]]:
        """
        Enrich a single chunk with LLM-generated metadata.
        
        Args:
            chunk: Document chunk to enrich
            
        Returns:
            Enriched metadata dictionary or None if error
        """
        is_table = 'text_as_html' in chunk.metadata
        content = chunk.metadata.get('text_as_html', chunk.page_content)
        
        # Truncate very long chunks to avoid overwhelming the LLM
        truncated_content = content[:3000]
        
        prompt = self.generate_enrichment_prompt(truncated_content, is_table)
        
        try:
            metadata_obj = self.enrichment_llm.invoke(prompt)
            return metadata_obj.dict()
        except Exception as e:
            print(f"  - Error enriching chunk: {e}")
            return None
    
    def process_documents(
        self, 
        file_paths: List[str], 
        output_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents and enrich them with metadata.
        
        Args:
            file_paths: List of file paths to process
            output_path: Optional path to save enriched chunks
            
        Returns:
            List of enriched chunks
        """
        all_enriched_chunks = []
        
        for file_path in tqdm(file_paths, desc="Processing files"):
            print(f"Processing {file_path}")
            
            # Parse HTML file
            elements = self.parse_html_file(file_path)
            if not elements:
                continue
            
            # Chunk documents
            chunks = self.chunk_documents(elements)
            print(f"  - Created {len(chunks)} chunks")
            
            # Enrich chunks
            enriched_chunks = []
            for chunk in tqdm(chunks, desc="Enriching chunks", leave=False):
                enriched_metadata = self.enrich_chunk(chunk)
                if enriched_metadata:
                    enriched_chunk = {
                        "content": chunk.page_content,
                        "metadata": chunk.metadata,
                        "enriched_metadata": enriched_metadata,
                        "source_file": file_path
                    }
                    enriched_chunks.append(enriched_chunk)
            
            all_enriched_chunks.extend(enriched_chunks)
            print(f"  - Enriched {len(enriched_chunks)} chunks")
        
        # Save to file if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_enriched_chunks, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(all_enriched_chunks)} enriched chunks to {output_path}")
        
        return all_enriched_chunks
    
    def create_embedding_text(self, chunk: Dict) -> str:
        """
        Create embedding text for a chunk by combining content and metadata.
        
        Args:
            chunk: Enriched chunk dictionary
            
        Returns:
            Combined text for embedding
        """
        content = chunk["content"]
        enriched_metadata = chunk["enriched_metadata"]
        
        # Combine content with metadata
        embedding_parts = [
            content,
            f"Summary: {enriched_metadata['summary']}",
            f"Keywords: {', '.join(enriched_metadata['keywords'])}",
            f"Questions: {' | '.join(enriched_metadata['hypothetical_questions'])}"
        ]
        
        if enriched_metadata.get('table_summary'):
            embedding_parts.append(f"Table Summary: {enriched_metadata['table_summary']}")
        
        return " | ".join(embedding_parts)
