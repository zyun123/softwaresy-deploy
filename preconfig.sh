#!/bin/bash

PROGRAM_PATH=/home/sy/sy-3-software-test-ci/sy-3-deploy

echo "正在设置共享内存文件权限..."
chmod 666 ./camprocess/tmp*
echo "设置完成"

echo "正在设置相机进程文件权限..."
chmod u+x ./camprocess/cam_process-*
echo "设置完成"

echo "正在生成桌面图标..."
echo "cd $PROGRAM_PATH; ./start.sh" > ~/desktop.sh
chmod u+x ~/desktop.sh
text="[Desktop Entry]
Name=qtDemo
Comment=qtDemo
Exec=/home/sy/desktop.sh
Icon=/home/sy/sy-3-deploy/sy-3.png
Terminal=false
Type=Application
Categories=Development;"
echo -e "$text" | sudo tee /usr/share/applications/qtDemo.desktop
chmod u+x /usr/share/applications/qtDemo.desktop
cp /usr/share/applications/qtDemo.desktop ~/Desktop/
echo "设置完成"

# 获取显卡型号
gpu=$(lspci | grep -i "vga")

# 判断显卡型号是否为"2080"
if echo "$gpu" | grep -q "2080"; then
    mv ./libs/ai_libs/libtorchvision.so ./libs/ai_libs/libtorchvision-bak.so
    cp ./libs/ai_libs/libtorchvision-2080.so ./libs/ai_libs/libtorchvision.so
fi

echo "正在设置软件开机自启动..."
mkdir ~/.config/autostart
ln -s ~/Desktop/qtDemo.desktop ~/.config/autostart/
echo "设置完成"

echo "正在设置关机机械臂复位脚本..."
sudo mkdir /opt/sy3

SERVICE_FILE="/etc/systemd/system/killsy3.service"
KILL_SCRIPT="/opt/sy3/killsy3.sh"

# 创建服务文件
echo "[Unit]
Description=kill sy3 software
DefaultDependencies=no
Before=shutdown.target

[Service]
Type=oneshot
ExecStart=$KILL_SCRIPT
TimeoutStartSec=0

[Install]
WantedBy=shutdown.target" | sudo tee $SERVICE_FILE

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable killsy3.service

echo "#!/bin/bash
APPNAME=sy3-dev
kill \$(ps -ef |grep \$APPNAME|grep -v grep|awk '{print \$2}')" | sudo tee $KILL_SCRIPT

sudo chmod 777 $KILL_SCRIPT

echo "##################################"
echo "请继续手动设置电脑IP 192.168.1.100"
echo "请继续手动设置硬盘挂载 使用disks将数据盘挂载到/home/sy/saveimgs, ln -s /home/sy/saveimsgs ."
echo "##################################"
