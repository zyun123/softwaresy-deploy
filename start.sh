#!/bin/bash
export LD_LIBRARY_PATH=./libs/ai_libs:./libs/other:./libs/opencv:./libs/qt:$LD_LIBRARY_PATH
./qtDemo --SaveCureImg=true --BedVer=2 --CamType=kinect --EnableCurrentsProtect=false --EnableLeftSensor=false --EnableRightSensor=false --LinkRealBot=true --EnableTestThread=false --EnableLog=true --EnableOneBtnCare=true --AutoForceThrehold=6,20
