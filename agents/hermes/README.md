# Hermes Agent
**Role:** Task Automation & Communication  
**Part of:** MrNothing OS

## Capabilities
- Termux notifications
- Scheduled notification tasks
- Interactive legacy command tasks with explicit owner confirmation
- Background scheduler that never executes shell tasks unattended

## Shell-task safety
- Shell tasks are blocked unless the interactive UI obtains an explicit confirmation bound to the exact command text.
- Commands are parsed with \`shlex\` and launched as an argument vector with \`shell=False\`.
- Shell interpreters are rejected and direct commands have a 30-second timeout.
- The confirmation is a local interaction, not strong owner authentication or a sandbox. Approved executables still run with this process's OS privileges.
- Do not use this legacy helper for root, device-control, destructive, remote, or production operations. It is not connected to the native Android command router.

## Usage
```
python3 agent.py           # Interactive mode
python3 agent.py --daemon  # Notification scheduling; shell tasks remain approval-blocked
```
