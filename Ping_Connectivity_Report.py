import subprocess
import platform
import socket
import time
import json
import re
from datetime import datetime


class ConnectivityTester:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def ping_target(self, target, count=4):
        """Ping a target with cross-platform compatibility."""

        # Determine the correct ping command based on the operating system
        if platform.system().lower() == "windows":
            ping_cmd = ["ping", "-n", str(count), target]
        else:
            ping_cmd = ["ping", "-c", str(count), target]

        try:
            result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=30)
            return result
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Error pinging {target}: {e}")
            return None

    def test_dns_resolution(self, hostname):
        """Test if a hostname can be resolved to an IP address."""
        try:
            ip = socket.gethostbyname(hostname)
            return ip
        except socket.gaierror:
            return None

    def test_port_connectivity(self, host, port, timeout=5):
        """Test if a specific port is open on a host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start_time = time.time()
            result = sock.connect_ex((host, port))
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            sock.close()
            return result == 0, response_time
        except Exception:
            return False, 0

    def extract_ping_stats(self, ping_output):
        """Extract ping statistics from the output."""
        stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'packet_loss': 0,
            'min_time': 0,
            'max_time': 0,
            'avg_time': 0
        }

        try:
            if platform.system().lower() == "windows":
                # Windows ping output parsing
                lines = ping_output.split('\n')
                for line in lines:
                    if 'Packets:' in line:
                        # Parse: Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
                        sent_match = re.search(r'Sent = (\d+)', line)
                        received_match = re.search(r'Received = (\d+)', line)
                        loss_match = re.search(r'\((\d+)% loss\)', line)

                        if sent_match:
                            stats['packets_sent'] = int(sent_match.group(1))
                        if received_match:
                            stats['packets_received'] = int(received_match.group(1))
                        if loss_match:
                            stats['packet_loss'] = int(loss_match.group(1))

                    elif 'time=' in line:
                        # Extract individual ping times
                        time_match = re.search(r'time[<=](\d+)ms', line)
                        if time_match:
                            ping_time = int(time_match.group(1))
                            if stats['min_time'] == 0 or ping_time < stats['min_time']:
                                stats['min_time'] = ping_time
                            if ping_time > stats['max_time']:
                                stats['max_time'] = ping_time

                    elif 'Average' in line:
                        # Parse average time
                        avg_match = re.search(r'Average = (\d+)ms', line)
                        if avg_match:
                            stats['avg_time'] = int(avg_match.group(1))
            else:
                # Unix/Linux ping output parsing
                lines = ping_output.split('\n')
                for line in lines:
                    if 'packets transmitted' in line:
                        parts = line.split(',')
                        stats['packets_sent'] = int(parts[0].split()[0])
                        stats['packets_received'] = int(parts[1].split()[0])
                        if len(parts) > 2:
                            loss_match = re.search(r'(\d+)%', parts[2])
                            if loss_match:
                                stats['packet_loss'] = int(loss_match.group(1))

                    elif 'min/avg/max' in line:
                        times_match = re.search(r'= ([\d.]+)/([\d.]+)/([\d.]+)', line)
                        if times_match:
                            stats['min_time'] = float(times_match.group(1))
                            stats['avg_time'] = float(times_match.group(2))
                            stats['max_time'] = float(times_match.group(3))

        except Exception as e:
            print(f"Error parsing ping stats: {e}")

        return stats

    def test_target(self, target):
        """Comprehensive test of a target."""
        print(f"\n🔍 Testing connectivity to: {target}")
        print("-" * 40)

        result_data = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'dns_resolution': None,
            'ping_success': False,
            'ping_stats': {},
            'port_tests': []
        }

        # Test DNS resolution for hostnames
        if not target.replace(".", "").replace(":", "").isdigit():  # If it's not an IP address
            print(f"DNS Resolution Test:")
            resolved_ip = self.test_dns_resolution(target)
            if resolved_ip:
                print(f"✅ {target} resolves to: {resolved_ip}")
                result_data['dns_resolution'] = {
                    'success': True,
                    'ip_address': resolved_ip
                }
            else:
                print(f"❌ Failed to resolve {target}")
                result_data['dns_resolution'] = {
                    'success': False,
                    'ip_address': None
                }
                self.results.append(result_data)
                return
        else:
            result_data['dns_resolution'] = {
                'success': True,
                'ip_address': target
            }

        # Ping test
        print(f"Ping Test:")
        ping_result = self.ping_target(target)

        if ping_result is None:
            print(f"❌ Ping to {target} timed out or failed")
            result_data['ping_success'] = False
        elif ping_result.returncode == 0:
            print(f"✅ Ping to {target} successful!")
            result_data['ping_success'] = True
            result_data['ping_stats'] = self.extract_ping_stats(ping_result.stdout)

            # Display key stats
            stats = result_data['ping_stats']
            print(
                f"📊 Packets: Sent={stats['packets_sent']}, Received={stats['packets_received']}, Loss={stats['packet_loss']}%")
            print(f"⏱️  Response time: Min={stats['min_time']}ms, Avg={stats['avg_time']}ms, Max={stats['max_time']}ms")
        else:
            print(f"❌ Ping to {target} failed!")
            print(f"Error: {ping_result.stderr.strip()}")
            result_data['ping_success'] = False

        # Test common ports
        print(f"Port Connectivity Test:")
        test_ip = result_data['dns_resolution']['ip_address']
        ports_to_test = [80, 443, 53]  # HTTP, HTTPS, DNS

        for port in ports_to_test:
            is_open, response_time = self.test_port_connectivity(test_ip, port)
            port_data = {
                'port': port,
                'is_open': is_open,
                'response_time': response_time
            }
            result_data['port_tests'].append(port_data)

            if is_open:
                print(f"✅ Port {port} is open ({response_time:.1f}ms)")
            else:
                print(f"❌ Port {port} is closed or filtered")

        self.results.append(result_data)

    def generate_html_report(self, filename="connectivity_report.html"):
        """Generate a beautiful HTML report."""

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Connectivity Report</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
        }}

        .summary-card h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}

        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}

        .content {{
            padding: 30px;
        }}

        .target-section {{
            margin-bottom: 40px;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}

        .target-header {{
            padding: 20px 30px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .target-header.failed {{
            background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);
        }}

        .target-header h2 {{
            font-size: 1.5em;
        }}

        .status-badge {{
            padding: 8px 16px;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.2);
            font-weight: bold;
        }}

        .target-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            padding: 30px;
        }}

        .detail-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        }}

        .detail-card h3 {{
            margin-bottom: 15px;
            color: #333;
            font-size: 1.2em;
        }}

        .metric {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}

        .metric:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            font-weight: 500;
            color: #666;
        }}

        .metric-value {{
            font-weight: bold;
        }}

        .port-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}

        .port-item {{
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            font-weight: bold;
        }}

        .port-open {{
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }}

        .port-closed {{
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }}

        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin-top: 30px;
        }}

        .chart-container h3 {{
            text-align: center;
            margin-bottom: 20px;
            color: #333;
            font-size: 1.3em;
        }}

        @media (max-width: 768px) {{
            .target-details {{
                grid-template-columns: 1fr;
            }}

            .summary {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Network Connectivity Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Targets Tested</h3>
                <div class="value">{len(self.results)}</div>
            </div>
            <div class="summary-card">
                <h3>Successful Pings</h3>
                <div class="value success">{sum(1 for r in self.results if r['ping_success'])}</div>
            </div>
            <div class="summary-card">
                <h3>DNS Resolutions</h3>
                <div class="value success">{sum(1 for r in self.results if r['dns_resolution'] and r['dns_resolution']['success'])}</div>
            </div>
            <div class="summary-card">
                <h3>Open Ports</h3>
                <div class="value warning">{sum(len([p for p in r['port_tests'] if p['is_open']]) for r in self.results)}</div>
            </div>
        </div>

        <div class="content">
"""

        # Add individual target sections
        for result in self.results:
            target = result['target']
            ping_success = result['ping_success']
            dns_success = result['dns_resolution']['success'] if result['dns_resolution'] else False

            header_class = "" if ping_success else "failed"
            status_text = "✅ ONLINE" if ping_success else "❌ OFFLINE"

            html_template += f"""
            <div class="target-section">
                <div class="target-header {header_class}">
                    <h2>{target}</h2>
                    <span class="status-badge">{status_text}</span>
                </div>

                <div class="target-details">
            """

            # DNS Resolution Card
            if result['dns_resolution']:
                dns_ip = result['dns_resolution']['ip_address']
                html_template += f"""
                    <div class="detail-card">
                        <h3>🔍 DNS Resolution</h3>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value {'success' if dns_success else 'danger'}">
                                {'✅ Success' if dns_success else '❌ Failed'}
                            </span>
                        </div>
                        {f'<div class="metric"><span class="metric-label">IP Address:</span><span class="metric-value">{dns_ip}</span></div>' if dns_ip else ''}
                    </div>
                """

            # Ping Statistics Card
            if ping_success and result['ping_stats']:
                stats = result['ping_stats']
                html_template += f"""
                    <div class="detail-card">
                        <h3>📡 Ping Statistics</h3>
                        <div class="metric">
                            <span class="metric-label">Packets Sent:</span>
                            <span class="metric-value">{stats['packets_sent']}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Packets Received:</span>
                            <span class="metric-value">{stats['packets_received']}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Packet Loss:</span>
                            <span class="metric-value {'danger' if stats['packet_loss'] > 0 else 'success'}">{stats['packet_loss']}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Response:</span>
                            <span class="metric-value">{stats['avg_time']}ms</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Min/Max Response:</span>
                            <span class="metric-value">{stats['min_time']}ms / {stats['max_time']}ms</span>
                        </div>
                    </div>
                """

            # Port Connectivity Card
            if result['port_tests']:
                html_template += f"""
                    <div class="detail-card">
                        <h3>🚪 Port Connectivity</h3>
                        <div class="port-grid">
                """

                for port_test in result['port_tests']:
                    port = port_test['port']
                    is_open = port_test['is_open']
                    response_time = port_test['response_time']
                    port_class = "port-open" if is_open else "port-closed"
                    port_status = f"✅ {port}" if is_open else f"❌ {port}"
                    time_display = f"<br><small>{response_time:.1f}ms</small>" if is_open else ""

                    html_template += f"""
                        <div class="port-item {port_class}">
                            {port_status}{time_display}
                        </div>
                    """

                html_template += """
                        </div>
                    </div>
                """

            html_template += """
                </div>
            </div>
            """

        # Add charts
        if self.results:
            html_template += """
            <div class="chart-container">
                <h3>📊 Response Time Analysis</h3>
                <canvas id="responseTimeChart" width="400" height="200"></canvas>
            </div>

            <div class="chart-container">
                <h3>🎯 Success Rate Overview</h3>
                <canvas id="successRateChart" width="400" height="200"></canvas>
            </div>
            """

        # Close content and container
        html_template += """
        </div>
    </div>

    <script>
        // Response Time Chart
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        const responseTimeChart = new Chart(responseTimeCtx, {
            type: 'bar',
            data: {"""

        # Prepare chart data
        labels = []
        avg_times = []
        colors = []

        for result in self.results:
            labels.append(result['target'])
            if result['ping_success'] and result['ping_stats']:
                avg_times.append(result['ping_stats']['avg_time'])
                colors.append('rgba(40, 167, 69, 0.8)')
            else:
                avg_times.append(0)
                colors.append('rgba(220, 53, 69, 0.8)')

        html_template += f"""
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Average Response Time (ms)',
                    data: {json.dumps(avg_times)},
                    backgroundColor: {json.dumps(colors)},
                    borderColor: {json.dumps(colors)},
                    borderWidth: 2,
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Response Time (ms)'
                        }}
                    }}
                }}
            }}
        }});

        // Success Rate Chart
        const successRateCtx = document.getElementById('successRateChart').getContext('2d');
        const successCount = {sum(1 for r in self.results if r['ping_success'])};
        const failureCount = {len(self.results) - sum(1 for r in self.results if r['ping_success'])};

        const successRateChart = new Chart(successRateCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Successful', 'Failed'],
                datasets: [{{
                    data: [successCount, failureCount],
                    backgroundColor: ['rgba(40, 167, 69, 0.8)', 'rgba(220, 53, 69, 0.8)'],
                    borderColor: ['rgba(40, 167, 69, 1)', 'rgba(220, 53, 69, 1)'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            font: {{
                                size: 14
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

        # Write the HTML file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"\n✅ HTML report generated: {filename}")
        return filename

    def run_tests(self, targets):
        """Run all connectivity tests."""
        print("=" * 60)
        print("PING & CONNECTIVITY TESTER")
        print("=" * 60)

        for target in targets:
            self.test_target(target)

        # Generate HTML report
        report_file = self.generate_html_report()

        print("\n" + "=" * 60)
        print("TESTING COMPLETE!")
        print("=" * 60)
        print(f"📊 Targets tested: {len(self.results)}")
        print(f"✅ Successful pings: {sum(1 for r in self.results if r['ping_success'])}")
        print(f"📄 HTML report: {report_file}")

        return report_file


def main():
    targets = ["8.8.8.8", "1.1.1.1", "www.google.com", "www.github.com", "www.amazon.com"]

    tester = ConnectivityTester()
    tester.run_tests(targets)


if __name__ == "__main__":
    main()