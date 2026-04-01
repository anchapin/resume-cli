## 2024-03-22 - [JobParser] Add SSRF protection

**Vulnerability:**
The `JobParser.parse_from_url` method passed arbitrary user-provided URLs directly to `requests.get` without any validation. This exposed the application to Server-Side Request Forgery (SSRF) attacks, where an attacker could coerce the server into making requests to internal network resources (e.g., AWS IMDS at `169.254.169.254`, `localhost`, etc).

**Learning:**
When an application takes a URL from untrusted user input and makes a server-side request using it, it is critical to resolve the hostname and validate the target IP address to ensure it does not belong to private or reserved IP ranges. Additionally, the IP validation should fail securely if resolution errors occur, and `0.0.0.0` needs explicit checks as it may resolve to localhost depending on the environment. Time-of-check to time-of-use (TOCTOU) issues via DNS rebinding can still technically occur if the hostname is passed to requests instead of the verified IP, but validating the IP is a crucial first step.

**Prevention:**
Always validate both the scheme and the resolved IP address (using a tool like Python's `ipaddress` library with `is_private`, `is_loopback`, `is_reserved`, etc.) before making requests to user-supplied URLs. Ensure the failure modes fail closed instead of open.
