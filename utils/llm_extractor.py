from openai import OpenAI
import json
from typing import Dict, List
import os

class LLMExtractor:
    """
    Extract structured data from markdown content using OpenAI
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    def extract_structured(
        self, 
        content: str, 
        schema: dict,
        instructions: str = ""
    ) -> dict:
        """
        Extract data theo schema định sẵn
        
        HOW STRUCTURED OUTPUT WORKS:
        ┌──────────────┐
        │ Your Schema  │ ← Define exact JSON structure
        │ (JSON Schema)│
        └──────┬───────┘
               │
               ↓
        ┌──────────────┐
        │ GPT-4 Model  │ ← FORCED to follow schema
        └──────┬───────┘
               │
               ↓
        ┌──────────────┐
        │ Perfect JSON │ ← 100% valid, no errors!
        └──────────────┘
        
        Args:
            content: Markdown content từ website
            schema: JSON Schema defining structure
            instructions: Extra instructions cho LLM
            
        Returns:
            Structured dict matching schema
        """
        
        prompt = f"""
        Extract information from the following content.
        
        {instructions}
        
        Content:
        {content}
        
        Return ONLY valid JSON matching the schema.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise data extraction assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": schema
                },
                temperature=0  # Deterministic output
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}
    
    def batch_extract(
        self,
        content_dict: Dict[str, str],
        schema: dict
    ) -> List[dict]:
        """
        Extract từ nhiều pages cùng lúc
        """
        results = []
        for url, content in content_dict.items():
            print(f"Extracting: {url}")
            data = self.extract_structured(content, schema)
            data['source_url'] = url
            results.append(data)
        return results