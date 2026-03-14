# Lesson 11 Area of Triangle

# 第十一讲 三角形面积（二）

# 相似模型

1.  ![](media/image4.png){width="1.3708333333333333in"
    height="2.375in"}三角形ADE与三角形ABC构成相似模型：

    对应角相等，对应边成比例，对应边上的高成比例：

    $$\frac{AD}{AB} = \frac{AE}{AC} = \frac{DE}{BC} = \frac{AG}{AF}$$

    三角形面积比等于对应线段的平方比：

    $$\frac{S_{\bigtriangleup ADE}}{S_{\bigtriangleup ABC}} = \frac{{AD}^{2}}{{AB}^{2}} = \frac{{AE}^{2}}{{AC}^{2}} = \frac{{DE}^{2}}{{BC}^{2}} = \frac{{AG}^{2}}{{AF}^{2}}$$

# ![](media/image5.png){width="1.4861111111111112in" height="1.0465277777777777in"}蝴蝶模型

1.  任意四边形中的"蝶形"

<!-- -->

1.  $S_{1}:S_{2} = S_{4}:S_{3}$或$S_{1} \times S_{3} = S_{2} \times S_{4}$

2.  AO:OC=($S_{1} + S_{2}$):($S_{3} + S_{4}$)

<!-- -->

2.  ![](media/image6.png){width="1.5416666666666667in"
    height="1.1625in"}梯形中的"蝶形"

<!-- -->

1.  $S_{1}:S_{3} = a^{2}:b^{2}$

2.  $S_{1}:S_{3}:S_{3}:S_{4} = a^{2}:b^{2}:ab:ab$

3.  梯形ABCD面积对应的份数是${(a + b)}^{2}$份

# ![](media/image7.png){width="1.2659722222222223in" height="1.0402777777777779in"}燕尾模型

1.  $S_{\bigtriangleup ABO}:S_{\bigtriangleup ACO} = S_{\bigtriangleup BOD}:S_{\bigtriangleup COD} = BD:CD$

2.  $S_{\bigtriangleup ABO}:S_{\bigtriangleup BCO} = S_{\bigtriangleup AOE}:S_{\bigtriangleup COE} = AE:CE$

3.  $S_{\bigtriangleup BCO}:S_{\bigtriangleup ACO} = S_{\bigtriangleup BOF}:S_{\bigtriangleup AOF} = BF:AF$

## 例题

**例题1**：在△ABC中，D、E分别在AB、AC上，且AD:DB = 1:2，AE:EC = 1:3，DE = 4，求BC的长度。

**解**：根据相似模型：
$\frac{DE}{BC} = \frac{AD}{AB} = \frac{1}{1+2} = \frac{1}{3}$
所以$BC = 3 \times DE = 3 \times 4 = 12$

**例题2**：在△ABC中，D、E分别在AB、AC上，且AD:DB = 1:1，AE:EC = 2:1，已知$S_{\triangle ABC} = 36$，求$S_{\triangle ADE}$。

**解**：根据相似模型：
$\frac{S_{\triangle ADE}}{S_{\triangle ABC}} = \frac{AD^2}{AB^2} = (\frac{1}{2})^2 = \frac{1}{4}$
所以$S_{\triangle ADE} = \frac{1}{4} \times 36 = 9$

**例题3**：在梯形ABCD中，AD∥BC，对角线AC、BD交于点O，已知$S_{\triangle AOD} = 4$，$S_{\triangle BOC} = 9$，求$S_{\triangle AOB} \times S_{\triangle COD}$。

**解**：根据蝴蝶模型：
$S_{\triangle AOB} \times S_{\triangle COD} = S_{\triangle AOD} \times S_{\triangle BOC} = 4 \times 9 = 36$

**例题4**：在梯形ABCD中，AD∥BC，AD = 3，BC = 5，对角线AC、BD交于点O，已知$S_{\triangle AOD} = 9$，求$S_{\triangle BOC}$。

**解**：根据梯形蝴蝶模型：
$\frac{S_{\triangle AOD}}{S_{\triangle BOC}} = \frac{AD^2}{BC^2} = \frac{3^2}{5^2} = \frac{9}{25}$
所以$S_{\triangle BOC} = \frac{25}{9} \times 9 = 25$

**例题5**：在△ABC中，D、E、F分别在BC、CA、AB上，且BD:DC = 2:1，CE:EA = 3:2，AF:FB = 1:1，AD、BE、CF交于点O，已知$S_{\triangle ABC} = 60$，求$S_{\triangle AOB}$。

**解**：根据燕尾模型，设$S_{\triangle AOB} = x$，$S_{\triangle BOC} = y$，$S_{\triangle COA} = z$
由BD:DC = 2:1，得：$\frac{x + z}{y} = \frac{2}{1}$，即$x + z = 2y$
由CE:EA = 3:2，得：$\frac{y + x}{z} = \frac{3}{2}$，即$2(y + x) = 3z$
由AF:FB = 1:1，得：$\frac{z + y}{x} = \frac{1}{1}$，即$z + y = x$
解方程组得：$x = 15$，$y = 10$，$z = 5$
所以$S_{\triangle AOB} = 15$

**例题6**：在梯形ABCD中，AD∥BC，AD = 2，BC = 6，对角线AC、BD交于点O，已知$S_{\triangle AOD} = 4$，求梯形ABCD的面积。

**解**：根据梯形蝴蝶模型，设$S_{\triangle AOB} = S_1$，$S_{\triangle COD} = S_2$
$\frac{S_{\triangle AOD}}{S_{\triangle BOC}} = \frac{AD^2}{BC^2} = \frac{4}{36} = \frac{1}{9}$
所以$S_{\triangle BOC} = 9 \times 4 = 36$
又$S_1 \times S_2 = 4 \times 36 = 144$
且$\frac{S_1}{S_2} = \frac{AD}{BC} = \frac{2}{6} = \frac{1}{3}$
所以$S_1 = 6$，$S_2 = 18$
梯形面积 = $4 + 6 + 36 + 18 = 64$
