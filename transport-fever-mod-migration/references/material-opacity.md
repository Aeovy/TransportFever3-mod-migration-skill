# 透明度与材质分类

当迁移后的车壳、车身或其他本应实体的表面像毛玻璃，能透过模型看到另一侧场景，或玻璃/车窗透明效果异常时读取本参考。材质类型、alpha、map/sampler 和深度/排序设置必须作为一组检查；只调 `sorted` 或只替换材质类型通常不足以定位问题。

## 诊断顺序

1. 从模型和各 LOD 的 mesh 材质引用出发，确定出问题的确切 `.mtl`。按视角和涂装缩小范围，避免修改整套模组中所有名字相似的材质。
2. 对照 TF2 原材质与 TF3 转换结果，记录 `type`、`map_albedo` 或 `map_albedo_opacity`、sampler 名称、`alpha_test` 属性、`sorted`、深度/法线写入开关，以及法线/MGA 引用。
3. 检查材质实际引用的纹理 alpha。除了整张纹理 alpha 范围，也要结合 UV 岛和对应 atlas 区域判断 alpha 的用途；整图同时包含实体和窗口时，全图 min/max 不能说明当前面片属于哪一类。
4. 将材质按实际表面分成实体壳体、独立透明玻璃、实体与透明区共用 atlas 三类。文件名只能提供线索，不能代替模型引用和 UV 检查。
5. 先在副本中修正最小范围，静态检查材质字段和纹理引用，再打包并在用户实际报告问题的平台复测。记录具体模组版本、材质范围与结果；编辑器预览不能代替游戏内排序和遮挡验证。

## 材质转换规则

| 表面用途 | 常见设置 | 需要确认 |
| --- | --- | --- |
| 完全不透明表面 | `PHYSICAL`，或带法线贴图的 `PHYSICAL_NRML_MAP`；`map_albedo` + `albedoTex` | 确认该网格面确实不需要 alpha 挖空；保留仍使用的法线、MGA、双面和灯光参数 |
| 真正透明玻璃 | `PHYS_TRANSPARENT`，或带法线贴图的透明变体；`map_albedo_opacity` + `albedoOpacityTex` | alpha、透明排序及深度/法线写入行为应按目标版本材质定义和实际玻璃效果设置 |
| 实体与玻璃共用 atlas | 依 UV 和 shader 的 alpha/cutout 语义决定 | 优先在源工程拆分实体和玻璃材质；强制不透明可能封住玻璃，cutout 会把连续半透明变成覆盖式透明 |

如果把 `PHYS_TRANSPARENT*` 改成 `PHYSICAL*`，要同时迁移 albedo 参数表和 sampler 键：`map_albedo_opacity` -> `map_albedo`，`albedoOpacityTex` -> `albedoTex`。只改 `type` 会留下不匹配的纹理绑定。保留 shader 仍需的 `map_normal`、`map_metal_gloss_ao` 等引用；不要把“修透明”扩大成对光照、法线、双面或 alpha 纹理的无关更改。

`sorted` 是透明绘制排序设置，不是实体/透明开关。把所有材质统一设为 `sorted=true` 可能让大面积壳体进入透明排序路径；反过来，对真实玻璃盲目关闭排序也可能产生前后遮挡错误。`cutout` 适合阈值式覆盖，不等价于连续半透明玻璃。

## 已验证案例：CR200J Windows 游戏中的车体毛玻璃

初版迁移在 Windows 中基本可用，但车体像毛玻璃，能看到车体另一侧场景。材质检查发现不少实体部件沿用 `PHYS_TRANSPARENT*`；其中一部分 atlas 有 alpha 125-255，独立玻璃约为半透明 alpha。仅依据这些静态数据无法判断哪一个 shader 设置是 Windows 症状的唯一原因。

第一次修正将大部分纯实体材质改为实体 shader，混合 atlas 使用 cutout，并保留独立玻璃透明。用户后续截图仍观察到少量透视。最终修正把 6 个车体主体 atlas 材质改成 `PHYSICAL` / `PHYSICAL_NRML_MAP`，并同步改为 `map_albedo` + `albedoTex`；保留独立玻璃透明，以及其他混合部件的 cutout。纹理、UV 和模型均未改动。用户在 Windows 游戏中确认这一版本彻底解决了所报告的车体透明问题。

该实测只证明这 6 个 CR200J 材质及其对应模型/UV 组合有效。别把 `_body_` 文件名、alpha 范围或 shader 替换当作其他模组的自动规则；有的模型确实通过同一 atlas 的 alpha 绘制玻璃。遇到新模组时，先定位网格引用与 UV，再选 shader，并在目标游戏中检查玻璃是否仍正确。

## 官方依据

- [Transport Fever 3 材质资源类型](https://wiki.transportfever3.com/doku.php?id=modding:general:resourcetypes:mtl)
- 项目实例历史：`cr200j-case-study.md`
