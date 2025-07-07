"""
CLI tool for running scalability tests
"""
import typer
import asyncio
import json
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import httpx
import time

from scalability_tests.scalability_runner import ScalabilityTestRunner
from config import config

console = Console()
app = typer.Typer(help="GovStack Scalability Testing CLI")

@app.command()
def run(
    test_types: List[str] = typer.Option(
        ["baseline", "concurrent", "daily_load", "stress", "memory"],
        "--test",
        "-t",
        help="Types of tests to run"
    ),
    max_users: int = typer.Option(config.max_users, "--max-users", "-u", help="Maximum concurrent users"),
    daily_users: int = typer.Option(config.daily_users, "--daily-users", "-d", help="Daily users target"),
    api_url: str = typer.Option(config.api_base_url, "--api-url", "-a", help="API base URL"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Run scalability tests directly"""
    
    console.print(Panel.fit("🚀 GovStack Scalability Tests", style="bold blue"))
    
    # Update config
    config.max_users = max_users
    config.daily_users = daily_users
    config.api_base_url = api_url
    
    # Display test configuration
    config_table = Table(title="Test Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")
    
    config_table.add_row("API URL", api_url)
    config_table.add_row("Max Concurrent Users", str(max_users))
    config_table.add_row("Daily Users Target", str(daily_users))
    config_table.add_row("Test Types", ", ".join(test_types))
    
    console.print(config_table)
    console.print()
    
    # Run tests
    async def run_tests():
        runner = ScalabilityTestRunner()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Create progress tasks
            tasks = {}
            for test_type in test_types:
                tasks[test_type] = progress.add_task(f"[cyan]Running {test_type} test...", total=1)
            
            results = {}
            
            # Run each test
            for test_type in test_types:
                progress.update(tasks[test_type], description=f"[yellow]Running {test_type} test...")
                
                try:
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
                    
                    progress.update(tasks[test_type], completed=1, description=f"[green]✓ {test_type} test completed")
                    
                except Exception as e:
                    progress.update(tasks[test_type], description=f"[red]✗ {test_type} test failed: {e}")
                    if verbose:
                        console.print_exception()
            
            # Add token projections
            if runner.token_tracker.usage_history:
                results['token_projections'] = runner.calculate_token_projections()
            
            # Generate report
            runner.test_results = results
            report = runner.generate_report()
            
            console.print()
            console.print(Panel(report, title="Test Report", expand=False))
            
            # Save results if output specified
            if output:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_file = output or f"scalability_test_results_{timestamp}.json"
                
                output_data = {
                    'test_config': config.to_dict(),
                    'test_results': results,
                    'report': report
                }
                
                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                console.print(f"[green]Results saved to {output_file}")
    
    # Run the async function
    asyncio.run(run_tests())

@app.command()
def service(
    port: int = typer.Option(8084, "--port", "-p", help="Port to run the test service on"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind the service to")
):
    """Start the test microservice"""
    console.print(f"🚀 Starting GovStack Test Service on {host}:{port}")
    
    import uvicorn
    from scalability_tests.test_service import app as test_app
    
    uvicorn.run(test_app, host=host, port=port)

@app.command()
def quick_check(
    api_url: str = typer.Option(config.api_base_url, "--api-url", "-a", help="API base URL")
):
    """Run a quick performance check"""
    console.print("🔍 Running quick performance check...")
    
    async def check():
        runner = ScalabilityTestRunner()
        
        try:
            # Update API URL
            config.api_base_url = api_url
            
            # Run baseline test
            results = await runner.test_baseline_performance()
            
            # Display results
            table = Table(title="Quick Performance Check Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")
            table.add_column("Status", style="green")
            
            avg_time = results.get('avg_response_time_ms', 0)
            success_rate = results.get('success_rate', 0) * 100
            
            # Response time status
            time_status = "✅ Good" if avg_time < 2000 else "⚠️ Slow" if avg_time < 5000 else "❌ Poor"
            success_status = "✅ Good" if success_rate >= 95 else "⚠️ Fair" if success_rate >= 90 else "❌ Poor"
            
            table.add_row("Average Response Time", f"{avg_time:.1f}ms", time_status)
            table.add_row("Success Rate", f"{success_rate:.1f}%", success_status)
            table.add_row("Total Requests", str(results.get('total_requests', 0)), "ℹ️ Info")
            
            console.print(table)
            
            # Recommendations
            recommendations = []
            if avg_time > 2000:
                recommendations.append("Consider optimizing response times")
            if success_rate < 95:
                recommendations.append("Investigate failed requests")
            if not recommendations:
                recommendations.append("System performance looks good!")
            
            console.print("\n📋 Recommendations:")
            for rec in recommendations:
                console.print(f"  • {rec}")
                
        except Exception as e:
            console.print(f"[red]Quick check failed: {e}")
            if typer.confirm("Show detailed error?"):
                console.print_exception()
    
    asyncio.run(check())

@app.command()
def remote_test(
    service_url: str = typer.Argument(..., help="URL of the test service"),
    test_types: List[str] = typer.Option(
        ["baseline", "concurrent"],
        "--test",
        "-t",
        help="Types of tests to run"
    ),
    max_users: int = typer.Option(1000, "--max-users", "-u", help="Maximum concurrent users"),
    daily_users: int = typer.Option(40000, "--daily-users", "-d", help="Daily users target"),
):
    """Start a test run on a remote test service"""
    
    async def start_remote_test():
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Start test
                console.print(f"🚀 Starting remote test on {service_url}")
                
                payload = {
                    "test_types": test_types,
                    "max_users": max_users,
                    "daily_users": daily_users
                }
                
                response = await client.post(f"{service_url}/tests/run", json=payload)
                response.raise_for_status()
                
                result = response.json()
                test_id = result["test_id"]
                
                console.print(f"✅ Test started with ID: {test_id}")
                console.print(f"⏱️ Estimated duration: {result['estimated_duration_minutes']} minutes")
                
                # Poll for status
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    
                    task = progress.add_task("[cyan]Running tests...", total=100)
                    
                    while True:
                        status_response = await client.get(f"{service_url}/tests/{test_id}/status")
                        status_response.raise_for_status()
                        
                        status_data = status_response.json()
                        progress_val = status_data["progress"]
                        current_phase = status_data["current_phase"]
                        
                        progress.update(
                            task, 
                            completed=progress_val, 
                            description=f"[yellow]{current_phase}..."
                        )
                        
                        if status_data["status"] == "completed":
                            break
                        elif status_data["status"] == "failed":
                            console.print("[red]Test failed!")
                            return
                        
                        await asyncio.sleep(5)  # Poll every 5 seconds
                
                # Get results
                results_response = await client.get(f"{service_url}/tests/{test_id}/results")
                results_response.raise_for_status()
                
                results_data = results_response.json()
                
                console.print()
                console.print(Panel(results_data["report"], title="Test Report", expand=False))
                
                # Show recommendations
                if results_data["recommendations"]:
                    console.print("\n📋 Recommendations:")
                    for rec in results_data["recommendations"]:
                        console.print(f"  • {rec}")
                
            except httpx.HTTPError as e:
                console.print(f"[red]HTTP error: {e}")
            except Exception as e:
                console.print(f"[red]Error: {e}")
    
    asyncio.run(start_remote_test())

@app.command()
def locust_ui(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind Locust UI"),
    port: int = typer.Option(8089, "--port", "-p", help="Port for Locust UI"),
    target_url: str = typer.Option(config.api_base_url, "--target", "-t", help="Target API URL")
):
    """Start Locust web UI for interactive load testing"""
    console.print(f"🌍 Starting Locust web UI on http://{host}:{port}")
    console.print(f"🎯 Target URL: {target_url}")
    
    import subprocess
    import os
    
    # Set environment variables for Locust
    env = os.environ.copy()
    env['API_BASE_URL'] = target_url
    
    # Start Locust
    cmd = [
        "locust",
        "-f", "tests/load_tests/locust_tests.py",
        "--host", target_url,
        "--web-host", host,
        "--web-port", str(port)
    ]
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        console.print("\n⏹️ Locust stopped")
    except FileNotFoundError:
        console.print("[red]Locust not found. Install with: pip install locust")

if __name__ == "__main__":
    app()
