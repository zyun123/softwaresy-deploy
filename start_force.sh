#!/bin/bash

# ps -ef|grep 'ft_feed_script'|grep -v grep|awk '{print $2}'|xargs kill -9
ps -ef|grep './python/bin/python'|grep -v grep|awk '{print $2}'|xargs kill -9
sleep 3

cd force
./python/bin/python ft_feed_script.py
