import json
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
import structlog
from src.core.config import settings

logger = structlog.get_logger()


class GeminiAdapter:
    """Adapter for Google Gemini AI enrichment"""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.cost_per_token = {
            'gemini-pro': {'input': 0.000125, 'output': 0.000375},  # per 1K tokens
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.00375},
            'gemini-1.5-flash': {'input': 0.000125, 'output': 0.000375},
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        if model not in self.cost_per_token:
            model = 'gemini-pro'  # fallback
        
        rates = self.cost_per_token[model]
        input_cost = (input_tokens / 1000) * rates['input']
        output_cost = (output_tokens / 1000) * rates['output']
        
        return input_cost + output_cost
    
    async def enrich_data(
        self, 
        extracted_data: Dict[str, Any], 
        prompt: str, 
        model: str = "gemini-pro"
    ) -> Dict[str, Any]:
        """Enrich extracted data using Gemini"""
        
        start_time = time.time()
        
        result = {
            'enriched_data': None,
            'model_used': model,
            'cost': 0.0,
            'input_tokens': 0,
            'output_tokens': 0,
            'duration_seconds': 0,
            'error': None
        }
        
        try:
            # Prepare the data for Gemini
            data_json = json.dumps(extracted_data, indent=2, ensure_ascii=False)
            
            # Create the full prompt
            full_prompt = f"""
{prompt}

Raw extracted data:
{data_json}

Please analyze and enrich this data according to the instructions above. 
Return your response as valid JSON.
"""
            
            logger.info("Sending data to Gemini", 
                       model=model, 
                       data_size=len(data_json),
                       prompt_preview=prompt[:100])
            
            # Estimate input tokens
            input_tokens = self.estimate_tokens(full_prompt)
            
            # Initialize the model
            model_instance = genai.GenerativeModel(model)
            
            # Generate content
            response = model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent results
                    max_output_tokens=4096,
                )
            )
            
            if not response.text:
                raise Exception("Empty response from Gemini")
            
            # Estimate output tokens
            output_tokens = self.estimate_tokens(response.text)
            
            # Try to parse as JSON
            try:
                enriched_data = json.loads(response.text)
            except json.JSONDecodeError:
                # If not valid JSON, wrap the response
                enriched_data = {
                    'analysis': response.text,
                    'raw_response': True
                }
            
            # Calculate cost
            cost = self.calculate_cost(model, input_tokens, output_tokens)
            
            result.update({
                'enriched_data': enriched_data,
                'cost': cost,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'duration_seconds': time.time() - start_time
            })
            
            logger.info("Gemini enrichment completed", 
                       model=model, 
                       cost=cost,
                       input_tokens=input_tokens,
                       output_tokens=output_tokens)
            
        except Exception as e:
            error_msg = str(e)
            result.update({
                'error': error_msg,
                'duration_seconds': time.time() - start_time
            })
            
            logger.error("Gemini enrichment failed", 
                        model=model, 
                        error=error_msg)
            
            # Handle rate limiting
            if 'rate limit' in error_msg.lower() or 'quota' in error_msg.lower():
                # Could implement exponential backoff here
                pass
        
        return result
    
    async def enrich_with_retry(
        self, 
        extracted_data: Dict[str, Any], 
        prompt: str, 
        model: str = "gemini-pro",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Enrich data with retry logic for rate limits"""
        
        last_result = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                # Exponential backoff for rate limiting
                wait_time = min(2 ** attempt * 5, 120)  # 5s, 10s, 20s, up to 2min
                logger.info("Retrying Gemini request", 
                           attempt=attempt, 
                           wait_time=wait_time)
                await asyncio.sleep(wait_time)
            
            result = await self.enrich_data(extracted_data, prompt, model)
            last_result = result
            
            if not result.get('error'):
                return result
            
            # Check if we should retry
            error = result.get('error', '').lower()
            if 'rate limit' not in error and 'quota' not in error:
                # Don't retry for non-rate-limit errors
                break
        
        return last_result
    
    def get_available_models(self) -> list:
        """Get list of available Gemini models"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name.replace('models/', ''))
            return models
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            return ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']


# Import asyncio here to avoid issues
import asyncio