# GFWList2surge

fork from clowwindy's gfwlist2pac

usage:


```
python main.py -i gfwlist.txt -f surge.conf -p "SOCKS5 192.168.1.17:1080;" --user-rule myrule --surge-proxy-name "proxy1" "proxy2" --surge-proxy "custom, 1.2.3.4, 443, rc4-md5, password" "custom, 1.2.3.4, 443, rc4-md5, password" --apple-dns apple-cdn-speed.report
```


ref

* [https://github.com/gongjianhui/AppleDNS](https://github.com/gongjianhui/AppleDNS)
