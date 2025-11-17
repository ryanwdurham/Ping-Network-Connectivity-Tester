Ping & Network Connectivity Tester
==================================

Overview
--------
This Python tool performs automated network connectivity diagnostics for any
set of targets (IP addresses or hostnames). It includes:

- DNS resolution testing
- Cross-platform ping testing (Windows, Linux, macOS)
- Port connectivity checks (80, 443, 53 by default)
- Detailed statistics extraction from ping results
- Beautiful HTML report generation (with charts)
- Summary metrics for all tested targets

The tool is designed for network engineers, IT professionals, QA testers,
and anyone who needs fast insight into network reachability and performance.


Features
--------
✔ Cross-platform ping implementation  
✔ DNS resolution with fallback handling  
✔ Port testing for HTTP, HTTPS, DNS  
✔ Extracts packet loss, min/max/avg ping times  
✔ Generates a full interactive HTML report  
✔ Uses Chart.js for graphs (no installation required)  
✔ Clean console output for quick checks  


Watch a video of it in action:  https://www.loom.com/share/9bac45d6d0074890bee0bc6e4e01709b

View a html connectivity report here:  https://ryanwdurham.github.io/Ping-Network-Connectivity-Tester/connectivity_report.html


Requirements
------------
This script uses standard Python libraries with no external dependencies
except for Chart.js (loaded via CDN in the HTML report).

Python 3.8+ recommended.

Built-in modules used:
- subprocess
- socket
- time
- datetime
- json
- re
- platform


How to Use
-----------
1. Install Python 3 if not already installed.

2. Place the script file in a directory, for example:
       connectivity_tester.py

3. Run the script:
       python connectivity_tester.py

4. The tool will:
   - Run DNS + ping + port tests
   - Print results to the console
   - Generate a full HTML report named:
       connectivity_report.html

5. Open the report in any browser to view charts and status dashboards.


Default Targets
---------------
The script currently tests the following by default:

- 8.8.8.8       (Google DNS)
- 1.1.1.1       (Cloudflare DNS)
- www.google.com
- www.github.com
- www.amazon.com

You can edit the `targets` list in `main()` to add more.


HTML Report Output
------------------
The generated HTML report includes:

- Total targets tested
- Successful pings
- DNS success count
- Count of open ports
- Detailed section for each target:
    • DNS resolution result  
    • Packet loss, min/avg/max ping times  
    • Port open/closed status  
- Charts:
    • Bar chart of average response times  
    • Doughnut chart of success vs. failure  


Customization
-------------
You can easily:
- Add more ports in the `ports_to_test` list
- Add more targets in the `targets` list
- Modify HTML styling in `generate_html_report()`

