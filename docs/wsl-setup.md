# WSL2 + Docker Setup for Windows Students

> **Who needs this:** Windows 11 users. If you are on macOS or Linux, skip to the
> "Verify" step at the bottom to confirm Docker is installed.
>
> **What we will do:** Enable WSL2, install Ubuntu, install Docker Desktop with WSL2
> integration. This is a one-time setup — once done, all the docker commands in this
> repo will work the same as on Linux.

---

## Why WSL2?

WSL2 (Windows Subsystem for Linux 2) runs a real Linux kernel inside Windows.
Docker Desktop uses it as its engine — meaning your containers run in actual Linux,
just like they would on a cloud server. This gives you:
- Full Linux command-line compatibility
- Better Docker performance than the old Hyper-V backend
- A proper bash shell for running the commands in this repo

---

## Step 1 — Enable WSL2 (PowerShell, run as Administrator)

Open **PowerShell as Administrator** (right-click the Start button → Terminal (Admin)).

```powershell
wsl --install
```

**Expected output:**
```
Installing: Virtual Machine Platform
Installing: Windows Subsystem for Linux
Installing: Ubuntu
```

This command:
1. Enables the WSL2 feature
2. Installs Ubuntu as the default Linux distribution

**Restart your computer** when prompted.

> **Already have WSL1?** Run `wsl --set-default-version 2` to switch to WSL2,
> then `wsl --update` to get the latest kernel.

---

## Step 2 — Open Ubuntu and create your Linux user

After restarting, search for "Ubuntu" in the Start menu and open it.

On first launch, you will be asked to create a Linux username and password.
These are separate from your Windows credentials — pick something simple.

**Expected output:**
```
Installing, this may take a few minutes...
Please create a default UNIX user account...
Enter new UNIX username: yourname
New password:
```

Once done, you will have a bash prompt:
```
yourname@DESKTOP-XXXX:~$
```

---

## Step 3 — Install Docker Desktop

1. Download Docker Desktop for Windows from the official Docker website.
   Search for "Docker Desktop download" — the first result is `docker.com/products/docker-desktop`.

2. Run the installer (`.exe` file). During installation:
   - Make sure **"Use WSL 2 instead of Hyper-V"** is checked (it usually is by default)
   - Leave other options at defaults

3. After installation, **restart your computer** again if prompted.

4. Open Docker Desktop from the Start menu. Wait for it to fully start
   (the whale icon in the system tray should stop animating).

---

## Step 4 — Enable WSL2 integration in Docker Desktop

Docker Desktop needs to share its engine with your Ubuntu WSL2 instance.

1. Open Docker Desktop → click the gear icon (Settings)
2. Go to **Resources** → **WSL Integration**
3. Toggle on **"Enable integration with my default WSL distro"**
4. If you have multiple distros, also toggle on **Ubuntu**
5. Click **Apply & Restart**

---

## Step 5 — Verify everything works

Open your **Ubuntu terminal** (not PowerShell) and run:

```bash
docker --version
```

**Expected output:**
```
Docker version 25.x.x, build xxxxxxx
```

```bash
docker compose version
```

**Expected output:**
```
Docker Compose version v2.x.x
```

```bash
docker run hello-world
```

**Expected output:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

If all three commands work, you are ready to start the learning modules.

---

## macOS / Linux users — quick verify

**macOS (with Docker Desktop):**
```bash
docker --version
docker compose version
docker run hello-world
```
Same expected output as above.

**Linux (Ubuntu/Debian — Docker Engine directly):**
```bash
# Install Docker Engine if not already installed:
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER   # add yourself to the docker group
newgrp docker                   # apply group change without logging out

docker run hello-world
```

---

## Troubleshooting

**"WSL --install" says WSL is already installed:**
```powershell
wsl --update
wsl --set-default-version 2
```

**Ubuntu does not appear in Docker Desktop WSL integration list:**
Make sure Ubuntu is running (open it from the Start menu), then reopen Docker Desktop settings.

**"docker: command not found" in Ubuntu:**
WSL integration may not be enabled. Check Step 4 above. Also try closing and reopening the Ubuntu terminal after enabling integration.

**Docker Desktop won't start:**
Check that virtualization is enabled in your BIOS (look for "Intel VT-x" or "AMD-V").
Most modern PCs have it enabled by default, but some need it turned on manually.

**"permission denied" running docker commands on Linux:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```
Then try again.

---

## Optional: Native "Docker inside WSL" (advanced)

Instead of Docker Desktop, you can install Docker Engine directly inside WSL2:
```bash
# Inside Ubuntu:
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

This avoids the Docker Desktop GUI but is more complex to maintain. **Docker Desktop
with WSL2 integration is the recommended approach** for beginners.

---

**Next:** Return to the main `README.md` and follow the recommended learning order.
