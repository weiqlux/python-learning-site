// Python 学习网 - 主脚本

/**
 * 简单的 Python 代码执行器（模拟）
 * 注意：这是前端模拟，实际生产环境需要后端沙箱执行
 */
function runCode() {
    const code = document.getElementById('code-input').value;
    const outputDiv = document.getElementById('output');
    
    if (!code.trim()) {
        outputDiv.innerHTML = '<span style="color: #e06c75;">请输入代码后再运行</span>';
        return;
    }
    
    outputDiv.innerHTML = '<span style="color: #61afef;">正在执行...</span>';
    
    // 模拟代码执行（实际应该发送到后端）
    setTimeout(() => {
        try {
            const result = simulatePythonExecution(code);
            outputDiv.innerHTML = result;
        } catch (error) {
            outputDiv.innerHTML = `<span style="color: #e06c75;">错误：${error.message}</span>`;
        }
    }, 500);
}

/**
 * 模拟 Python 代码执行
 * 这是一个简化的模拟器，仅支持基础语法
 */
function simulatePythonExecution(code) {
    const lines = code.split('\n');
    let output = [];
    let variables = {};
    
    for (let line of lines) {
        line = line.trim();
        
        // 跳过空行和注释
        if (!line || line.startsWith('#')) {
            continue;
        }
        
        // 处理 print 语句
        const printMatch = line.match(/^print\((.*)\)$/);
        if (printMatch) {
            let value = printMatch[1].trim();
            
            // 处理 f-string
            if (value.startsWith('f"') || value.startsWith("f'")) {
                value = evaluateFString(value, variables);
            } 
            // 处理字符串
            else if ((value.startsWith('"') && value.endsWith('"')) || 
                     (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            // 处理变量
            else if (variables.hasOwnProperty(value)) {
                value = variables[value];
            }
            // 处理数字
            else if (/^-?\d+$/.test(value)) {
                value = parseInt(value);
            }
            
            output.push(String(value));
            continue;
        }
        
        // 处理变量赋值
        const assignMatch = line.match(/^(\w+)\s*=\s*(.+)$/);
        if (assignMatch) {
            const varName = assignMatch[1];
            let varValue = assignMatch[2].trim();
            
            // 字符串
            if ((varValue.startsWith('"') && varValue.endsWith('"')) || 
                (varValue.startsWith("'") && varValue.endsWith("'"))) {
                varValue = varValue.slice(1, -1);
            }
            // 整数
            else if (/^-?\d+$/.test(varValue)) {
                varValue = parseInt(varValue);
            }
            // 浮点数
            else if (/^-?\d+\.\d+$/.test(varValue)) {
                varValue = parseFloat(varValue);
            }
            // 布尔值
            else if (varValue === 'True') {
                varValue = true;
            } else if (varValue === 'False') {
                varValue = false;
            }
            
            variables[varName] = varValue;
            continue;
        }
        
        // 处理 for 循环 (简化版)
        const forMatch = line.match(/^for\s+(\w+)\s+in\s+range\((\d+)\):$/);
        if (forMatch) {
            const varName = forMatch[1];
            const count = parseInt(forMatch[2]);
            // 这里只做简单提示，实际应该执行循环体
            output.push(`[循环 ${count} 次，变量：${varName}]`);
            continue;
        }
        
        // 未知语句
        output.push(`[模拟执行] ${line}`);
    }
    
    if (output.length === 0) {
        return '<span style="color: #98c379;">代码执行完成（无输出）</span>';
    }
    
    return '<span style="color: #98c379;">' + output.join('\n') + '</span>';
}

/**
 * 评估 f-string
 */
function evaluateFString(fstring, variables) {
    // 简单的 f-string 解析
    return fstring.replace(/{(\w+)}/g, (match, varName) => {
        if (variables.hasOwnProperty(varName)) {
            return variables[varName];
        }
        return match;
    }).slice(2, -1); // 移除 f" 和 "
}

// 支持 Ctrl+Enter 运行代码
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('code-input');
    if (textarea) {
        textarea.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                runCode();
            }
        });
    }
});
