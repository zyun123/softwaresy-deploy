cmd="date -s "$(date -I'ns')
cmd1=${cmd: 0:0-6}
sshpass -p easybot ssh root@192.168.1.102 "$cmd1"
sshpass -p easybot ssh root@192.168.1.101 "$cmd1"