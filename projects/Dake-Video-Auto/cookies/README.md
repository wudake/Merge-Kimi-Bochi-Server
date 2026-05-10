# 抖音 Cookie 配置说明

## 配置方法

### 方法1：使用浏览器扩展导出（推荐）

1. **安装 Cookie 导出扩展**
   - Chrome: 安装 "Get cookies.txt LOCALLY" 扩展
   - Edge: 安装 "Cookie-Editor" 扩展

2. **登录抖音**
   - 在浏览器中打开 https://www.douyin.com
   - 登录你的抖音账号
   - 播放任意一个视频

3. **导出 Cookie**
   - 点击扩展图标
   - 选择 "导出" / "Export"
   - 格式选择 Netscape / cookies.txt
   - 保存到项目目录: `cookies/douyin_cookies.txt`

### 方法2：使用 curl 测试 Cookie

导出 Cookie 后，可以先测试是否有效：

```bash
yt-dlp --cookies cookies/douyin_cookies.txt --list-formats "https://www.douyin.com/video/VIDEO_ID"
```

如果显示格式列表，说明 Cookie 有效。

## Cookie 文件格式

Cookie 文件应该是 Netscape 格式：

```
# Netscape HTTP Cookie File
.douyin.com	TRUE	/	FALSE	1750000000	passport_csrf_token	XXX
.douyin.com	TRUE	/	FALSE	1750000000	ttwid	XXX
.douyin.com	TRUE	/	FALSE	1750000000	sessionid	XXX
...
```

## 注意事项

1. **Cookie 会过期** - 通常 1-3 个月后需要重新导出
2. **不要分享 Cookie** - 包含登录信息，泄露会导致账号被盗
3. **定期更新** - 如果下载失败提示 Cookie 错误，需要重新导出

## 多用户模式

如果使用多用户模式，每个用户需要单独配置：
- 单用户: `cookies/douyin_cookies.txt`
- 用户A: `users/{user_id}/cookies/douyin_cookies.txt`
