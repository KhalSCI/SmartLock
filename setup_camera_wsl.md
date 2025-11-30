# WSL2 USB Camera Passthrough Setup Guide

Follow these steps to enable your USB camera in WSL2:

## Step 1: Install usbipd-win on Windows

1. Open PowerShell as Administrator (on Windows side)
2. Install usbipd-win using winget:
   ```powershell
   winget install --interactive --exact dorssel.usbipd-win
   ```
   
   Or download from: https://github.com/dorssel/usbipd-win/releases

3. Restart your computer after installation

## Step 2: Install USB/IP tools in WSL2

Run these commands in your WSL terminal:

```bash
sudo apt-get update
sudo apt-get install -y linux-tools-generic hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*-generic/usbip 20
```

## Step 3: Connect Your Camera

1. **On Windows (PowerShell as Administrator):**
   
   List all USB devices:
   ```powershell
   usbipd list
   ```
   
   You'll see output like:
   ```
   BUSID  VID:PID    DEVICE                                                        STATE
   1-4    046d:0825  Logitech Webcam C270, USB Input Device                       Not shared
   ```
   
   Note your camera's BUSID (e.g., 1-4)

2. **Share the camera (one-time setup):**
   ```powershell
   usbipd bind --busid 1-4
   ```
   (Replace 1-4 with your actual BUSID)

3. **Attach the camera to WSL:**
   ```powershell
   usbipd attach --wsl --busid 1-4
   ```
   (Replace 1-4 with your actual BUSID)

## Step 4: Verify Camera Access in WSL

In your WSL terminal, check if the camera is detected:

```bash
ls -la /dev/video*
```

You should see `/dev/video0` or similar.

## Step 5: Set Permissions

```bash
sudo usermod -a -G video $USER
sudo chmod 666 /dev/video0
```

## Step 6: Run Your SmartLock Application

```bash
cd ~/SmartLock
source venv/bin/activate
python enroll.py
```

---

## Quick Reference - Daily Use

Every time you restart your computer or WSL, you need to re-attach the camera:

**On Windows PowerShell (as Administrator):**
```powershell
usbipd attach --wsl --busid 1-4
```

**To detach when done:**
```powershell
usbipd detach --busid 1-4
```

**Check camera status in WSL:**
```bash
ls /dev/video*
```

---

## Troubleshooting

### Camera not showing in WSL
- Make sure WSL is running when you attach
- Try detaching and reattaching
- Restart WSL: `wsl --shutdown` then reopen

### Permission denied error
```bash
sudo chmod 666 /dev/video0
```

### usbipd command not found (Windows)
- Restart PowerShell after installation
- Restart your computer

### Camera already in use
- Close any Windows apps using the camera
- Detach from WSL and try again

---

## Alternative: Use Windows Native Python (Easier)

If USB passthrough is too complex, you can run the Python scripts directly on Windows:

1. Install Python on Windows from python.org
2. Copy your SmartLock folder to Windows (e.g., C:\Users\YourName\SmartLock)
3. Install dependencies in Windows Command Prompt:
   ```cmd
   pip install opencv-python face-recognition flask numpy
   ```
4. Run normally:
   ```cmd
   python enroll.py
   python main.py
   ```
