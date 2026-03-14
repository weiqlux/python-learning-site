# Lesson 19 Logic

**第十九讲 逻辑推理**

**一、Statements 命题**

1.  命题：一个命题是要么真要么假，但不可能同时为真和假的句子。

    例如：波士顿是美国的一个城市。

2.  Negation 命题的否定：

    真命题的否定为假，假命题的否定为真。

    例如：月亮不是星星。

3.  Converse,Inverse and Contrapositive 逆命题，否命题和逆反命题：

    Direct statement: If p,then q.

    Converse:If q,then p.

    Inverse:If not p,then not q.

    Contrapositive:If not q,then not p.

4.  Logically equivalent pair of statements 逻辑等价命题：

    一个命题及其逆否命题等价。一个命题的逆命题和否命题等价。（即下图中对角线的两个命题等价）

    ![](media/image4.png){width="4.600694444444445in"
    height="1.695138888888889in"}

5.  Not logically equivalent pair of statements(adjacent)
    逻辑不等价命题（相邻位置）：

    一个命题和它的逆命题不等价。一个命题和它的否命题不等价。

<!-- -->

2.  **Problem solving skills 解题技巧**

<!-- -->

1.  Find the correct order by switching
    positions通过转换位置找到正确的顺序

2.  Find the contrapositive of the statement找出命题的逆否命题

3.  Find two statements that are contradicted to each
    other找到两个相互矛盾的命题(矛盾分析)

4.  Find two statements that are in agreement with each
    other找到两个相互一致的命题

5.  Focus on the step before the last关注最后一步之前的步骤

6.  Squeezing method挤压法

## 例题

**例题1**：写出命题"如果今天下雨，那么我会带伞"的逆命题、否命题和逆否命题。

**解**：
- 原命题：如果今天下雨，那么我会带伞。
- 逆命题：如果我会带伞，那么今天下雨。
- 否命题：如果今天不下雨，那么我不会带伞。
- 逆否命题：如果我不会带伞，那么今天不下雨。

**例题2**：判断"如果一个数是偶数，那么它能被2整除"和"如果一个数不能被2整除，那么它不是偶数"是否等价。

**解**：第二个命题是第一个命题的逆否命题，根据逻辑等价性，它们等价。

**例题3**：A、B、C、D四人中，只有一人说了真话。A说："B在说谎。"B说："C在说谎。"C说："A和B都在说谎。"D说："B在说谎。"请问谁说了真话？

**解**：假设A说真话，则B说谎，那么C说真话，但C说A和B都在说谎，矛盾。
假设B说真话，则C说谎，那么A和B不都在说谎，但A说B说谎，矛盾。
假设C说真话，则A和B都在说谎，那么A说"B在说谎"是假的，即B说真话，矛盾。
假设D说真话，则B说谎，那么C说真话，但C说A和B都在说谎，即A也说谎，这与D说真话不矛盾。所以D说了真话。

**例题4**：三个盒子分别标有"苹果"、"橙子"、"苹果和橙子"，但标签都贴错了。只允许打开一个盒子，如何确定每个盒子里装的是什么？

**解**：打开标有"苹果和橙子"的盒子。
- 如果里面是苹果，则标"苹果"的盒子是橙子，标"橙子"的盒子是"苹果和橙子"。
- 如果里面是橙子，则标"橙子"的盒子是苹果，标"苹果"的盒子是"苹果和橙子"。
- 如果里面是"苹果和橙子"，则标"苹果"的盒子是橙子，标"橙子"的盒子是苹果。

**例题5**：A、B、C三人中，一人是骑士（总是说真话），一人是骗子（总是说谎），一人是普通人（有时说真话有时说谎）。A说："B是普通人。"B说："C不是普通人。"C说："A不是普通人。"请判断三人的身份。

**解**：假设A是骑士，则B是普通人，那么C不是普通人，即C是骗子，所以A不是普通人，矛盾。
假设A是骗子，则B不是普通人，那么C是普通人，所以A不是普通人，即A是骗子，成立。所以A是骗子，B是骑士，C是普通人。
