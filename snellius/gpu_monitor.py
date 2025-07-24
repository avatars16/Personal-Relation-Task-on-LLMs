import time
import threading
import os
import csv
from datetime import datetime

# Add pynvml for GPU monitoring
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    print("pynvml not available. GPU monitoring will be disabled. Install with: pip install pynvml")

class GPUMonitor:
    """Monitor GPU usage and memory"""
    def __init__(self, monitor_interval=1.0, log_dir=None):
        self.keep_monitoring = False
        self.monitoring_thread = None
        self.monitor_interval = monitor_interval
        self.gpu_logs = []
        self.monitoring_session_id = None
        
        # Set up logging directory
        if log_dir is None:
            self.log_dir = os.path.join(os.getcwd(), "gpu_logs")
        else:
            self.log_dir = log_dir
            
        os.makedirs(self.log_dir, exist_ok=True)
        
        if not PYNVML_AVAILABLE:
            print("GPU monitoring disabled: pynvml not installed")
            return
            
        try:
            pynvml.nvmlInit()
            self.device_count = pynvml.nvmlDeviceGetCount()
            print(f"GPU monitoring initialized. Found {self.device_count} GPU devices.")
        except Exception as e:
            print(f"Failed to initialize GPU monitoring: {e}")
            self.device_count = 0
    
    def get_gpu_metrics(self):
        """Get current GPU metrics for all devices"""
        if not PYNVML_AVAILABLE:
            return None
        
        metrics = []
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                metrics.append({
                    'device_id': i,
                    'gpu_util': util.gpu,  # GPU utilization percentage
                    'memory_used': mem_info.used / (1024 ** 2),  # MB
                    'memory_total': mem_info.total / (1024 ** 2),  # MB
                    'memory_util': (mem_info.used / mem_info.total) * 100,  # Percentage
                    'temperature': temperature,  # Celsius
                    'timestamp': time.time()
                })
        except Exception as e:
            print(f"Error getting GPU metrics: {e}")
        
        return metrics
    
    def log_gpu_metrics(self, log_to_csv=False, description=None):
        """Log current GPU metrics"""
        metrics = self.get_gpu_metrics()
        if not metrics:
            return
            
        # Log to console
        for device_metrics in metrics:
            device_id = device_metrics['device_id']
            print(f"GPU {device_id}: Util={device_metrics['gpu_util']}%, "
                  f"Mem={device_metrics['memory_used']:.0f}/{device_metrics['memory_total']:.0f}MB "
                  f"({device_metrics['memory_util']:.1f}%), "
                  f"Temp={device_metrics['temperature']}°C")
        
        # Store in memory
        self.gpu_logs.append(metrics)
        
        # Log to CSV if requested
        if log_to_csv:
            if self.monitoring_session_id is None:
                self.monitoring_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create a timestamp to describe this metrics collection
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate a descriptive filename
            if description:
                csv_filename = f"gpu_metrics_{self.monitoring_session_id}_{description}.csv"
            else:
                csv_filename = f"gpu_metrics_{self.monitoring_session_id}.csv"
            
            csv_path = os.path.join(self.log_dir, csv_filename)
            
            # Check if file exists to decide if we need headers
            file_exists = os.path.isfile(csv_path)
            
            with open(csv_path, mode='a', newline='') as file:
                fieldnames = ['timestamp', 'event_description', 'device_id', 'gpu_util', 'memory_used', 
                              'memory_total', 'memory_util', 'temperature']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                for device_metrics in metrics:
                    row = {
                        'timestamp': timestamp,
                        'event_description': description or 'regular_check',
                        'device_id': device_metrics['device_id'],
                        'gpu_util': device_metrics['gpu_util'],
                        'memory_used': device_metrics['memory_used'],
                        'memory_total': device_metrics['memory_total'],
                        'memory_util': device_metrics['memory_util'],
                        'temperature': device_metrics['temperature']
                    }
                    writer.writerow(row)
        
    def monitor_gpu(self, log_to_csv=False, description=None):
        """Monitoring thread function"""
        while self.keep_monitoring:
            self.log_gpu_metrics(log_to_csv=log_to_csv, description=description)
            time.sleep(self.monitor_interval)
    
    def start_monitoring(self, log_to_csv=False, description="continuous_monitoring"):
        """Start GPU monitoring in a separate thread"""
        if not PYNVML_AVAILABLE or self.device_count == 0:
            return False
            
        if self.monitoring_thread is not None and self.monitoring_thread.is_alive():
            print("Monitoring already running")
            return True
        
        # Generate a new session ID if needed
        if self.monitoring_session_id is None:
            self.monitoring_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Reset logs for new monitoring session
        self.gpu_logs = []
        self.keep_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self.monitor_gpu, 
            args=(log_to_csv, description)
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        return True
        
    def stop_monitoring(self):
        """Stop GPU monitoring"""
        self.keep_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
            
    def get_summary(self):
        """Get summary of GPU usage during monitoring period"""
        if not self.gpu_logs:
            return "No GPU metrics collected"
            
        summary = {}
        for device_id in range(self.device_count):
            device_metrics = [log[device_id] for log in self.gpu_logs if device_id < len(log)]
            
            if device_metrics:
                gpu_utils = [m['gpu_util'] for m in device_metrics]
                mem_utils = [m['memory_util'] for m in device_metrics]
                
                summary[f"GPU_{device_id}"] = {
                    'avg_gpu_util': sum(gpu_utils) / len(gpu_utils),
                    'max_gpu_util': max(gpu_utils),
                    'avg_mem_util': sum(mem_utils) / len(mem_utils),
                    'max_mem_util': max(mem_utils),
                    'max_mem_used': max(m['memory_used'] for m in device_metrics),
                    'mem_total': device_metrics[0]['memory_total']
                }
        
        return summary
    
    def save_summary_to_csv(self, description="summary", include_full_logs=False):
        """Save monitoring summary to CSV file"""
        if not self.gpu_logs:
            print("No GPU metrics to summarize")
            return None
        
        if self.monitoring_session_id is None:
            self.monitoring_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create summary filename
        csv_filename = f"gpu_summary_{self.monitoring_session_id}_{description}.csv"
        csv_path = os.path.join(self.log_dir, csv_filename)
        
        summary = self.get_summary()
        
        # Save summary data
        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # Write header and metadata
            writer.writerow(['GPU Monitoring Summary'])
            writer.writerow(['Session ID', self.monitoring_session_id])
            writer.writerow(['Description', description])
            writer.writerow(['Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(['Monitoring Duration', f"{len(self.gpu_logs) * self.monitor_interval:.2f} seconds"])
            writer.writerow(['Number of Samples', len(self.gpu_logs)])
            writer.writerow([])  # Empty row for separation
            
            # Write summary data
            writer.writerow(['Device', 'Avg GPU Util (%)', 'Max GPU Util (%)', 
                            'Avg Memory Util (%)', 'Max Memory Util (%)', 
                            'Max Memory Used (MB)', 'Total Memory (MB)'])
            
            for device_id, metrics in summary.items():
                writer.writerow([
                    device_id,
                    f"{metrics['avg_gpu_util']:.2f}",
                    f"{metrics['max_gpu_util']:.2f}",
                    f"{metrics['avg_mem_util']:.2f}",
                    f"{metrics['max_mem_util']:.2f}",
                    f"{metrics['max_mem_used']:.2f}",
                    f"{metrics['mem_total']:.2f}"
                ])
        
        print(f"GPU summary saved to {csv_path}")
        return csv_path
