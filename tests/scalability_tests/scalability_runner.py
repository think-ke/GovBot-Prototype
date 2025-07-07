"""
Scalability testing suite for GovStack API
Tests for 1000 concurrent users and 40000 daily users scenarios
"""
import asyncio
import time
import json
import random
from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx
import psutil
import statistics

from ..config import config
from ..utils.monitoring import PerformanceMonitor
from ..utils.token_tracker import TokenTracker, ProjectedUsageCalculator


class ScalabilityTestRunner:
    """Main scalability test runner"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.token_tracker = TokenTracker()
        self.test_results = {}
        self.start_time = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all scalability tests"""
        print("🚀 Starting GovStack API Scalability Tests")
        print(f"Target: {config.max_users} concurrent users, {config.daily_users} daily users")
        print("-" * 60)
        
        self.start_time = time.time()
        
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
        try:
            # Run different types of tests
            results = {}
            
            # 1. Baseline performance test
            print("📊 Running baseline performance test...")
            results['baseline'] = await self.test_baseline_performance()
            
            # 2. Concurrent users test
            print("👥 Running concurrent users test...")
            results['concurrent_users'] = await self.test_concurrent_users()
            
            # 3. Daily load simulation
            print("📅 Running daily load simulation...")
            results['daily_load'] = await self.test_daily_load_simulation()
            
            # 4. Stress test (push to limits)
            print("💪 Running stress test...")
            results['stress_test'] = await self.test_stress_scenarios()
            
            # 5. Memory and latency analysis
            print("🧠 Running memory and latency analysis...")
            results['memory_latency'] = await self.test_memory_and_latency()
            
            # 6. Token usage projection
            print("💰 Calculating token usage projections...")
            results['token_projections'] = self.calculate_token_projections()
            
            self.test_results = results
            return results
            
        finally:
            self.performance_monitor.stop_monitoring()
    
    async def test_baseline_performance(self) -> Dict[str, Any]:
        """Test baseline performance with single users"""
        print("  Testing single user performance...")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(10):
                start_time = time.time()
                
                try:
                    payload = {
                        "message": random.choice(config.sample_queries),
                        "session_id": str(uuid4()),
                        "user_id": f"baseline_user_{i}",
                        "metadata": {"test_type": "baseline"}
                    }
                    
                    response = await client.post(
                        f"{config.api_base_url}/chat/",
                        json=payload
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        success_count += 1
                        
                        # Track token usage if available
                        try:
                            data = response.json()
                            self.token_tracker.track_usage_from_response(data)
                        except Exception as e:
                            print(f"    Failed to track token usage: {e}")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    print(f"    Error in baseline test: {e}")
                
                await asyncio.sleep(1)  # 1 second between requests
        
        return {
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'min_response_time_ms': min(response_times) if response_times else 0,
            'max_response_time_ms': max(response_times) if response_times else 0,
            'median_response_time_ms': statistics.median(response_times) if response_times else 0,
            'success_rate': success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0,
            'total_requests': success_count + error_count,
            'successful_requests': success_count,
            'failed_requests': error_count
        }
    
    async def test_concurrent_users(self) -> Dict[str, Any]:
        """Test with multiple concurrent users"""
        concurrent_levels = [10, 25, 50, 100, 250, 500, 1000]
        results = {}
        
        for level in concurrent_levels:
            if level > config.max_users:
                continue
                
            print(f"  Testing {level} concurrent users...")
            
            start_time = time.time()
            response_times = []
            success_count = 0
            error_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create tasks for concurrent requests
                tasks = []
                
                for i in range(level):
                    task = self._send_concurrent_request(client, i, level)
                    tasks.append(task)
                
                # Execute all tasks concurrently
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in task_results:
                    if isinstance(result, Exception):
                        error_count += 1
                    elif result:
                        response_times.append(result['response_time'])
                        if result['success']:
                            success_count += 1
                        else:
                            error_count += 1
            
            test_duration = time.time() - start_time
            
            results[f"{level}_users"] = {
                'concurrent_users': level,
                'test_duration_seconds': test_duration,
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0,
                'min_response_time_ms': min(response_times) if response_times else 0,
                'requests_per_second': level / test_duration if test_duration > 0 else 0,
                'success_rate': success_count / level if level > 0 else 0,
                'successful_requests': success_count,
                'failed_requests': error_count,
                'total_requests': level
            }
            
            # Wait between test levels
            await asyncio.sleep(5)
            
            # Check if we're hitting limits
            current_metrics = self.performance_monitor.get_current_metrics()
            if current_metrics and current_metrics.memory_mb > config.max_memory_mb:
                print(f"    Memory limit reached at {level} users, stopping concurrent test")
                break
        
        return results
    
    async def _send_concurrent_request(self, client: httpx.AsyncClient, user_id: int, level: int) -> Dict[str, Any]:
        """Send a single concurrent request"""
        start_time = time.time()
        
        try:
            payload = {
                "message": random.choice(config.sample_queries),
                "session_id": str(uuid4()),
                "user_id": f"concurrent_user_{level}_{user_id}",
                "metadata": {
                    "test_type": "concurrent",
                    "concurrent_level": level,
                    "user_index": user_id
                }
            }
            
            response = await client.post(
                f"{config.api_base_url}/chat/",
                json=payload
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Track token usage if response is successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token_tracker.track_usage_from_response(data)
                except Exception as e:
                    print(f"    Failed to track token usage in concurrent request: {e}")
            
            return {
                'response_time': response_time,
                'success': response.status_code == 200,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'response_time': (time.time() - start_time) * 1000,
                'success': False,
                'error': str(e)
            }
    
    async def test_daily_load_simulation(self) -> Dict[str, Any]:
        """Simulate daily load patterns"""
        print("  Simulating daily usage patterns...")
        
        # Simulate load distribution across hours
        # Peak hours: 9-11 AM and 2-4 PM
        hourly_distribution = {
            0: 0.01, 1: 0.005, 2: 0.005, 3: 0.005, 4: 0.005, 5: 0.01,
            6: 0.02, 7: 0.04, 8: 0.08, 9: 0.12, 10: 0.15, 11: 0.12,
            12: 0.08, 13: 0.06, 14: 0.12, 15: 0.15, 16: 0.12, 17: 0.08,
            18: 0.06, 19: 0.04, 20: 0.03, 21: 0.02, 22: 0.02, 23: 0.01
        }
        
        # Simulate compressed version (1 minute = 1 hour)
        total_simulated_requests = min(1000, config.daily_users // 40)  # Scale down for testing
        
        results = []
        current_hour = 9  # Start at peak hour
        
        for minute in range(5):  # 5 minutes = 5 hours simulation
            hour_load = hourly_distribution.get(current_hour, 0.05)
            requests_this_minute = int(total_simulated_requests * hour_load)
            
            if requests_this_minute > 0:
                print(f"    Simulating hour {current_hour}: {requests_this_minute} requests")
                
                start_time = time.time()
                success_count = 0
                error_count = 0
                response_times = []
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Spread requests across the minute
                    interval = 60.0 / requests_this_minute if requests_this_minute > 0 else 1.0
                    
                    tasks = []
                    for i in range(requests_this_minute):
                        task = self._send_daily_load_request(client, current_hour, i)
                        tasks.append(task)
                        
                        # Add small delays to spread load
                        if i % 10 == 0:
                            await asyncio.sleep(interval / 10)
                    
                    # Execute requests
                    task_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in task_results:
                        if isinstance(result, Exception):
                            error_count += 1
                        elif result:
                            response_times.append(result['response_time'])
                            if result['success']:
                                success_count += 1
                            else:
                                error_count += 1
                
                duration = time.time() - start_time
                
                results.append({
                    'simulated_hour': current_hour,
                    'requests_sent': requests_this_minute,
                    'successful_requests': success_count,
                    'failed_requests': error_count,
                    'duration_seconds': duration,
                    'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                    'requests_per_second': requests_this_minute / duration if duration > 0 else 0
                })
            
            current_hour = (current_hour + 1) % 24
        
        # Calculate overall daily simulation results
        total_requests = sum(r['requests_sent'] for r in results)
        total_successful = sum(r['successful_requests'] for r in results)
        total_failed = sum(r['failed_requests'] for r in results)
        
        return {
            'hourly_results': results,
            'total_requests': total_requests,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'overall_success_rate': total_successful / total_requests if total_requests > 0 else 0,
            'projected_daily_requests': config.daily_users * 5,  # Assume 5 requests per user per day
            'scaling_factor': config.daily_users / total_requests if total_requests > 0 else 1
        }
    
    async def _send_daily_load_request(self, client: httpx.AsyncClient, hour: int, request_id: int) -> Dict[str, Any]:
        """Send a request as part of daily load simulation"""
        start_time = time.time()
        
        try:
            payload = {
                "message": random.choice(config.sample_queries),
                "session_id": str(uuid4()),
                "user_id": f"daily_user_{hour}_{request_id}",
                "metadata": {
                    "test_type": "daily_load",
                    "simulated_hour": hour
                }
            }
            
            response = await client.post(
                f"{config.api_base_url}/chat/",
                json=payload
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Track token usage if response is successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token_tracker.track_usage_from_response(data)
                except Exception as e:
                    print(f"    Failed to track token usage in daily load request: {e}")
            
            return {
                'response_time': response_time,
                'success': response.status_code == 200,
                'status_code': response.status_code
            }
            
        except Exception:
            return {
                'response_time': (time.time() - start_time) * 1000,
                'success': False
            }
    
    async def test_stress_scenarios(self) -> Dict[str, Any]:
        """Test extreme stress scenarios"""
        print("  Running stress scenarios...")
        
        results = {}
        
        # 1. Rapid fire test
        print("    Testing rapid fire requests...")
        rapid_fire_results = await self._test_rapid_fire()
        results['rapid_fire'] = rapid_fire_results
        
        # 2. Long running conversation test
        print("    Testing long conversations...")
        long_conversation_results = await self._test_long_conversations()
        results['long_conversations'] = long_conversation_results
        
        # 3. Large payload test
        print("    Testing large payloads...")
        large_payload_results = await self._test_large_payloads()
        results['large_payloads'] = large_payload_results
        
        return results
    
    async def _test_rapid_fire(self) -> Dict[str, Any]:
        """Test rapid successive requests"""
        session_id = str(uuid4())
        response_times = []
        success_count = 0
        error_count = 0
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(20):  # 20 rapid requests
                start_time = time.time()
                
                try:
                    payload = {
                        "message": f"Rapid fire query {i}",
                        "session_id": session_id,
                        "user_id": "rapid_fire_user",
                        "metadata": {"test_type": "rapid_fire", "sequence": i}
                    }
                    
                    response = await client.post(
                        f"{config.api_base_url}/chat/",
                        json=payload
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception:
                    error_count += 1
                
                # Very short delay (100ms)
                await asyncio.sleep(0.1)
        
        return {
            'total_requests': 20,
            'successful_requests': success_count,
            'failed_requests': error_count,
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'max_response_time_ms': max(response_times) if response_times else 0
        }
    
    async def _test_long_conversations(self) -> Dict[str, Any]:
        """Test long multi-turn conversations"""
        conversation_queries = [
            "What is the Kenya Film Commission?",
            "What services do they provide?",
            "How can filmmakers apply for support?",
            "What are the eligibility criteria?",
            "What is the application process?",
            "How long does approval take?",
            "What documents are required?",
            "Are there any fees involved?",
            "Can international filmmakers apply?",
            "What happens after approval?"
        ]
        
        session_id = str(uuid4())
        response_times = []
        success_count = 0
        error_count = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, query in enumerate(conversation_queries):
                start_time = time.time()
                
                try:
                    payload = {
                        "message": query,
                        "session_id": session_id,
                        "user_id": "long_conversation_user",
                        "metadata": {
                            "test_type": "long_conversation",
                            "turn": i + 1,
                            "total_turns": len(conversation_queries)
                        }
                    }
                    
                    response = await client.post(
                        f"{config.api_base_url}/chat/",
                        json=payload
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception:
                    error_count += 1
                
                # Wait between conversation turns
                await asyncio.sleep(2)
        
        return {
            'conversation_turns': len(conversation_queries),
            'successful_turns': success_count,
            'failed_turns': error_count,
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'conversation_success_rate': success_count / len(conversation_queries)
        }
    
    async def _test_large_payloads(self) -> Dict[str, Any]:
        """Test handling of large message payloads"""
        large_messages = [
            "Short message",
            "Medium message " * 100,  # ~1.5KB
            "Long message " * 500,    # ~7.5KB
            "Very long message " * 1000  # ~15KB
        ]
        
        results = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, message in enumerate(large_messages):
                start_time = time.time()
                
                try:
                    payload = {
                        "message": message,
                        "session_id": str(uuid4()),
                        "user_id": f"large_payload_user_{i}",
                        "metadata": {
                            "test_type": "large_payload",
                            "message_size": len(message)
                        }
                    }
                    
                    response = await client.post(
                        f"{config.api_base_url}/chat/",
                        json=payload
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    results.append({
                        'message_size_bytes': len(message),
                        'response_time_ms': response_time,
                        'success': response.status_code == 200,
                        'status_code': response.status_code
                    })
                    
                except Exception as e:
                    results.append({
                        'message_size_bytes': len(message),
                        'response_time_ms': (time.time() - start_time) * 1000,
                        'success': False,
                        'error': str(e)
                    })
        
        return {'payload_tests': results}
    
    async def test_memory_and_latency(self) -> Dict[str, Any]:
        """Test memory usage and latency patterns"""
        print("  Analyzing memory and latency...")
        
        # Get initial memory state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        memory_samples = []
        latency_samples = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(50):  # 50 requests to build up memory usage
                start_time = time.time()
                
                try:
                    payload = {
                        "message": random.choice(config.sample_queries),
                        "session_id": str(uuid4()),
                        "user_id": f"memory_test_user_{i}",
                        "metadata": {"test_type": "memory_analysis"}
                    }
                    
                    response = await client.post(
                        f"{config.api_base_url}/chat/",
                        json=payload
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    latency_samples.append(response_time)
                    
                    # Sample memory every 5 requests
                    if i % 5 == 0:
                        current_memory = process.memory_info().rss / (1024 * 1024)
                        memory_samples.append({
                            'request_number': i,
                            'memory_mb': current_memory,
                            'memory_growth_mb': current_memory - initial_memory
                        })
                    
                except Exception:
                    pass
                
                await asyncio.sleep(0.5)  # 500ms between requests
        
        final_memory = process.memory_info().rss / (1024 * 1024)
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'total_memory_growth_mb': final_memory - initial_memory,
            'memory_samples': memory_samples,
            'avg_latency_ms': statistics.mean(latency_samples) if latency_samples else 0,
            'p95_latency_ms': statistics.quantiles(latency_samples, n=20)[18] if len(latency_samples) >= 20 else 0,
            'p99_latency_ms': statistics.quantiles(latency_samples, n=100)[98] if len(latency_samples) >= 100 else 0,
            'max_latency_ms': max(latency_samples) if latency_samples else 0
        }
    
    def calculate_token_projections(self) -> Dict[str, Any]:
        """Calculate token usage projections"""
        usage_summary = self.token_tracker.get_usage_summary()
        
        if usage_summary['total_requests'] == 0:
            return {'error': 'No token usage data available'}
        
        avg_tokens_per_request = usage_summary['avg_tokens_per_request']
        avg_cost_per_request = usage_summary['cost_per_request']
        
        # Project for target scenarios
        daily_projection = ProjectedUsageCalculator.calculate_daily_projection(
            type('MockUsage', (), {
                'total_tokens': int(avg_tokens_per_request),
                'cost_estimate': avg_cost_per_request
            })(),
            requests_per_user_per_day=5,  # Assume 5 requests per user per day
            total_daily_users=config.daily_users
        )
        
        concurrent_projection = ProjectedUsageCalculator.calculate_concurrent_projection(
            avg_tokens_per_request=int(avg_tokens_per_request),
            avg_cost_per_request=avg_cost_per_request,
            concurrent_users=config.max_users,
            requests_per_minute_per_user=1.0  # 1 request per minute per user
        )
        
        return {
            'current_usage': usage_summary,
            'daily_projection': daily_projection,
            'concurrent_projection': concurrent_projection,
            'cost_warning': daily_projection['projected_daily_cost'] > 100  # Warning if > $100/day
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        if not self.test_results:
            return "No test results available"
        
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        report = [
            "=" * 80,
            "🚀 GOVSTACK API SCALABILITY TEST REPORT",
            "=" * 80,
            f"Test Duration: {total_duration:.2f} seconds",
            f"Target Users: {config.max_users} concurrent, {config.daily_users} daily",
            f"Test Completed: {datetime.now(timezone.utc).isoformat()}",
            "",
            "📊 BASELINE PERFORMANCE",
            "-" * 40
        ]
        
        # Add baseline results
        baseline = self.test_results.get('baseline', {})
        report.extend([
            f"Average Response Time: {baseline.get('avg_response_time_ms', 0):.2f}ms",
            f"Success Rate: {baseline.get('success_rate', 0)*100:.1f}%",
            f"Total Requests: {baseline.get('total_requests', 0)}",
            ""
        ])
        
        # Add concurrent users results
        concurrent = self.test_results.get('concurrent_users', {})
        if concurrent:
            report.extend([
                "👥 CONCURRENT USERS TEST",
                "-" * 40
            ])
            
            for level, data in concurrent.items():
                users = data.get('concurrent_users', 0)
                avg_time = data.get('avg_response_time_ms', 0)
                success_rate = data.get('success_rate', 0)
                rps = data.get('requests_per_second', 0)
                
                report.append(f"{users:4d} users: {avg_time:6.1f}ms avg, {success_rate*100:5.1f}% success, {rps:5.1f} req/s")
            
            report.append("")
        
        # Add daily load results
        daily = self.test_results.get('daily_load', {})
        if daily:
            report.extend([
                "📅 DAILY LOAD SIMULATION",
                "-" * 40,
                f"Total Requests: {daily.get('total_requests', 0)}",
                f"Success Rate: {daily.get('overall_success_rate', 0)*100:.1f}%",
                f"Projected Daily Requests: {daily.get('projected_daily_requests', 0):,}",
                ""
            ])
        
        # Add stress test results
        stress = self.test_results.get('stress_test', {})
        if stress:
            report.extend([
                "💪 STRESS TEST RESULTS",
                "-" * 40
            ])
            
            rapid_fire = stress.get('rapid_fire', {})
            if rapid_fire:
                report.append(f"Rapid Fire: {rapid_fire.get('successful_requests', 0)}/{rapid_fire.get('total_requests', 0)} successful")
            
            long_conv = stress.get('long_conversations', {})
            if long_conv:
                report.append(f"Long Conversations: {long_conv.get('conversation_success_rate', 0)*100:.1f}% success rate")
            
            report.append("")
        
        # Add memory and latency analysis
        memory = self.test_results.get('memory_latency', {})
        if memory:
            report.extend([
                "🧠 MEMORY & LATENCY ANALYSIS",
                "-" * 40,
                f"Memory Growth: {memory.get('total_memory_growth_mb', 0):.1f}MB",
                f"Average Latency: {memory.get('avg_latency_ms', 0):.2f}ms",
                f"P95 Latency: {memory.get('p95_latency_ms', 0):.2f}ms",
                f"P99 Latency: {memory.get('p99_latency_ms', 0):.2f}ms",
                ""
            ])
        
        # Add token projections
        tokens = self.test_results.get('token_projections', {})
        if tokens and 'daily_projection' in tokens:
            daily_proj = tokens['daily_projection']
            concurrent_proj = tokens['concurrent_projection']
            
            report.extend([
                "💰 TOKEN USAGE PROJECTIONS",
                "-" * 40,
                f"Projected Daily Cost: ${daily_proj.get('projected_daily_cost', 0):.2f}",
                f"Projected Monthly Cost: ${daily_proj.get('projected_monthly_cost', 0):.2f}",
                f"Peak Hour Cost: ${concurrent_proj.get('hourly_cost', 0):.2f}",
                ""
            ])
        
        # Add recommendations
        report.extend([
            "📋 RECOMMENDATIONS",
            "-" * 40
        ])
        
        # Generate recommendations based on results
        recommendations = self._generate_recommendations()
        report.extend(recommendations)
        
        report.extend([
            "",
            "=" * 80,
            "End of Report",
            "=" * 80
        ])
        
        return "\n".join(report)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check baseline performance
        baseline = self.test_results.get('baseline', {})
        if baseline.get('avg_response_time_ms', 0) > config.max_response_time_ms:
            recommendations.append("⚠️  Response times exceed target - consider optimization")
        
        if baseline.get('success_rate', 1) < config.min_success_rate:
            recommendations.append("⚠️  Success rate below target - investigate error causes")
        
        # Check memory usage
        memory = self.test_results.get('memory_latency', {})
        if memory.get('total_memory_growth_mb', 0) > 100:
            recommendations.append("⚠️  High memory growth detected - check for memory leaks")
        
        # Check token costs
        tokens = self.test_results.get('token_projections', {})
        if tokens.get('cost_warning', False):
            recommendations.append("💰 High projected costs - consider cost optimization strategies")
        
        # Concurrent user performance
        concurrent = self.test_results.get('concurrent_users', {})
        if concurrent:
            # Find the highest successful level
            max_successful_users = 0
            for level, data in concurrent.items():
                if data.get('success_rate', 0) >= 0.95:  # 95% success rate
                    max_successful_users = max(max_successful_users, data.get('concurrent_users', 0))
            
            if max_successful_users < config.max_users:
                recommendations.append(f"📈 System handles up to {max_successful_users} concurrent users reliably")
                recommendations.append("🔧 Consider scaling infrastructure for higher loads")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - system appears ready for target load")
        
        return recommendations
    
    def save_results(self, filepath: str):
        """Save test results to JSON file"""
        output_data = {
            'test_config': config.to_dict(),
            'test_results': self.test_results,
            'test_duration_seconds': time.time() - self.start_time if self.start_time else 0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'performance_summary': self.performance_monitor.get_metrics_summary(),
            'token_summary': self.token_tracker.get_usage_summary()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📁 Test results saved to {filepath}")


async def main():
    """Run the scalability test suite"""
    runner = ScalabilityTestRunner()
    
    try:
        results = await runner.run_all_tests()
        
        # Generate and print report
        report = runner.generate_report()
        print(report)
        
        # Save results
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        results_file = f"scalability_test_results_{timestamp}.json"
        runner.save_results(results_file)
        
        # Save performance metrics
        metrics_file = f"performance_metrics_{timestamp}.json"
        runner.performance_monitor.save_metrics_to_file(metrics_file)
        
        # Save token usage data
        token_file = f"token_usage_{timestamp}.json"
        runner.token_tracker.save_usage_to_file(token_file)
        
        print(f"\n📊 All data saved:")
        print(f"  - Test results: {results_file}")
        print(f"  - Performance metrics: {metrics_file}")
        print(f"  - Token usage: {token_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
