"""
Token usage tracking for OpenAI and other LLM APIs
"""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token usage metrics"""
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    request_id: Optional[str] = None
    cost_estimate: Optional[float] = None

class TokenTracker:
    """Track token usage across requests"""
    
    # Pricing per 1K tokens (approximate as of 2024)
    PRICING = {
        'gpt-4o': {'input': 0.005, 'output': 0.015},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
        'text-embedding-3-small': {'input': 0.00002, 'output': 0.0},
        'text-embedding-ada-002': {'input': 0.0001, 'output': 0.0}
    }
    
    def __init__(self):
        self.usage_history: List[TokenUsage] = []
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def track_usage(self, usage_data: Dict[str, Any], model: str = "unknown", request_id: Optional[str] = None):
        """Track token usage from API response"""
        try:
            # Handle different formats of usage data
            if isinstance(usage_data, dict):
                # Check if it's the new nested usage format from the chat response
                if 'usage' in usage_data and usage_data['usage']:
                    usage_obj = usage_data['usage']
                    prompt_tokens = usage_obj.get('request_tokens', 0)
                    completion_tokens = usage_obj.get('response_tokens', 0)
                    total_tokens = usage_obj.get('total_tokens', prompt_tokens + completion_tokens)
                else:
                    # Direct usage data format
                    prompt_tokens = usage_data.get('request_tokens', usage_data.get('prompt_tokens', 0))
                    completion_tokens = usage_data.get('response_tokens', usage_data.get('completion_tokens', 0))
                    total_tokens = usage_data.get('total_tokens', prompt_tokens + completion_tokens)
            else:
                # Assume it's a Usage object with attributes
                prompt_tokens = getattr(usage_data, 'request_tokens', getattr(usage_data, 'prompt_tokens', 0))
                completion_tokens = getattr(usage_data, 'response_tokens', getattr(usage_data, 'completion_tokens', 0))
                total_tokens = getattr(usage_data, 'total_tokens', prompt_tokens + completion_tokens)
            
            # Calculate cost estimate
            cost_estimate = self._calculate_cost(model, prompt_tokens, completion_tokens)
            
            usage = TokenUsage(
                timestamp=datetime.now(timezone.utc),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=model,
                request_id=request_id,
                cost_estimate=cost_estimate
            )
            
            self.usage_history.append(usage)
            self.total_tokens += total_tokens
            self.total_cost += cost_estimate or 0.0
            
            logger.debug(f"Tracked token usage: {total_tokens} tokens, ${cost_estimate:.4f} estimated cost")
            
        except Exception as e:
            logger.error(f"Error tracking token usage: {e}")
            logger.error(f"Usage data received: {usage_data}")
    
    def track_usage_from_response(self, response_json: Dict[str, Any], model: str = "gpt-4o"):
        """Track token usage from chat API response"""
        try:
            # Extract usage information from the chat response
            if 'usage' in response_json and response_json['usage']:
                self.track_usage(response_json['usage'], model)
            else:
                logger.warning(f"No usage information found in response: {list(response_json.keys())}")
        except Exception as e:
            logger.error(f"Error tracking usage from response: {e}")
            logger.error(f"Response: {response_json}")
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost based on token usage"""
        if model not in self.PRICING:
            # Default to GPT-4 pricing if model unknown
            pricing = self.PRICING['gpt-4']
        else:
            pricing = self.PRICING[model]
        
        input_cost = (prompt_tokens / 1000) * pricing['input']
        output_cost = (completion_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of token usage"""
        if not self.usage_history:
            return {
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_tokens_per_request': 0,
                'models_used': []
            }
        
        models_used = list(set(usage.model for usage in self.usage_history))
        avg_tokens = self.total_tokens / len(self.usage_history)
        
        # Group by model
        model_breakdown = {}
        for usage in self.usage_history:
            if usage.model not in model_breakdown:
                model_breakdown[usage.model] = {
                    'requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0
                }
            
            model_breakdown[usage.model]['requests'] += 1
            model_breakdown[usage.model]['total_tokens'] += usage.total_tokens
            model_breakdown[usage.model]['total_cost'] += usage.cost_estimate or 0.0
        
        return {
            'total_requests': len(self.usage_history),
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'avg_tokens_per_request': avg_tokens,
            'models_used': models_used,
            'model_breakdown': model_breakdown,
            'cost_per_request': self.total_cost / len(self.usage_history) if self.usage_history else 0
        }
    
    def get_usage_by_time_window(self, minutes: int = 60) -> Dict[str, Any]:
        """Get token usage for a specific time window"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (minutes * 60)
        
        recent_usage = [
            usage for usage in self.usage_history 
            if usage.timestamp.timestamp() > cutoff_time
        ]
        
        if not recent_usage:
            return {'requests': 0, 'tokens': 0, 'cost': 0.0}
        
        total_tokens = sum(usage.total_tokens for usage in recent_usage)
        total_cost = sum(usage.cost_estimate or 0.0 for usage in recent_usage)
        
        return {
            'requests': len(recent_usage),
            'tokens': total_tokens,
            'cost': total_cost,
            'tokens_per_minute': total_tokens / minutes,
            'cost_per_minute': total_cost / minutes
        }
    
    def save_usage_to_file(self, filepath: str):
        """Save token usage history to JSON file"""
        data = {
            'summary': self.get_usage_summary(),
            'usage_history': [asdict(usage) for usage in self.usage_history]
        }
        
        # Convert datetime objects to strings
        for usage in data['usage_history']:
            usage['timestamp'] = usage['timestamp'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Token usage data saved to {filepath}")
    
    def check_cost_limits(self, max_cost_per_hour: float = 10.0) -> Dict[str, Any]:
        """Check if token usage exceeds cost limits"""
        hourly_usage = self.get_usage_by_time_window(60)
        
        return {
            'within_limits': hourly_usage['cost'] <= max_cost_per_hour,
            'current_hourly_cost': hourly_usage['cost'],
            'limit': max_cost_per_hour,
            'percentage_used': (hourly_usage['cost'] / max_cost_per_hour) * 100
        }
    
    def reset_tracking(self):
        """Reset all tracking data"""
        self.usage_history.clear()
        self.total_tokens = 0
        self.total_cost = 0.0
        logger.info("Token tracking data reset")


class ProjectedUsageCalculator:
    """Calculate projected usage for scaling scenarios"""
    
    @staticmethod
    def calculate_daily_projection(
        sample_usage: TokenUsage,
        requests_per_user_per_day: int,
        total_daily_users: int
    ) -> Dict[str, Any]:
        """Calculate projected daily usage"""
        
        total_daily_requests = requests_per_user_per_day * total_daily_users
        
        projected_tokens = sample_usage.total_tokens * total_daily_requests
        projected_cost = (sample_usage.cost_estimate or 0.0) * total_daily_requests
        
        return {
            'daily_users': total_daily_users,
            'requests_per_user': requests_per_user_per_day,
            'total_daily_requests': total_daily_requests,
            'projected_daily_tokens': projected_tokens,
            'projected_daily_cost': projected_cost,
            'projected_monthly_cost': projected_cost * 30,
            'projected_yearly_cost': projected_cost * 365
        }
    
    @staticmethod
    def calculate_concurrent_projection(
        avg_tokens_per_request: int,
        avg_cost_per_request: float,
        concurrent_users: int,
        requests_per_minute_per_user: float
    ) -> Dict[str, Any]:
        """Calculate projected usage for concurrent users"""
        
        requests_per_minute = concurrent_users * requests_per_minute_per_user
        tokens_per_minute = requests_per_minute * avg_tokens_per_request
        cost_per_minute = requests_per_minute * avg_cost_per_request
        
        return {
            'concurrent_users': concurrent_users,
            'requests_per_minute': requests_per_minute,
            'tokens_per_minute': tokens_per_minute,
            'cost_per_minute': cost_per_minute,
            'hourly_cost': cost_per_minute * 60,
            'daily_cost_at_peak': cost_per_minute * 60 * 8  # Assuming 8 peak hours
        }
