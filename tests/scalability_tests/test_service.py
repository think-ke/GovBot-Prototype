"""
Test microservice main application
FastAPI service for running tests as a microservice
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import uuid
import json
import os
from datetime import datetime, timezone

from .scalability_runner import ScalabilityTestRunner
from ..config import config

app = FastAPI(
    title="GovStack Test Service",
    description="Scalability and performance testing microservice for GovStack API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test execution tracking
running_tests: Dict[str, Dict[str, Any]] = {}
test_results: Dict[str, Dict[str, Any]] = {}

class TestRunRequest(BaseModel):
    """Request model for starting a test run"""
    test_types: List[str] = ["baseline", "concurrent", "daily_load", "stress", "memory"]
    max_users: Optional[int] = None
    daily_users: Optional[int] = None
    custom_config: Optional[Dict[str, Any]] = None

class TestRunResponse(BaseModel):
    """Response model for test run creation"""
    test_id: str
    status: str
    message: str
    estimated_duration_minutes: int

class TestStatusResponse(BaseModel):
    """Response model for test status"""
    test_id: str
    status: str
    progress: float
    current_phase: str
    start_time: str
    duration_seconds: float
    estimated_remaining_minutes: Optional[int] = None

class TestResultsResponse(BaseModel):
    """Response model for test results"""
    test_id: str
    status: str
    results: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]
    report: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GovStack Test Service",
        "version": "1.0.0",
        "status": "running",
        "active_tests": len(running_tests),
        "completed_tests": len(test_results)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "api_base_url": config.api_base_url,
            "max_users": config.max_users,
            "daily_users": config.daily_users
        }
    }

@app.post("/tests/run", response_model=TestRunResponse)
async def start_test_run(request: TestRunRequest, background_tasks: BackgroundTasks):
    """Start a new test run"""
    test_id = str(uuid.uuid4())
    
    # Update config if custom values provided
    if request.max_users:
        config.max_users = request.max_users
    if request.daily_users:
        config.daily_users = request.daily_users
    if request.custom_config:
        for key, value in request.custom_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Estimate duration based on test types
    estimated_duration = 0
    if "baseline" in request.test_types:
        estimated_duration += 2
    if "concurrent" in request.test_types:
        estimated_duration += 10
    if "daily_load" in request.test_types:
        estimated_duration += 15
    if "stress" in request.test_types:
        estimated_duration += 8
    if "memory" in request.test_types:
        estimated_duration += 5
    
    # Initialize test tracking
    running_tests[test_id] = {
        "status": "starting",
        "progress": 0.0,
        "current_phase": "initializing",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "test_types": request.test_types,
        "estimated_duration_minutes": estimated_duration
    }
    
    # Start test in background
    background_tasks.add_task(run_scalability_test, test_id, request.test_types)
    
    return TestRunResponse(
        test_id=test_id,
        status="started",
        message=f"Test run {test_id} started successfully",
        estimated_duration_minutes=estimated_duration
    )

@app.get("/tests/{test_id}/status", response_model=TestStatusResponse)
async def get_test_status(test_id: str):
    """Get the status of a running test"""
    if test_id not in running_tests and test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test_id in running_tests:
        test_info = running_tests[test_id]
        start_time = datetime.fromisoformat(test_info["start_time"])
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Estimate remaining time
        estimated_total = test_info.get("estimated_duration_minutes", 30) * 60
        estimated_remaining = max(0, estimated_total - duration) / 60
        
        return TestStatusResponse(
            test_id=test_id,
            status=test_info["status"],
            progress=test_info["progress"],
            current_phase=test_info["current_phase"],
            start_time=test_info["start_time"],
            duration_seconds=duration,
            estimated_remaining_minutes=int(estimated_remaining)
        )
    else:
        # Test completed
        test_info = test_results[test_id]
        return TestStatusResponse(
            test_id=test_id,
            status="completed",
            progress=100.0,
            current_phase="finished",
            start_time=test_info["start_time"],
            duration_seconds=test_info["duration_seconds"]
        )

@app.get("/tests/{test_id}/results", response_model=TestResultsResponse)
async def get_test_results(test_id: str):
    """Get the results of a completed test"""
    if test_id not in test_results:
        if test_id in running_tests:
            raise HTTPException(status_code=409, detail="Test is still running")
        else:
            raise HTTPException(status_code=404, detail="Test not found")
    
    test_data = test_results[test_id]
    
    return TestResultsResponse(
        test_id=test_id,
        status="completed",
        results=test_data["results"],
        summary=test_data["summary"],
        recommendations=test_data["recommendations"],
        report=test_data["report"]
    )

@app.get("/tests")
async def list_tests():
    """List all tests (running and completed)"""
    all_tests = []
    
    # Add running tests
    for test_id, info in running_tests.items():
        all_tests.append({
            "test_id": test_id,
            "status": info["status"],
            "start_time": info["start_time"],
            "test_types": info["test_types"]
        })
    
    # Add completed tests
    for test_id, info in test_results.items():
        all_tests.append({
            "test_id": test_id,
            "status": "completed",
            "start_time": info["start_time"],
            "duration_seconds": info["duration_seconds"]
        })
    
    return {"tests": all_tests}

@app.delete("/tests/{test_id}")
async def delete_test(test_id: str):
    """Delete test results"""
    deleted = False
    
    if test_id in running_tests:
        # Can't delete running test
        raise HTTPException(status_code=409, detail="Cannot delete running test")
    
    if test_id in test_results:
        del test_results[test_id]
        deleted = True
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {"message": f"Test {test_id} deleted successfully"}

@app.post("/tests/quick-check")
async def quick_performance_check():
    """Run a quick performance check"""
    runner = ScalabilityTestRunner()
    
    try:
        # Run only baseline test
        baseline_results = await runner.test_baseline_performance()
        
        # Quick health assessment
        avg_response_time = baseline_results.get('avg_response_time_ms', 0)
        success_rate = baseline_results.get('success_rate', 0)
        
        health_status = "healthy"
        if avg_response_time > config.max_response_time_ms:
            health_status = "slow"
        if success_rate < config.min_success_rate:
            health_status = "unhealthy"
        
        return {
            "health_status": health_status,
            "avg_response_time_ms": avg_response_time,
            "success_rate": success_rate * 100,
            "total_requests": baseline_results.get('total_requests', 0),
            "recommendations": _generate_quick_recommendations(baseline_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick check failed: {str(e)}")

def _generate_quick_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate quick recommendations"""
    recommendations = []
    
    if results.get('avg_response_time_ms', 0) > 2000:
        recommendations.append("Response times are slow - consider optimization")
    
    if results.get('success_rate', 1) < 0.95:
        recommendations.append("Success rate is low - investigate errors")
    
    if not recommendations:
        recommendations.append("System performance looks good")
    
    return recommendations

async def run_scalability_test(test_id: str, test_types: List[str]):
    """Background task to run scalability tests"""
    try:
        runner = ScalabilityTestRunner()
        
        # Update status
        running_tests[test_id]["status"] = "running"
        running_tests[test_id]["current_phase"] = "initializing"
        running_tests[test_id]["progress"] = 0.0
        
        results = {}
        total_phases = len(test_types)
        
        # Run each test type
        for i, test_type in enumerate(test_types):
            running_tests[test_id]["current_phase"] = test_type
            running_tests[test_id]["progress"] = (i / total_phases) * 100
            
            if test_type == "baseline":
                results['baseline'] = await runner.test_baseline_performance()
            elif test_type == "concurrent":
                results['concurrent_users'] = await runner.test_concurrent_users()
            elif test_type == "daily_load":
                results['daily_load'] = await runner.test_daily_load_simulation()
            elif test_type == "stress":
                results['stress_test'] = await runner.test_stress_scenarios()
            elif test_type == "memory":
                results['memory_latency'] = await runner.test_memory_and_latency()
        
        # Add token projections if we have data
        if runner.token_tracker.usage_history:
            results['token_projections'] = runner.calculate_token_projections()
        
        # Generate report
        runner.test_results = results
        report = runner.generate_report()
        
        # Calculate summary
        summary = {
            "total_requests": sum(r.get('total_requests', 0) for r in results.values() if isinstance(r, dict)),
            "overall_success_rate": 0.0,  # Calculate this properly
            "performance_summary": runner.performance_monitor.get_metrics_summary(),
            "token_summary": runner.token_tracker.get_usage_summary()
        }
        
        # Generate recommendations
        recommendations = runner._generate_recommendations()
        
        # Move to completed
        start_time = running_tests[test_id]["start_time"]
        duration = (datetime.now(timezone.utc) - datetime.fromisoformat(start_time)).total_seconds()
        
        test_results[test_id] = {
            "start_time": start_time,
            "duration_seconds": duration,
            "results": results,
            "summary": summary,
            "recommendations": recommendations,
            "report": report
        }
        
        # Remove from running tests
        del running_tests[test_id]
        
    except Exception as e:
        # Handle error
        running_tests[test_id]["status"] = "failed"
        running_tests[test_id]["error"] = str(e)
        print(f"Test {test_id} failed: {e}")

# Configuration endpoints
@app.get("/config")
async def get_config():
    """Get current test configuration"""
    return config.to_dict()

@app.put("/config")
async def update_config(new_config: Dict[str, Any]):
    """Update test configuration"""
    updated_fields = []
    
    for key, value in new_config.items():
        if hasattr(config, key):
            setattr(config, key, value)
            updated_fields.append(key)
    
    return {
        "message": "Configuration updated",
        "updated_fields": updated_fields,
        "current_config": config.to_dict()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
