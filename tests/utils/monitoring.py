"""
Performance monitoring utilities
"""
import psutil
import time
import asyncio
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
import os
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: float
    network_bytes_recv: float
    response_time_ms: float
    requests_per_second: float
    active_connections: int
    error_rate: float

class PerformanceMonitor:
    """Monitor system and application performance"""
    
    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus
        self.metrics_history: List[PerformanceMetrics] = []
        self.start_time = time.time()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Initialize Prometheus metrics if enabled
        if self.enable_prometheus:
            self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics collectors"""
        self.cpu_gauge = Gauge('system_cpu_percent', 'CPU usage percentage')
        self.memory_gauge = Gauge('system_memory_mb', 'Memory usage in MB')
        self.response_time_histogram = Histogram('http_request_duration_seconds', 'HTTP request latency')
        self.request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
        self.error_counter = Counter('http_errors_total', 'Total HTTP errors')
        self.active_connections_gauge = Gauge('active_connections', 'Number of active connections')
    
    def start_monitoring(self, interval: float = 1.0, prometheus_port: int = 8000):
        """Start background monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Start Prometheus server if enabled
        if self.enable_prometheus:
            try:
                start_http_server(prometheus_port)
                logger.info(f"Prometheus metrics server started on port {prometheus_port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        
        while self.is_monitoring:
            try:
                # Get current system metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_info = psutil.virtual_memory()
                
                # Disk I/O metrics
                current_disk_io = psutil.disk_io_counters()
                disk_read_mb = (current_disk_io.read_bytes - last_disk_io.read_bytes) / (1024 * 1024)
                disk_write_mb = (current_disk_io.write_bytes - last_disk_io.write_bytes) / (1024 * 1024)
                last_disk_io = current_disk_io
                
                # Network I/O metrics
                current_network_io = psutil.net_io_counters()
                network_sent = current_network_io.bytes_sent - last_network_io.bytes_sent
                network_recv = current_network_io.bytes_recv - last_network_io.bytes_recv
                last_network_io = current_network_io
                
                # Create metrics snapshot
                metrics = PerformanceMetrics(
                    timestamp=datetime.now(timezone.utc),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_info.used / (1024 * 1024),
                    memory_percent=memory_info.percent,
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb,
                    network_bytes_sent=network_sent,
                    network_bytes_recv=network_recv,
                    response_time_ms=0.0,  # Will be updated by request handlers
                    requests_per_second=0.0,  # Will be calculated
                    active_connections=0,  # Will be updated by connection handlers
                    error_rate=0.0  # Will be calculated
                )
                
                self.metrics_history.append(metrics)
                
                # Update Prometheus metrics if enabled
                if self.enable_prometheus:
                    self.cpu_gauge.set(cpu_percent)
                    self.memory_gauge.set(memory_info.used / (1024 * 1024))
                
                # Keep only last 1000 metrics to prevent memory bloat
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def record_request(self, method: str, endpoint: str, status_code: int, response_time: float):
        """Record a request for metrics"""
        if self.enable_prometheus:
            self.request_counter.labels(method=method, endpoint=endpoint, status=status_code).inc()
            self.response_time_histogram.observe(response_time)
            
            if status_code >= 400:
                self.error_counter.inc()
    
    def update_active_connections(self, count: int):
        """Update active connections count"""
        if self.enable_prometheus:
            self.active_connections_gauge.set(count)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics_history:
            return {}
        
        # Calculate averages and totals
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_mb for m in self.metrics_history]
        response_times = [m.response_time_ms for m in self.metrics_history if m.response_time_ms > 0]
        
        return {
            'duration_seconds': time.time() - self.start_time,
            'total_samples': len(self.metrics_history),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'avg_mb': sum(memory_values) / len(memory_values),
                'max_mb': max(memory_values),
                'min_mb': min(memory_values)
            },
            'response_time': {
                'avg_ms': sum(response_times) / len(response_times) if response_times else 0,
                'max_ms': max(response_times) if response_times else 0,
                'min_ms': min(response_times) if response_times else 0
            }
        }
    
    def save_metrics_to_file(self, filepath: str):
        """Save collected metrics to JSON file"""
        data = {
            'summary': self.get_metrics_summary(),
            'metrics': [asdict(m) for m in self.metrics_history]
        }
        
        # Convert datetime objects to strings
        for metric in data['metrics']:
            metric['timestamp'] = metric['timestamp'].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Metrics saved to {filepath}")
    
    def check_thresholds(self, max_memory_mb: float, max_response_time_ms: float) -> Dict[str, bool]:
        """Check if metrics exceed thresholds"""
        current = self.get_current_metrics()
        if not current:
            return {'memory_ok': True, 'response_time_ok': True}
        
        return {
            'memory_ok': current.memory_mb <= max_memory_mb,
            'response_time_ok': current.response_time_ms <= max_response_time_ms
        }


class AsyncPerformanceMonitor:
    """Async version of performance monitor for async applications"""
    
    def __init__(self):
        self.sync_monitor = PerformanceMonitor()
        self.monitoring_task = None
    
    async def start_monitoring(self, interval: float = 1.0):
        """Start async monitoring"""
        self.sync_monitor.start_monitoring(interval)
        
    async def stop_monitoring(self):
        """Stop async monitoring"""
        self.sync_monitor.stop_monitoring()
    
    async def record_request_async(self, method: str, endpoint: str, status_code: int, response_time: float):
        """Record request asynchronously"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.sync_monitor.record_request,
            method, endpoint, status_code, response_time
        )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return self.sync_monitor.get_metrics_summary()
    
    def save_metrics_to_file(self, filepath: str):
        """Save metrics to file"""
        self.sync_monitor.save_metrics_to_file(filepath)
