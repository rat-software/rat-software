Here is a quick and concise summary of the optimal setup (running Ollama natively on Windows while making requests from WSL) in English:

### 1. Windows: Configure Ollama
* **Install Ollama** directly on Windows (not in WSL).
* **Set Environment Variable:** 
  Press the Windows key, search for "Environment Variables", and add a new user variable:
  * Name: `OLLAMA_HOST`
  * Value: `0.0.0.0`
  *(This allows Ollama to accept connections from outside, including WSL).*
* **Restart Ollama** (Quit from the system tray and start it again).
* **Pull the model** via Windows PowerShell: 
  `ollama pull qwen3.5:9b` (or whatever model you need).

### 2. Windows: Open the Firewall
Open **PowerShell as Administrator** and run this command to allow WSL to access Ollama's port:
```powershell
New-NetFirewallRule -DisplayName "Ollama WSL" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
```

### 3. Windows: Get your IP Address
In PowerShell, type `ipconfig`.
Look for your active Network Adapter (e.g., Ethernet or WLAN) and copy the **IPv4 Address** (e.g., `10.171.26.111`).

### 4. WSL: Update your Script/Tool
In your WSL Ubuntu terminal, open your Python script or your backend configuration (like the `rat-backend` UI) and replace `localhost` or `127.0.0.1` with the Windows IP address you just found:

* **API Base URL:** `http://10.171.26.111:11434/v1`
* **API Key:** `ollama` (or anything, just don't leave it blank if required)

### 5. WSL: Update your Script/Tool
Use ollama serve in the console to monitor the process.

**Done!** Now your WSL tools will bypass the virtual network limitations and send requests directly to the Windows Ollama server, utilizing 100% of your RTX 5090 GPU with no slowdowns.