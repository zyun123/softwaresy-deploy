第三方库版本说明：

    ubuntu 20.04.2
    opencv 4.5.5
    cuda 11.3.1
    cudnn 8.2.1
    libtorch 1.11.0
    torchvision 0.12.0
    qt 5.12.12

---

## 部署流程

1. 执行`preconfig.sh`脚本以自动完成下列设置
    - 设置共享内存权限
    - 添加桌面图标
    - 根据显卡型号选择libtorchvision.so版本

2. 配置机械盘挂载位置(如/opt/data),存储软件运行数据，软连接到上位机软件根目录`saveimgs`

        ln -s /opt/data/saveimgs saveimgs
