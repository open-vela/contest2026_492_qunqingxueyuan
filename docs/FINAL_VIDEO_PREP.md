# 最终录制准备

录制前先确认正在使用的是已实际验证可运行的 openvela candidate。由于本次 final clean-first 构建未产出完整新镜像，不要在视频或讲解中把该 candidate 描述为“本次 clean build 新固件”。

`tools/start_final_demo.ps1` 仅在它能够找到可启动且已验证的目标固件时使用；若启动器因本次新固件缺失而拒绝启动，不要绕过检查或伪造新固件状态，改用此前已实际验证的 candidate 演示路径。

打开 http://127.0.0.1:8090。WSL Ubuntu-D 目标 Telnet 为 10025，模拟器为 5558/5559，gRPC 为 8558。启动器会检查端口冲突，不会杀死其他模拟器。已经运行本次最终演示时直接使用现有实例。

依照 [FINAL_VIDEO_SCRIPT.md](FINAL_VIDEO_SCRIPT.md) 录制约 3 分钟。终端操作时先暂停网页，避免多个输入源争用同一 C 会话。断线片段可在浏览器开发者工具 Network 选择 Offline，再恢复 No throttling 后点“重新连接”；该操作证明 Browser–bridge 通信失效后的暂停。目标 socket 故障另有自动集成测试证据。

将成片保存为 `submission/final/FlyReflex_演示视频.mp4`，然后执行：

```powershell
python -X utf8 tools/package_submission.py
```

生成 `submission/群青学院-FlyReflex-contest2026_492_qunqingxueyuan.zip`，只包含最终 DOCX、PDF 和视频。代码与 AI Coding logs 通过赛事 Git 仓提交。旧 `FlyReflex_浏览器实录素材.mp4` 不会自动装包。
