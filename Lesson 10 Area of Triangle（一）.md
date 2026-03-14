# Lesson 10 Area of Triangle

# 第十讲 三角形面积（一）

# 面积公式

1.  平行四边形面积=底$\times$高

2.  三角形面积=底$\times$高$\div$`<!-- -->`{=html}2

# 一半模型

1.  平行四边形中的一半模型，图中各点均是任意点，阴影部分是平行四边形面积的一半。

    ![](media/image4.png){width="5.131944444444445in"
    height="1.9583333333333333in"}

<!-- -->

(1) 梯形和任意四边形中的一半模型，图中各点均为四边形各边中点（图3取中位线上任意一点），阴影部分的面积均为四边形面积的一半。

    ![](media/image5.png){width="4.824305555555555in"
    height="1.9770833333333333in"}

# 等积变形

1.  等底等高的两个三角形面积相等。

2.  两个三角形高相等，面积比等于它们的底之比。两个三角形底相等，面积比等于它们的高之比。

    ![](media/image6.png){width="1.2291666666666667in"
    height="1.1875in"}

3.  夹在一组平行线之间的等积变形，如图$S_{\bigtriangleup ACD} = S_{\bigtriangleup BCD}$。反之，如果$S_{\bigtriangleup ACD} = S_{\bigtriangleup BCD}$，则直线AB∥CD。

# 鸟头模型

1.  两个三角形中有一个角相等或互补，这两个三角形叫做共角三角形。

2.  共角三角形的面积比等于对应角（相等角或互补角）两夹边的乘积之比。

3.  在△ABC中，D、E分别是AB、AC上的点，则$S_{\bigtriangleup ADE}:S_{\bigtriangleup ABC} = (AD \times AE):(AB \times AC)$

    ![](media/image7.png){width="2.765277777777778in"
    height="1.6083333333333334in"}

## 例题

**例题1**：一个三角形的底是12厘米，高是8厘米，求面积。

**解**：面积 = $\frac{1}{2} \times 底 \times 高 = \frac{1}{2} \times 12 \times 8 = 48$ 平方厘米

**例题2**：一个平行四边形的底是10厘米，高是6厘米，求面积。

**解**：面积 = 底 × 高 = 10 × 6 = 60 平方厘米

**例题3**：在平行四边形ABCD中，E是BC上任意一点，连接AE、DE，求证：$S_{\triangle ABE} + S_{\triangle CDE} = \frac{1}{2}S_{ABCD}$。

**解**：设平行四边形的高为h，底为BC = AD = b
$S_{\triangle ABE} = \frac{1}{2} \times BE \times h$
$S_{\triangle CDE} = \frac{1}{2} \times CE \times h$
$S_{\triangle ABE} + S_{\triangle CDE} = \frac{1}{2} \times (BE + CE) \times h = \frac{1}{2} \times b \times h = \frac{1}{2}S_{ABCD}$

**例题4**：在△ABC中，D是BC的中点，E是AC的中点，连接AD、BE，求$S_{\triangle ABE}:S_{\triangle ABC}$。

**解**：因为E是AC的中点，所以AE = $\frac{1}{2}$AC
$S_{\triangle ABE}:S_{\triangle ABC} = AE:AC = 1:2$

**例题5**：在△ABC中，D是AB上一点，且AD:DB = 2:3，E是AC上一点，且AE:EC = 1:2，求$S_{\triangle ADE}:S_{\triangle ABC}$。

**解**：根据鸟头模型：
$S_{\triangle ADE}:S_{\triangle ABC} = (AD \times AE):(AB \times AC)$
$= (2 \times 1):(5 \times 3) = 2:15$

**例题6**：在△ABC中，D、E分别是AB、AC的中点，F是BC的中点，连接DE、EF、FD，求$S_{\triangle DEF}:S_{\triangle ABC}$。

**解**：因为D、E分别是AB、AC的中点，所以DE∥BC，且DE = $\frac{1}{2}$BC
根据相似模型，$S_{\triangle ADE}:S_{\triangle ABC} = (\frac{1}{2})^2 = 1:4$
同理，$S_{\triangle BDF}:S_{\triangle ABC} = 1:4$，$S_{\triangle CEF}:S_{\triangle ABC} = 1:4$
所以$S_{\triangle DEF} = S_{\triangle ABC} - 3 \times \frac{1}{4}S_{\triangle ABC} = \frac{1}{4}S_{\triangle ABC}$
因此$S_{\triangle DEF}:S_{\triangle ABC} = 1:4$

**例题7**：在△ABC中，D是BC上一点，BD:DC = 2:3，E是AC上一点，AE:EC = 1:1，连接AD、BE交于点O，已知$S_{\triangle ABC} = 50$，求$S_{\triangle AOB}$。

**解**：设$S_{\triangle ABC} = 50$
因为BD:DC = 2:3，所以$S_{\triangle ABD}:S_{\triangle ABC} = 2:5$
$S_{\triangle ABD} = \frac{2}{5} \times 50 = 20$
因为AE:EC = 1:1，所以E是AC的中点
在△ABD中，$S_{\triangle AOB}:S_{\triangle ABD} = 1:2$（等积变形）
所以$S_{\triangle AOB} = \frac{1}{2} \times 20 = 10$
