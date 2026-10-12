# 模组管理页面的封面迁移

最后核对：2026-10-06；官方 Mod Definition 文档及本机三代内置模组。

TF3 的网格卡片使用模组根目录下的 `_metadata/0.png`；详情页可使用 `1.png`、`2.png` 等编号图片。官方建议尺寸为 1920×1080。二代的根目录 `image_00.tga`、`image_00.jpg` 和 `workshop_preview.jpg` 不会自动替代这项三代展示资源。即使模型、购买图标和 `_metadata/modinfo.json` 全部有效，卡片仍可能显示问号。

## 修复与迁移

1. 在原包中查找 `image_00.*`，缺少时查看 `workshop_preview.*`；检查实际图片内容，合并包应选用能代表最终内容的原图。保留作者文字与标识，不用生成图代替已有封面。原包没有图片时可使用已获授权的实际模型截图；若仍缺少合适来源，在报告中注明。
2. 将图片真正解码并保存为 `_metadata/0.png`，不能仅改扩展名，也不放到 `content/_metadata/`。保持比例，非 16:9 图片用留边，避免裁掉文字或拉伸车体。工具只执行格式/尺寸转换，不创作新画面：

   ```sh
   uv run --with 'pydantic>=2.11,<3' --with 'pillow>=11,<13' python \
     <skill目录>/scripts/migrate_cover.py \
     --source /path/to/original_tf2_mod --mod /path/to/final_tf3_mod \
     --report /path/to/work/cover.json
   ```

   需要指定某张原图时，用 `--image /path/to/existing/image` 替换 `--source`。
3. 重新解码最终 PNG，核对它的尺寸、SHA-256 和 ZIP 成员路径。封面更新时提升成品 `revision`，保持 `modId` 和车辆/脚本资源。`package_mod.py` 默认阻止可见模组遗漏封面；确实无法提供的例外可以用 `--allow-missing-cover`，并在报告中说明。隐藏的辅助模组无需强行增加封面。
4. 在用户允许的范围内，打开实际主游戏的模组网格页面检查卡片和需要的详情页。Model Editor 的车辆购买图标不能证明管理页面封面显示正常。记录截图及版本；未打开主游戏时标为“未运行”。若仍显示旧问号，重新启动游戏并检查 `staging_area` 的同 ID 副本、实际加载位置及图片大小写。不要用删除存档或全量缓存作为首选修复。

已有包只缺封面时，可交付仅含 `modId/_metadata/0.png` 的合并补丁，明确它不是完整模组；不要让用户把补丁空壳文件夹当成可单独启用的模组。同步更新完整 ZIP、CRC/SHA-256 和报告，并核对旧包中除版本字段外的文件没有意外变化。

官方依据：[Mod Definition](https://wiki.transportfever3.com/doku.php?id=modding:general:moddefinition)。
